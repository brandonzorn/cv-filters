FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --find-links https://download.pytorch.org/whl/cpu -r requirements.txt

CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]