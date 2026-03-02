# Notification per pixel API (v2)

FastAPI application that receives longitude and latitude coordinates and writes a notification directly to the blockchain. This version uses **on-chain spatial indexing** built into the smart contract, eliminating the need for off-chain databases.

## Architecture

- **Pure Blockchain** - All spatial indexing and data storage happens on-chain
- **No Database Dependencies** - Direct communication with the blockchain contract
- **Coordinate-Based Operations** - Smart contract handles lat/lon to pixel resolution

## Quick Start

1. **Configure environment variables:**
   ```bash
   cp .env.docker .env
   # Edit .env with your blockchain configuration
   ```

2. **Start the API:**
   ```bash
   docker-compose up -d --build
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f api
   ```

4. **Send a notification:**
   ```bash
   curl -X POST "http://localhost:8000/notifications" \
     -H "Content-Type: application/json" \
     -d '{"longitude": -34.880170, "latitude": -7.120100, "content": "Hello from this pixel!"}'
   ```

5. **Get notifications:**
   ```bash
   curl -X GET "http://localhost:8000/notifications?long=-34.880170&lat=-7.120100&since=0"
   ```

6. **Stop the API:**
   ```bash
   docker compose down
   ```

## API Endpoints

### `POST /notifications`
Send a notification based on coordinates. The smart contract uses its built-in spatial indexing to resolve the coordinates to pixels and store the notification on-chain.

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
- `content` (string, required): Notification content

**Success Response (200):**
```json
{
  "transaction_hash": "0x1234567890abcdef...",
  "content": "Your notification message here",
  "latitude": -7.120100,
  "longitude": -34.880170
}
```

### `GET /notifications`
Retrieve notifications for coordinates. The smart contract uses its built-in spatial indexing to find all pixels intersecting with the coordinates and returns their notifications.

**Query Parameters:**
- `long` (float, required): Longitude coordinate (-180 to 180)
- `lat` (float, required): Latitude coordinate (-90 to 90)
- `since` (int, optional): Unix timestamp to retrieve notifications from. Defaults to 10 minutes ago if not provided (≥0)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/notifications?long=-34.880170&lat=-7.120100&since=0"
```

**Success Response (200):**
```json
{
  "latitude": -7.120100,
  "longitude": -34.880170,
  "notifications": [
    {
      "sender": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
      "content": "Hello from this pixel!",
      "timestamp": 1700000123
    }
  ]
}
```

## Environment Variables

### Blockchain Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB3_PROVIDER_URI` | `https://otter.bordel.wtf/erigon` | Ethereum node provider URL |
| `CONTRACT_ADDRESS` | - | Smart contract address |
| `PRIVATE_KEY` | - | Private key for signing transactions |
| `CONTRACT_ABI_PATH` | `./contract_abi.json` | Path to smart contract ABI file |

## Smart Contract Integration

The v2 API communicates directly with a smart contract that has built-in spatial indexing capabilities. Pixel data is stored on-chain and managed through the contract's owner functions.

### Coordinate Scaling

Coordinates are scaled by 1e6 before being sent to the contract to maintain precision with integer types:
- Latitude range: -90 to 90 → -90000000 to 90000000
- Longitude range: -180 to 180 → -180000000 to 180000000

### Contract Methods Used

1. **`addNotification(int256 _lat, int256 _lon, string _content)`**
   - Adds a notification at the given coordinates
   - Contract performs spatial query to find matching pixels
   - Stores notification with sender address and timestamp
   - Requires gas for transaction

2. **`getNotificationsSince(int256 _lat, int256 _lon, uint256 _since)`**
   - Retrieves notifications for coordinates since a timestamp
   - Contract performs spatial query to find matching pixels
   - Returns array of notifications with sender, content, and timestamp
   - Free to call (view function)

### Data Management

Pixel boundaries are loaded into the smart contract using the owner-only functions:
- `addPixel(uint256 _pixelId, int256 _minLat, int256 _minLon, int256 _maxLat, int256 _maxLon)`
- `removePixel(uint256 _pixelId)`
