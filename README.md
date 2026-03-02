# Quickstart (Local)

## Gridmaker

```bash
cd gridmaker/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gridmaker.py --city-name "João Pessoa" --cell-size 0.005
deactivate
```

## V1

```bash
cd v1/api
cp .env.docker .env
```

Edit .env file with the right variables (you should only need to edit the STORAGE_TYPE and Blockchain Configuration)

### Run with MongoDB

```bash
docker compose -f docker-compose.mongo.yml up -d --build
```

### Run with PostgreSQL

```bash
docker compose -f docker-compose.psql.yml up -d --build
```

### Test

```bash
curl -X POST "http://localhost:8001/notifications" \
  -H "Content-Type: application/json" \
  -d '{"longitude": -34.880170, "latitude": -7.120100, "content": "Hello from this pixel!"}'
```

```bash
curl -X GET "http://localhost:8001/notifications?long=-34.880170&lat=-7.120100&since=0"
```

### Take down

```bash
docker compose -f docker-compose.mongo.yml down
```

or

```bash
docker compose -f docker-compose.psql.yml down
```

## V2

```bash
cd v2/api
cp .env.docker .env
```

Edit .env file with the right variables (you should only need to edit the Blockchain Configuration)

### Run

```bash
docker compose up -d --build
```

### Test

```bash
curl -X POST "http://localhost:8000/notifications" \
 -H "Content-Type: application/json" \
 -d '{"longitude": -34.880170, "latitude": -7.120100, "content": "Hello from this pixel!"}'
```

```bash
curl -X GET "http://localhost:8000/notifications?long=-34.880170&lat=-7.120100&since=0"
```