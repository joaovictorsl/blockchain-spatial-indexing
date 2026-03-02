from dataclasses import dataclass

@dataclass
class Pixel:
    id: int
    area: float
    centroid_lon: float
    centroid_lat: float