FROM python:3.10.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY load_data ./load_data
COPY . .

CMD ["sh", "-c", "python load_data/main.py && uvicorn api:app --host 0.0.0.0 --port 8000"]
