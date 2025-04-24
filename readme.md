# ArxivReader

ArxivReader is a lightweight API service that helps you quickly read and understand arXiv papers using GPT-4.1.
Simply provide one or more arXiv URLs, and the backend will automatically download, extract, and summarize the content for you.

## Features

- Accepts one or multiple arXiv URLs from users
- Automatically downloads and extracts text from PDFs
- Generates a default reading prompt if the user does not provide one
- Uses GPT-4.1 (API key loaded from `.env`) for summarization
- Easy RESTful API interface

## Requirements

- Python 3.8+
- [openai](https://pypi.org/project/openai/)
- [fastapi](https://fastapi.tiangolo.com/)
- [uvicorn](https://www.uvicorn.org/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [requests](https://pypi.org/project/requests/)
- [pdfplumber](https://pypi.org/project/pdfplumber/)
- [gradio]()

Install all dependencies:

```bash
pip install -r requirements.txt
```

## launch
```
python gradio.py
```