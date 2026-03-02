# Notification per pixel API

FastAPI application that receives longitude and latitude coordinates and writes a notification on the blockchain to the pixel that contains those coordinates.

## Storage Implementations

- **PostgreSQL + PostGIS** - Uses PostGIS `ST_Intersects` function with spatial indexes
- **MongoDB** - Uses MongoDB's `$geoIntersects` operator with 2dsphere indexes

## Quick Start

1. **Start services:**
   ```bash
   docker compose -f docker-compose.mongo.yml up -d --build
   or
   docker compose -f docker-compose.psql.yml up -d --build
   ```

2. **Send a notification:**
   ```bash
   curl -X POST "http://localhost:8001/notifications" \
     -H "Content-Type: application/json" \
     -d '{"longitude": -34.880170, "latitude": -7.120100, "content": "Hello from this pixel!"}'
   ```

3. **Get notifications:**
   ```bash
   curl -X GET "http://localhost:8001/notifications?long=-34.880170&lat=-7.120100&since=0"
   ```

## API Endpoints

### `POST /notifications`
Send a notification to a pixel based on coordinates. The API will find the pixel containing the coordinates and write the notification to the blockchain.

**Request Body:**
```json
{
  "longitude": -34.880170,
  "latitude": -7.120100,
  "content": "Your notification message here"
}
```

**Parameters:**
- `longitude` (float, required): Longitude coordinate (-180 to 180)
- `latitude` (float, required): Latitude coordinate (-90 to 90)
- `content` (string, required): Notification content to write to blockchain

### `GET /notifications`
Retrieve notifications for a pixel based on coordinates. The API will find the pixel containing the coordinates and read notifications from the blockchain.

**Query Parameters:**
- `long` (float, required): Longitude coordinate (-180 to 180)
- `lat` (float, required): Latitude coordinate (-90 to 90)
- `since` (int, optional): Unix timestamp to retrieve notifications from. Defaults to 10 minutes ago if not provided (≥0)

## Environment Variables

### Blockchain Configuration

Required for both implementations:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB3_PROVIDER_URI` | `https://rpc-sepolia.rockx.com` | Ethereum node provider URL |
| `CONTRACT_ADDRESS` | - | Smart contract address (required) |
| `PRIVATE_KEY` | - | Private key for signing transactions (required) |
| `CONTRACT_ABI_PATH` | `/app/contract_abi.json` | Path to smart contract ABI (required) |

### PostgreSQL Implementation

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `example` | PostgreSQL password |
| `POSTGRES_HOST` | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `tcc` | Database name |
| `POSTGRES_TABLE` | `pixels` | Table name |
| `GEOJSON_PATH` | `/app/grid/city_grid.geojson` | Path to GeoJSON file |

### MongoDB Implementation

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_USER` | `root` | MongoDB username |
| `MONGO_PASSWORD` | `example` | MongoDB password |
| `MONGO_HOST` | `mongo` | MongoDB host |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_DB` | `tcc` | Database name |
| `MONGO_COLLECTION` | `pixels` | Collection name |
| `GEOJSON_PATH` | `/app/grid/city_grid.geojson` | Path to GeoJSON file |
| `MONGO_URI` | `mongodb://${MONGO_USER}:${MONGO_PASSWORD}@${MONGO_HOST}:${MONGO_PORT}/` | MongoDB connection string |

## Data Loading

The data loader (`load_data/main.py`) runs automatically on container startup:

### PostgreSQL Implementation

1. Connects to PostgreSQL
2. Enables PostGIS extension if not already enabled
3. Checks if the table exists and is empty
4. If empty or doesn't exist:
   - Creates the table with appropriate schema
   - Loads GeoJSON features from the specified file
   - Creates a spatial GIST index on the `geometry` column
   - Creates an index on `grid_id` for faster lookups
   - Inserts all features in batches of 1000
5. If not empty: Skips loading to avoid duplicates

### MongoDB Implementation

1. Connects to MongoDB
2. Checks if the collection is empty
3. If empty:
   - Loads GeoJSON features from the specified file
   - Creates a 2dsphere geospatial index on the `geometry` field
   - Creates an index on `properties.grid_id` for faster lookups
   - Inserts all features in batches of 1000
4. If not empty: Skips loading to avoid duplicates
