# Notification Testing Script

This script tests the notification API by posting and retrieving notifications across multiple grid pixels while tracking performance metrics.

## Features

- 📍 Loads pixel coordinates from `../gridmaker/output/city_grid.geojson`
- 📤 Posts multiple notifications per pixel via HTTP POST
- 📥 Retrieves notifications via HTTP GET
- ⏱️ Tracks latency for all operations
- ⛽ Monitors gas consumption for blockchain transactions
- 📊 Generates comprehensive performance metrics

## Installation

```bash
cd test/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To deactivate the virtual environment when done:

```bash
deactivate
```

## Usage

### Basic Usage

```bash
python3 test_notifications.py
```

### Configuration via Environment Variables

```bash
export API_BASE_URL="http://localhost:8000"

export GEOJSON_PATH="../gridmaker/output/city_grid.geojson"

export WEB3_PROVIDER_URI="https://sepolia.base.org"

python3 test_notifications.py
```

### Customizing Test Parameters

Edit the following constants in `test_notifications.py`:

- `NOTIFICATIONS_PER_PIXEL`: Number of notifications to post per pixel (default: 3)
- `NUM_PIXELS_TO_TEST`: Number of pixels to test (default: 10)

## Prerequisites

Before running the test, ensure:

1. **V2 API is running**:
   ```bash
   cd v2/api
   docker compose up -d --build
   ```

2. **Grid data is available**:
   - Ensure `city_grid.geojson` exists in `../gridmaker/output/`
   - Or specify a different path via `GEOJSON_PATH`

3. **Blockchain is initialized**:
   - Pixels should be loaded into the blockchain
   - Contract should be deployed and accessible

## Output

The script provides:

### Console Output
- Real-time progress for each POST and GET operation
- Transaction hashes for each posted notification
- Gas consumption per transaction
- Latency measurements

### Performance Metrics
- **POST Operations**: Average, median, min, max latency and standard deviation
- **GET Operations**: Average, median, min, max latency and standard deviation
- **Gas Consumption**: Total, average, median, min, max gas usage and standard deviation

## Example Output

```
############################################################
# NOTIFICATION TESTING SUITE
############################################################
API URL: http://localhost:8000
Web3 Provider: https://sepolia.base.org
Blockchain connected: True

============================================================
Loading pixel coordinates from ../gridmaker/output/city_grid.geojson
============================================================
  Pixel 0: (-34.964277, -7.215493)
  Pixel 1: (-34.964277, -7.197108)
  ...

============================================================
POSTING NOTIFICATIONS
============================================================
Pixels to test: 10
Notifications per pixel: 3
Total notifications to post: 30

--- Pixel 0 (1/10) ---
Coordinates: (-34.964277, -7.215493)
  ✓ Posted notification 1/3
    Latency: 1234.56ms
    TX Hash: 0x1234567890abcdef...
    Gas Used: 123,456

...

============================================================
PERFORMANCE METRICS
============================================================

📊 POST Operations:
  Total requests: 30
  Average latency: 1250.45ms
  Median latency: 1230.12ms
  Min latency: 1100.23ms
  Max latency: 1450.67ms
  Std deviation: 85.34ms

📊 GET Operations:
  Total requests: 10
  Average latency: 234.56ms
  Median latency: 230.45ms
  Min latency: 210.12ms
  Max latency: 280.34ms
  Std deviation: 18.45ms

⛽ Gas Consumption:
  Transactions tracked: 30
  Total gas used: 3,703,680
  Average gas per tx: 123,456
  Median gas per tx: 123,400
  Min gas per tx: 120,000
  Max gas per tx: 125,000
  Std deviation: 1,234
```
