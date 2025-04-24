import os
import tempfile
import requests
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import openai
from typing import Optional, List

load_dotenv()
app = FastAPI()

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

DEFAULT_PROMPT_TEMPLATE = (
    "请帮我阅读以下论文，"
    "并以结构化要点输出：\n"
    "1. 核心问题\n2. 方法方案\n3. 创新点\n4. 结果评价\n5. 适用场景与局限\n"
    "这是论文内容：\n\n{text}"
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
        # 若填写了自定义prompt，则用自定义prompt，内容自己放置{text}或自动追加
        if "{text}" in user_prompt:
            return user_prompt.replace("{text}", text[:3500])
        else:
            return user_prompt + "\n\n" + text[:3500]
    else:
        return DEFAULT_PROMPT_TEMPLATE.replace("{text}", text[:3500])

def stream_gpt_response(prompt):
    # yield流式token
    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        stream=True
    )
    for chunk in response:
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

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
        for res in stream_gpt_response(prompt_str):
            yield res
        yield "\n"

@app.post("/read_papers/")
async def read_papers(request: Request):
    data = await request.json()
    urls = data.get("urls", [])
    prompt = data.get("prompt")
    # 多个 stream输出，逐条论文逐条推送
    return StreamingResponse(batch_stream(urls, prompt), media_type="text/plain")