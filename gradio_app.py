import gradio as gr
from main import download_arxiv_pdf, extract_text_from_pdf, make_prompt, stream_llm_response
import os

def gradio_read_papers(urls_text, prompt):
    urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
    outputs = []
    for idx, url in enumerate(urls):
        try:
            pdf_path = download_arxiv_pdf(url)
            text = extract_text_from_pdf(pdf_path)
            os.unlink(pdf_path)
        except Exception as e:
            outputs.append(f"[{idx+1}] {url} 下载/解析出错: {str(e)}")
            continue
        prompt_str = make_prompt(text, prompt)
        result = ""
        for chunk in stream_llm_response(prompt_str):
            result += chunk
        outputs.append(f"【第{idx+1}篇】{url}\n{result}")
    return "\n\n".join(outputs)

with gr.Blocks() as demo:
    gr.Markdown("## ArXiv Paper Reader · 论文批量分析（GPT-4.1）")
    urls_box = gr.Textbox(lines=5, label="论文链接(每行一个，不要空行)")
    prompt_box = gr.Textbox(lines=3, label="自定义Prompt（可选，支持{text}占位）")
    output = gr.Textbox(lines=15, label="全部论文结果", interactive=True)
    btn = gr.Button("开始分析")
    btn.click(
        fn=gradio_read_papers,
        inputs=[urls_box, prompt_box],
        outputs=output,
        api_name="arxiv_read"
    )

if __name__ == "__main__":
    demo.queue().launch()