import json
import os
import argparse
from typing import List, Dict, Any
from city import City


def polygons_to_geojson(polygons: List[Any]) -> Dict[str, Any]:
    """
    Convert a list of Shapely Polygon objects to GeoJSON FeatureCollection.
    
    Args:
        polygons: List of Shapely Polygon objects
    
    Returns:
        GeoJSON FeatureCollection dictionary
    """
    features = []
    for i, polygon in enumerate(polygons):
        coords = list(polygon.exterior.coords)
        grid_id = i + 1
        feature = {
            "type": "Feature",
            "id": grid_id,
            "properties": {
                "grid_id": grid_id,
                "area": polygon.area,
                "centroid_lon": polygon.centroid.x,
                "centroid_lat": polygon.centroid.y
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read a city, split into grid squares, and output GeoJSON"
    )
    parser.add_argument(
        "--input",
        default="data/city_properties.json",
        help="Input JSON file with city data"
    )
    parser.add_argument(
        "--output",
        default="output/city_grid.geojson",
        help="Output GeoJSON file path"
    )
    parser.add_argument(
        "--city-id",
        help="City ID to process"
    )
    parser.add_argument(
        "--city-name",
        help="City name to process (alternative to --city-id)"
    )
    parser.add_argument(
        "--cell-size",
        type=float,
        default=None,
        help="Grid cell size in degrees (e.g., 0.01 ≈ 1km). If not specified, calculates optimal size based on --target-cells."
    )
    parser.add_argument(
        "--target-cells",
        type=int,
        default=100,
        help="Target number of cells when using automatic cell size (default: 100)"
    )
    
    args = parser.parse_args()
    
    if not args.city_id and not args.city_name:
        parser.error("Either --city-id or --city-name must be specified")
    
    print(f"Loading cities from {args.input}...")
    with open(args.input, "r", encoding="utf-8") as f:
        geojson = json.load(f)
    
    cities = [City.from_dict(city) for city in geojson]
    print(f"Loaded {len(cities)} cities")
    
    city = None
    if args.city_id:
        city = next((c for c in cities if c.id == args.city_id), None)
        if not city:
            print(f"Error: City with ID '{args.city_id}' not found")
            return
    else:
        city = next((c for c in cities if c.name.lower() == args.city_name.lower()), None)
        if not city:
            print(f"Error: City with name '{args.city_name}' not found")
            return
    
    print(f"Processing city: {city.name} (ID: {city.id})")
    
    if args.cell_size is not None:
        cell_size = args.cell_size
        print(f"Using specified cell size: {cell_size}°")
    else:
        min_lon = min(p.longitude for p in city.geometry.coordinates)
        max_lon = max(p.longitude for p in city.geometry.coordinates)
        min_lat = min(p.latitude for p in city.geometry.coordinates)
        max_lat = max(p.latitude for p in city.geometry.coordinates)
        
        bbox_width = max_lon - min_lon
        bbox_height = max_lat - min_lat
        bbox_area = bbox_width * bbox_height
        
        cell_size = (bbox_area / args.target_cells) ** 0.5
        print(f"Calculated optimal cell size: {cell_size:.6f}° (target: {args.target_cells} cells)")
    
    print("Splitting city into grid squares...")
    grid_squares = city.split_into_grid(cell_size=cell_size)
    print(f"Created {len(grid_squares)} grid squares")
    
    print(f"Converting to GeoJSON...")
    geojson_output = polygons_to_geojson(grid_squares)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(geojson_output, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully wrote {len(grid_squares)} grid squares to {args.output}")
    
    total_area = sum(p.area for p in grid_squares)
    print(f"\nStatistics:")
    print(f"  City: {city.name} (ID: {city.id})")
    print(f"  Total grid area: {total_area:.6f} square degrees")
    print(f"  Average square area: {total_area/len(grid_squares):.8f} square degrees")
    print(f"  Cell size: {cell_size}°")


if __name__ == "__main__":
    main()
