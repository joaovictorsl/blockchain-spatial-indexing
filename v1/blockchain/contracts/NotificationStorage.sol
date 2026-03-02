// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract NotificationStorage {
    struct Notification {
        address sender;
        string content;
        uint256 timestamp;
    }
    mapping(uint64 => Notification[]) notifications;
    address owner;

    /// Too many notifications to return, try a more recent timestamp
    error TooManyNotificationsToReturn(uint256 count);
    uint256 maxNotificationsToReturn = 200;

    constructor() {
        owner = msg.sender;
    }

    modifier ownerOnly() {
        require(
            msg.sender == owner,
            "Must be owner"
        );
        _;
    }

    function setMaxNotificationsToReturn(uint256 value) external ownerOnly {
        maxNotificationsToReturn = value;
    }

    function addNotification(uint64 _id, string memory _content) public {
        notifications[_id].push(Notification(msg.sender, _content, block.timestamp));
    }

    function getNotificationsByIdSince(uint64 _id, uint256 _since) public view returns (Notification[] memory) {
        Notification[] storage notificationsById = notifications[_id];
        uint256 startIndex = binarySearch(notificationsById, _since);
        uint256 count = notificationsById.length - startIndex;

        require(count <= maxNotificationsToReturn, TooManyNotificationsToReturn(count));

        Notification[] memory result = new Notification[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = notificationsById[startIndex + i];
        }
        return result;
    }

    function binarySearch(Notification[] storage _notifications, uint256 since) private view returns (uint256) {
        uint256 left = 0;
        uint256 right = _notifications.length;

        while (left < right) {
            uint256 mid = left + (right - left) / 2;
            if (_notifications[mid].timestamp < since) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        return left;
    }
}
