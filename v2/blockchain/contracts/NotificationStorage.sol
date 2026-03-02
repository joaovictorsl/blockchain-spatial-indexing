// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../libs/SpatialGrid.sol";

contract NotificationStorage {
    using SpatialGrid for SpatialGrid.Index;

    struct Notification {
        address sender;
        string content;
        uint256 timestamp;
    }
    mapping(uint64 => Notification[]) notifications;
    SpatialGrid.Index private spatialIndex;
    address owner;

    /// Too many notifications to return, try a more recent timestamp
    error TooManyNotificationsToReturn(uint256 count);
    uint256 maxNotificationsToReturn = 200;

    constructor(int256 _precision, int256 _bucketSize) {
        owner = msg.sender;
        spatialIndex.initialize(_precision, _bucketSize);
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

    function addNotification(int256 _lat, int256 _lon, string memory _content) public {
        uint256[] memory pixelIds = spatialIndex.query(_lat, _lon);
        require(pixelIds.length > 0, "No pixels found at given coordinates");
        
        for (uint256 i = 0; i < pixelIds.length; i++) {
            notifications[uint64(pixelIds[i])].push(Notification(msg.sender, _content, block.timestamp));
        }
    }

    function addPixel(
        uint256 _pixelId,
        int256 _minLat,
        int256 _minLon,
        int256 _maxLat,
        int256 _maxLon
    ) public ownerOnly {
        spatialIndex.insert(_pixelId, _minLat, _minLon, _maxLat, _maxLon);
    }

    function batchAddPixels(
        uint256[] memory _pixelIds,
        int256[] memory _minLats,
        int256[] memory _minLons,
        int256[] memory _maxLats,
        int256[] memory _maxLons
    ) public ownerOnly {
        require(_pixelIds.length == _minLats.length, "Array length mismatch");
        require(_pixelIds.length == _minLons.length, "Array length mismatch");
        require(_pixelIds.length == _maxLats.length, "Array length mismatch");
        require(_pixelIds.length == _maxLons.length, "Array length mismatch");
        
        for (uint256 i = 0; i < _pixelIds.length; i++) {
            spatialIndex.insert(_pixelIds[i], _minLats[i], _minLons[i], _maxLats[i], _maxLons[i]);
        }
    }

    function getNotificationsSince(int256 _lat, int256 _lon, uint256 _since) public view returns (Notification[] memory) {
        uint256[] memory pixelIds = spatialIndex.query(_lat, _lon);
        require(pixelIds.length > 0, "No pixels found at given coordinates");
        
        uint256 totalCount = 0;
        for (uint256 i = 0; i < pixelIds.length; i++) {
            Notification[] storage notificationsById = notifications[uint64(pixelIds[i])];
            uint256 startIndex = _binarySearch(notificationsById, _since);
            totalCount += notificationsById.length - startIndex;
        }
        
        require(totalCount <= maxNotificationsToReturn, TooManyNotificationsToReturn(totalCount));
        
        Notification[] memory result = new Notification[](totalCount);
        uint256 currentIndex = 0;
        
        for (uint256 i = 0; i < pixelIds.length; i++) {
            Notification[] storage notificationsById = notifications[uint64(pixelIds[i])];
            uint256 startIndex = _binarySearch(notificationsById, _since);
            uint256 count = notificationsById.length - startIndex;
            
            for (uint256 j = 0; j < count; j++) {
                result[currentIndex] = notificationsById[startIndex + j];
                currentIndex++;
            }
        }
        
        return result;
    }

    function getNotificationsByIdSince(uint64 _id, uint256 _since) public view returns (Notification[] memory) {
        Notification[] storage notificationsById = notifications[_id];
        uint256 startIndex = _binarySearch(notificationsById, _since);
        uint256 count = notificationsById.length - startIndex;

        require(count <= maxNotificationsToReturn, TooManyNotificationsToReturn(count));

        Notification[] memory result = new Notification[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = notificationsById[startIndex + i];
        }
        return result;
    }

    function _binarySearch(Notification[] storage _notifications, uint256 since) private view returns (uint256) {
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
