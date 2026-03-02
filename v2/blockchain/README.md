# NotificationStorage Smart Contract (v2)

A Solidity smart contract for storing and retrieving coordinate-based notifications with **on-chain spatial indexing**. This version eliminates the need for off-chain databases by implementing a spatial grid system directly in the blockchain.

## Architecture

The v2 system consists of two main components:

1. **`NotificationStorage.sol`** - Main contract handling notifications and pixel management
2. **`SpatialGrid.sol`** - Library implementing spatial indexing with grid-based bucketing

## Spatial Grid System

The `SpatialGrid` library implements a 2D grid-based spatial index:

### Configuration
- **Scale**: Coordinate precision multiplier (default: 1,000,000 for 6 decimal places)
- **Grid Size**: Bucket size in scaled units (default: 5,000 for ~0.005 degree)

### How It Works
1. Pixels are defined by bounding boxes (minLat, minLon, maxLat, maxLon)
2. Each pixel is inserted into multiple grid buckets based on its coverage
3. Coordinate queries lookup the appropriate grid bucket
4. Candidates are filtered to find exact intersections

## Contract Functions

### Notification Management

#### `addNotification(int256 _lat, int256 _lon, string memory _content)`
Adds a new notification at the given coordinates.
- **Parameters:**
  - `_lat`: Latitude in scaled units (e.g., -7.120100 → -7120100)
  - `_lon`: Longitude in scaled units (e.g., -34.880170 → -34880170)
  - `_content`: Notification content
- **Access:** Public
- **Behavior:** 
  - Performs spatial query to find all pixels containing the coordinates
  - Stores notification in all matching pixels
  - Records sender address and timestamp automatically
  - Reverts if no pixels found at coordinates

#### `getNotificationsSince(int256 _lat, int256 _lon, uint256 _since)`
Retrieves all notifications for coordinates since a specific timestamp.
- **Parameters:**
  - `_lat`: Latitude in scaled units
  - `_lon`: Longitude in scaled units
  - `_since`: Unix timestamp to filter from
- **Returns:** Array of `Notification` structs containing sender, content, and timestamp
- **Access:** Public view (free to call)
- **Behavior:**
  - Performs spatial query to find all pixels at coordinates
  - Aggregates notifications from all matching pixels
  - Uses binary search for efficient timestamp filtering
  - Reverts if result count exceeds `maxNotificationsToReturn`

### Pixel Management (Owner Only)

#### `addPixel(uint256 _pixelId, int256 _minLat, int256 _minLon, int256 _maxLat, int256 _maxLon)`
Adds a single pixel to the spatial index.
- **Parameters:**
  - `_pixelId`: Unique identifier for the pixel
  - `_minLat`, `_minLon`: Minimum bounds (scaled)
  - `_maxLat`, `_maxLon`: Maximum bounds (scaled)
- **Access:** Owner only
- **Behavior:** 
  - Validates bounds (min < max)
  - Inserts pixel into all appropriate grid buckets
  - Reverts if pixel ID already exists

#### `batchAddPixels(uint256[] memory _pixelIds, int256[] memory _minLats, ...)`
Batch insert multiple pixels efficiently.
- **Parameters:** Arrays of pixel data (all same length)
- **Access:** Owner only
- **Behavior:** Validates array lengths match, then inserts all pixels

#### `removePixel(uint256 _pixelId)`
Removes a pixel from the spatial index.
- **Parameters:**
  - `_pixelId`: Pixel ID to remove
- **Access:** Owner only
- **Behavior:**
  - Removes pixel from all grid buckets
  - Deletes pixel data and bucket mappings
  - Reverts if pixel doesn't exist
- **Note:** Does NOT delete associated notifications (notifications persist)

### Configuration

#### `setMaxNotificationsToReturn(uint256 value)`
Sets the maximum notifications that can be returned in a single query.
- **Parameters:**
  - `value`: Maximum count
- **Access:** Owner only
- **Default:** 200

## Deployment

### Constructor
```solidity
constructor()
```
- Sets deployer as owner
- Initializes spatial index with scale=1,000,000 and gridSize=5,000
- No parameters required

### Post-Deployment Steps
1. Load pixel data using `addPixel()` or `batchAddPixels()`
2. Optionally adjust `maxNotificationsToReturn` if needed

## Integration Guide

### Coordinate Scaling
Coordinates must be scaled by 1e6 before contract calls:
```python
lat_scaled = int(latitude * 1e6)   # -7.120100 → -7120100
lon_scaled = int(longitude * 1e6)  # -34.880170 → -34880170
```
