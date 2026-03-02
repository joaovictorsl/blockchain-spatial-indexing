# NotificationStorage Smart Contract (v1)

A Solidity smart contract for storing and retrieving notifications mapped to unique IDs.

## Features

- **Add Notifications**: Store notifications with content mapped to specific IDs
- **Retrieve Notifications**: Fetch notifications by ID since a specific timestamp

## Functions

### `addNotification(uint64 _id, string memory _content)`
Adds a new notification to the specified ID.
- **Parameters:**
  - `_id`: Unique identifier for the notification group
  - `_content`: Content of the notification
- **Access:** Public

### `getNotificationsByIdSince(uint64 _id, uint256 _since)`
Retrieves all notifications for a given ID since a specific timestamp.
- **Parameters:**
  - `_id`: Unique identifier for the notification group
  - `_since`: Unix timestamp to filter notifications from
- **Returns:** Array of Notification structs
- **Access:** Public view
- **Note:** Reverts if result exceeds `maxNotificationsToReturn`

### `setMaxNotificationsToReturn(uint256 value)`
Sets the maximum number of notifications that can be returned in a single query.
- **Parameters:**
  - `value`: Maximum count
- **Access:** Owner only
