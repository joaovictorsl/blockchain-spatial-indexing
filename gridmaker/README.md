# Grid Splitting

Given a city from Paraíba, Brazil, split it into a grid of square polygons.

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Process a city by name:
```bash
python main.py --city-name "João Pessoa" --output output/joao_pessoa_grid.geojson
```

Process a city by ID:
```bash
python main.py --city-id "city_123" --output output/city_grid.geojson
```

### Advanced Options

Customize grid cell size manually:
```bash
python main.py --city-name "João Pessoa" --cell-size 0.005 --output output/joao_pessoa_fine_grid.geojson
```

Use automatic cell sizing with target number of cells:
```bash
python main.py --city-name "João Pessoa" --target-cells 50 --output output/joao_pessoa_50cells.geojson
```

### Command Line Arguments

- `--input`: Input JSON file with city data (default: `data/city_properties.json`)
- `--output`: Output GeoJSON file path (default: `output/city_grid.geojson`)
- `--city-id`: City ID to process
- `--city-name`: City name to process (alternative to `--city-id`)
- `--cell-size`: Grid cell size in degrees (optional). If not specified, calculates optimal size based on `--target-cells`
- `--target-cells`: Target number of cells when using automatic cell sizing (default: `100`). Only used when `--cell-size` is not specified

**Note**: Either `--city-id` or `--city-name` must be specified.

## Output Format

The output GeoJSON contains a FeatureCollection with the following properties for each grid square:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": 0,
      "properties": {
        "grid_id": 0,
        "area": 0.0001,
        "centroid_lon": -46.6333,
        "centroid_lat": -23.5505
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[...]]
      }
    }
  ]
}
```

You can use this site to open and visualize the GeoJSON file: https://geojson.io/
