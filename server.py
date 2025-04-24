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

def get_default_prompt(text):
    # 可以根据token限制自行截断
    return DEFAULT_PROMPT_TEMPLATE.replace("{text}", text[:3500])

def stream_gpt_response(prompt):
    # 流式yield gpt4.1响应
    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        stream=True
    )
    for chunk in response:
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

@app.post("/read_papers/")
async def read_papers(request: Request):
    data = await request.json()
    urls = data.get("urls", [])
    prompt = data.get("prompt")
    all_contents = []
    for url in urls:
        pdf_path = download_arxiv_pdf(url)
        text = extract_text_from_pdf(pdf_path)
        all_contents.append(text)
        os.unlink(pdf_path)
    full_text = "\n\n".join(all_contents)
    prompt_str = prompt or get_default_prompt(full_text)
    return StreamingResponse(stream_gpt_response(prompt_str), media_type="text/plain")

# 示例run: uvicorn main:app --reload