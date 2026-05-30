FROM python:3.13

WORKDIR /app

COPY requirements.txt .

RUN pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]