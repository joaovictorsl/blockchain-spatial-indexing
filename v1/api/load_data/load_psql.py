import os
import json
import logging
import time
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "example")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tcc")
POSTGRES_TABLE = os.getenv("POSTGRES_TABLE", "pixels")
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "../../gridmaker/output/city_grid.geojson")


def load_geojson_data():
    logger.info(f"Connecting to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")
    
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD
    )
    conn.autocommit = False
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT 1")
        logger.info("Successfully connected to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise
    
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
        conn.commit()
        logger.info("PostGIS extension enabled")
    except Exception as e:
        logger.error(f"Failed to enable PostGIS: {e}")
        conn.rollback()
        raise
    
    query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s"
    cursor.execute(query, (POSTGRES_TABLE,))
    table_exists = cursor.fetchone()[0] > 0
    
    if table_exists:
        query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(POSTGRES_TABLE))
        cursor.execute(query)
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            logger.info(f"Table '{POSTGRES_TABLE}' already contains {existing_count} rows. Skipping data load.")
            cursor.close()
            conn.close()
            return
    
    logger.info(f"Table '{POSTGRES_TABLE}' is empty or doesn't exist. Loading data from {GEOJSON_PATH}")
    
    if not table_exists:
        create_table_sql = sql.SQL("""
        CREATE TABLE {} (
            id SERIAL PRIMARY KEY,
            grid_id INTEGER,
            area DOUBLE PRECISION,
            centroid_lon DOUBLE PRECISION,
            centroid_lat DOUBLE PRECISION,
            geometry GEOMETRY(Polygon, 4326)
        )
        """).format(sql.Identifier(POSTGRES_TABLE))
        cursor.execute(create_table_sql)
        conn.commit()
        logger.info(f"Created table '{POSTGRES_TABLE}'")
    
    geojson_file = Path(GEOJSON_PATH)
    if not geojson_file.exists():
        logger.error(f"GeoJSON file not found at {GEOJSON_PATH}")
        raise FileNotFoundError(f"GeoJSON file not found at {GEOJSON_PATH}")
    
    logger.info(f"Reading GeoJSON file: {GEOJSON_PATH}")
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    if data.get("type") != "FeatureCollection":
        raise ValueError("Invalid GeoJSON format: expected FeatureCollection")
    
    features = data.get("features", [])
    if not features:
        logger.warning("No features found in GeoJSON file")
        cursor.close()
        conn.close()
        return
    
    logger.info(f"Found {len(features)} features to insert")
    
    insert_sql = sql.SQL("""
    INSERT INTO {} (grid_id, area, centroid_lon, centroid_lat, geometry)
    VALUES (%s, %s, %s, %s, ST_GeomFromGeoJSON(%s))
    """).format(sql.Identifier(POSTGRES_TABLE))
    
    batch_size = 10
    total_inserted = 0
    
    # Performance metrics
    start_time = time.time()
    batch_times = []
    
    for i in range(0, len(features), batch_size):
        batch_start_time = time.time()
        batch = features[i:i + batch_size]
        batch_data = []
        
        for feature in batch:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")
            
            grid_id = properties.get("grid_id")
            area = properties.get("area")
            centroid_lon = properties.get("centroid_lon")
            centroid_lat = properties.get("centroid_lat")
            geometry_json = json.dumps(geometry)
            
            batch_data.append((grid_id, area, centroid_lon, centroid_lat, geometry_json))
        
        execute_batch(cursor, insert_sql, batch_data)
        conn.commit()
        batch_elapsed = time.time() - batch_start_time
        batch_times.append(batch_elapsed)
        
        total_inserted += len(batch_data)
        logger.info(f"Inserted {total_inserted}/{len(features)} rows")
        logger.info(f"Batch time: {batch_elapsed:.2f}s")
    
    insert_time = time.time() - start_time
    
    logger.info("Creating spatial index on geometry column")
    index_start_time = time.time()
    index_name = f"idx_{POSTGRES_TABLE}_geometry"
    query = sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} USING GIST (geometry)").format(
        sql.Identifier(index_name),
        sql.Identifier(POSTGRES_TABLE)
    )
    cursor.execute(query)
    conn.commit()
    spatial_index_time = time.time() - index_start_time
    logger.info(f"Spatial index created successfully in {spatial_index_time:.2f}s")
    
    grid_index_start_time = time.time()
    index_name = f"idx_{POSTGRES_TABLE}_grid_id"
    query = sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} (grid_id)").format(
        sql.Identifier(index_name),
        sql.Identifier(POSTGRES_TABLE)
    )
    cursor.execute(query)
    conn.commit()
    grid_index_time = time.time() - grid_index_start_time
    logger.info(f"Created index on grid_id in {grid_index_time:.2f}s")
    
    query = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(POSTGRES_TABLE))
    cursor.execute(query)
    final_count = cursor.fetchone()[0]
    
    total_time = time.time() - start_time
    
    logger.info(f"Data loading complete. Total rows in table: {final_count}")
    logger.info("=" * 60)
    logger.info("PERFORMANCE METRICS")
    logger.info("=" * 60)
    logger.info(f"Total time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    logger.info(f"Insert time: {insert_time:.2f}s ({insert_time/60:.2f} minutes)")
    logger.info(f"Spatial index time: {spatial_index_time:.2f}s")
    logger.info(f"Grid index time: {grid_index_time:.2f}s")
    
    if batch_times:
        avg_batch_time = sum(batch_times) / len(batch_times)
        logger.info(f"Number of batches: {len(batch_times)}")
        logger.info(f"Average time per batch: {avg_batch_time:.2f}s")
        logger.info(f"Min batch time: {min(batch_times):.2f}s")
        logger.info(f"Max batch time: {max(batch_times):.2f}s")
        logger.info(f"Average rows per second: {total_inserted/insert_time:.2f}")
    
    logger.info("=" * 60)
    
    cursor.close()
    conn.close()
