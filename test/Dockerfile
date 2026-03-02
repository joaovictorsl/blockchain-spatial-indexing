FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY test_notifications.py .

ENV API_BASE_URL=http://localhost:8000
ENV GEOJSON_PATH=/data/city_grid.geojson
ENV WEB3_PROVIDER_URI=https://sepolia.base.org

CMD ["python3", "test_notifications.py"]
