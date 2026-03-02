// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

library SpatialGrid {
    struct Pixel {
        uint256 id;
        int256 minLat;
        int256 minLon;
        int256 maxLat;
        int256 maxLon;
    }

    struct Index {
        // Configuration
        int256 scale;
        int256 gridSize;
        
        // Maps Pixel ID -> Pixel Data
        mapping(uint256 => Pixel) pixels;
        // Maps GridHash -> Array of Pixel IDs
        mapping(bytes32 => uint256[]) buckets;
    }

    function initialize(
        Index storage self,
        int256 _scale,
        int256 _gridSize
    ) internal {
        require(self.scale == 0, "Already initialized");
        require(_scale > 0 && _gridSize > 0, "Invalid configuration");
        self.scale = _scale;
        self.gridSize = _gridSize;
    }

    function insert(
        Index storage self,
        uint256 _id,
        int256 _minLat,
        int256 _minLon,
        int256 _maxLat,
        int256 _maxLon
    ) internal {
        require(self.pixels[_id].id == 0, "Pixel ID exists");
        require(_minLat < _maxLat && _minLon < _maxLon, "Invalid bounds");

        self.pixels[_id] = Pixel(_id, _minLat, _minLon, _maxLat, _maxLon);

        int256 startY = _floorDiv(_minLat, self.gridSize);
        int256 endY = _floorDiv(_maxLat, self.gridSize);
        int256 startX = _floorDiv(_minLon, self.gridSize);
        int256 endX = _floorDiv(_maxLon, self.gridSize);

        for (int256 y = startY; y <= endY; y++) {
            for (int256 x = startX; x <= endX; x++) {
                bytes32 key = _getGridKey(x, y);
                self.buckets[key].push(_id);
            }
        }
    }

    function query(Index storage self, int256 _lat, int256 _lon) 
        internal 
        view 
        returns (uint256[] memory) 
    {
        int256 gridY = _floorDiv(_lat, self.gridSize);
        int256 gridX = _floorDiv(_lon, self.gridSize);
        bytes32 key = _getGridKey(gridX, gridY);

        uint256[] storage candidates = self.buckets[key];
        
        uint256[] memory results = new uint256[](candidates.length);
        uint256 count = 0;

        for (uint256 i = 0; i < candidates.length; i++) {
            uint256 pid = candidates[i];
            Pixel storage p = self.pixels[pid];

            if (_intersects(p, _lat, _lon)) {
                results[count] = pid;
                count++;
            }
        }

        uint256[] memory trimmed = new uint256[](count);
        for (uint256 j = 0; j < count; j++) {
            trimmed[j] = results[j];
        }
        return trimmed;
    }

    function getPixel(Index storage self, uint256 _id) internal view returns (Pixel memory) {
        return self.pixels[_id];
    }

    function _getGridKey(int256 x, int256 y) private pure returns (bytes32) {
        return keccak256(abi.encodePacked(x, y));
    }

    function _intersects(Pixel storage _pixel, int256 _lat, int256 _lon) private view returns (bool) {
        return _lat >= _pixel.minLat && _lat <= _pixel.maxLat &&
               _lon >= _pixel.minLon && _lon <= _pixel.maxLon;
    }

    function _floorDiv(int256 a, int256 b) private pure returns (int256) {
        if ((a < 0) != (b < 0) && a % b != 0) return (a / b) - 1;
        return a / b;
    }
}