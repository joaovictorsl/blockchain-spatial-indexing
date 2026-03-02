from dataclasses import dataclass
from typing import List
from shapely.geometry import Polygon, box


@dataclass
class Point:
    longitude: float
    latitude: float


@dataclass
class Geometry:
    type: str
    coordinates: List[Point]


@dataclass
class City:
    id: str
    name: str
    description: str
    geometry: Geometry

    @classmethod
    def from_dict(cls, data: dict) -> 'City':
        """Create a City instance from a dictionary."""
        geometry_data = data['geometry']
        
        coordinates = [
            Point(longitude=coord[0], latitude=coord[1])
            for coord in geometry_data['coordinates'][0]
        ]
        
        geometry = Geometry(
            type=geometry_data['type'],
            coordinates=coordinates
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            geometry=geometry
        )
    
    def split_into_grid(self, cell_size: float = 0.01) -> List[Polygon]:
        """
        Split a city's area into a grid of square polygons.
        
        Args:
            cell_size: Size of each grid cell in degrees (default 0.01 ≈ 1km)
        
        Returns:
            List of Shapely Polygon objects representing grid squares that
            intersect with the city boundary
        """
        coords = [(p.longitude, p.latitude) for p in self.geometry.coordinates]
        city_polygon = Polygon(coords)
        
        min_lon = min(p.longitude for p in self.geometry.coordinates)
        max_lon = max(p.longitude for p in self.geometry.coordinates)
        min_lat = min(p.latitude for p in self.geometry.coordinates)
        max_lat = max(p.latitude for p in self.geometry.coordinates)
        
        grid_squares = []
        
        current_lon = min_lon
        while current_lon < max_lon:
            current_lat = min_lat
            while current_lat < max_lat:
                square = box(
                    current_lon,
                    current_lat,
                    current_lon + cell_size,
                    current_lat + cell_size
                )
                
                if square.intersects(city_polygon):
                    grid_squares.append(square)
                
                current_lat += cell_size
            current_lon += cell_size
        
        return grid_squares
