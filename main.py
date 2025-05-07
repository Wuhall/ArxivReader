import os
import tempfile
import requests
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()
app = FastAPI()

# ---- 配置读取 ----
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai').lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-2025-04-14")

ALIYUN_MODEL_KEY = os.getenv("ALIYUN_MODEL_KEY")
ALIYUN_MODEL_NAME = os.getenv("ALIYUN_MODEL_NAME", "deepseek-r1")

# OpenAI/阿里 客户端复用变量
_openai_client = None
_ali_client = None

DEFAULT_PROMPT_TEMPLATE = (
    """  
## 指令：严格按论文原始结构（Abstract/Introduction/Method等）逐段解析，每部分包含：  
1. 总结（1-2句中文，保留关键术语）  
2. 分析（逻辑漏洞/隐藏信息/领域关联）  
        3. 标注位置（例：`Page 5, Table 2`）  

## 输出格式：markdown，包含章节标题和位置标注。  

## 示例指令：  
"从Abstract开始解析，输出简体中文。""
    "这是论文内容：\n\n{text}"""
)

class UrlsModel(BaseModel):
    urls: List[str]
    prompt: Optional[str] = None

def download_arxiv_pdf(url):
    if 'arxiv.org/abs/' in url:
        paper_id = url.strip().split('/')[-1]
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
    elif 'arxiv.org/pdf/' in url:
        pdf_url = url
        if not pdf_url.endswith('.pdf'):
            pdf_url += '.pdf'
    else:
        raise ValueError("只支持arxiv链接")
    resp = requests.get(pdf_url)
    resp.raise_for_status()
    f = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    f.write(resp.content)
    f.close()
    return f.name

def extract_text_from_pdf(pdf_file):
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except ImportError:
        raise RuntimeError("请 pip install pdfplumber")

def make_prompt(text, user_prompt=None):
    if user_prompt and user_prompt.strip():
        if "{text}" in user_prompt:
            return user_prompt.replace("{text}", text[:3500])
        else:
            return user_prompt + "\n\n" + text[:3500]
    else:
        return DEFAULT_PROMPT_TEMPLATE.replace("{text}", text[:3500])

# ---------- LLM统一响应 ----------
def get_openai_client():
    global _openai_client
    if _openai_client is None:
        import openai
        _openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client

def get_ali_client():
    global _ali_client
    if _ali_client is None:
        import openai # 官方兼容openai客户端
        _ali_client = openai.OpenAI(
            api_key=ALIYUN_MODEL_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    return _ali_client

def stream_llm_response(prompt):
    """根据 LLM_PROVIDER 调用不同平台，yield 内容"""
    if LLM_PROVIDER == "openai":
        client = get_openai_client()
        model = OPENAI_MODEL
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            stream=True
        )
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    elif LLM_PROVIDER == "ali":
        client = get_ali_client()
        model = ALIYUN_MODEL_NAME
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            stream=True
        )
        for chunk in response:
            delta = chunk.choices[0].delta
            # 阿里模型有reasoning_content和content二者, 只输出最终回复/思考
            # 可根据实际需求自定义（默认只拼content）
            if hasattr(delta, 'content') and delta.content:
                yield delta.content

    else:
        raise RuntimeError("不支持的LLM_PROVIDER: 仅支持openai和ali")

def batch_stream(urls: list, prompt: Optional[str]):
    for idx, url in enumerate(urls):
        try:
            pdf_path = download_arxiv_pdf(url)
            text = extract_text_from_pdf(pdf_path)
            os.unlink(pdf_path)
        except Exception as e:
            yield f"\n=== [{idx+1}] {url} 报错: {str(e)} ===\n"
            continue

        prompt_str = make_prompt(text, prompt)
        yield f"\n=== [{idx+1}] {url} 分析结果 ===\n"
        for res in stream_llm_response(prompt_str):
            yield res
        yield "\n"

@app.post("/read_papers/")
async def read_papers(request: Request):
    data = await request.json()
    urls = data.get("urls", [])
    prompt = data.get("prompt")
    return StreamingResponse(batch_stream(urls, prompt), media_type="text/plain")