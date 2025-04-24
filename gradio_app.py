import os
import gradio as gr
from server import download_arxiv_pdf, extract_text_from_pdf, get_default_prompt, client

def gradio_read_papers(urls_text, prompt):
    urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
    all_contents = []
    for url in urls:
        pdf_path = download_arxiv_pdf(url)
        text = extract_text_from_pdf(pdf_path)
        all_contents.append(text)
        os.unlink(pdf_path)
    full_text = "\n\n".join(all_contents)
    prompt_str = prompt or get_default_prompt(full_text)
    # 流式拼接输出
    result = ""
    response = client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[{"role": "user", "content": prompt_str}],
        max_tokens=2048,
        stream=True
    )
    for chunk in response:
        if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
            result += chunk.choices[0].delta.content
            yield result

with gr.Blocks() as demo:
    gr.Markdown("## ArXiv 论文智能阅读（支持多条arXiv链接）")
    urls_box = gr.Textbox(lines=5, label="论文链接(每行一个)")
    prompt_box = gr.Textbox(lines=3, label="自定义提示词（可选）")
    output = gr.Textbox(lines=20, label="GPT-4.1 输出", interactive=True)
    btn = gr.Button("开始分析")
    btn.click(
        fn=gradio_read_papers,
        inputs=[urls_box, prompt_box],
        outputs=output,
        api_name="arxiv_read"
    )

if __name__ == "__main__":
    demo.queue().launch()