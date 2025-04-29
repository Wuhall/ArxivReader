# ArxivReader

> [中文](#简介) | English

## Introduction

ArxivReader is a lightweight API and frontend service for helping you quickly read and understand arXiv papers via GPT-4.1.
Simply provide one or more arXiv URLs; the backend will automatically download, extract and summarize the paper(s) for you.

## Features

- Accepts one or multiple arXiv URLs
- Automatically downloads and extracts text from PDFs
- Supports user custom prompt, and falls back to builtin default prompt
- Uses GPT-4.1 (API key loaded from `.env`) for summarization
- Easy-to-use RESTful API and visual Gradio interface

## Requirements

- Python 3.8+
- [openai](https://pypi.org/project/openai/)
- [fastapi](https://fastapi.tiangolo.com/)
- [uvicorn](https://www.uvicorn.org/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)
- [pdfplumber](https://pypi.org/project/pdfplumber/)
- [gradio](https://gradio.app/)

To install all dependencies:

```bash
pip install -r requirements.txt
```

## How to launch

First, configure your `.env` with your OPENAI_API_KEY.
```
cp .env.example .env
```

To start the Gradio visual interface:

```bash
python gradio.py
```

Or for RESTful backend:

```bash
uvicorn main:app --reload
```




> 简体中文 | [English](#english)

## 简介

ArxivReader 是一个轻量级的 API 和可视化服务，利用 GPT-4.1 大模型帮助你快速阅读和理解 arXiv 论文。  
你只需输入一条或多条 arXiv 论文链接，后端会自动下载 PDF、提取其内容并摘要核心要点。

## 功能

- 支持批量输入 arXiv 链接
- 自动下载并解析 PDF
- 支持自定义阅读 prompt，也可使用内置默认 prompt
- 支持 GPT-4.1（API Key 需填在 `.env` 文件中）
- 提供 RESTful API 与可视化交互（Gradio 界面）
- 支持阿里云百炼API，接入DeepSeek-R1（API Key 需填在 `.env` 文件中）

## 环境依赖

- Python 3.8+
- [openai](https://pypi.org/project/openai/)
- [fastapi](https://fastapi.tiangolo.com/)
- [uvicorn](https://www.uvicorn.org/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)
- [pdfplumber](https://pypi.org/project/pdfplumber/)
- [gradio](https://gradio.app/)

安装所有依赖：

```bash
pip install -r requirements.txt
```

## 启动方式

首先配置 `.env` 文件，填入你的 OPENAI_API_KEY。
```
cp .env.example .env
```

运行 Gradio 可视化界面：

```bash
gradio gradio_app.py
```

或如需 RESTful 后端：

```bash
uvicorn main:app --reload
```

---


