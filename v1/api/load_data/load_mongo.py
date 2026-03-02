import os
import json
import logging
import time
from pymongo import MongoClient, GEOSPHERE
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "tcc")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "pixels")
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "../../gridmaker/output/city_grid.geojson")


def load_geojson_data():
    logger.info(f"Connecting to MongoDB at {MONGO_URI}")
    client = MongoClient(MONGO_URI)
    
    try:
        client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    
    existing_count = collection.count_documents({})
    
    if existing_count > 0:
        logger.info(f"Collection '{MONGO_COLLECTION}' already contains {existing_count} documents. Skipping data load.")
        return
    
    logger.info(f"Collection '{MONGO_COLLECTION}' is empty. Loading data from {GEOJSON_PATH}")
    
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
        return
    
    logger.info(f"Found {len(features)} features to insert")
    
    logger.info("Creating 2dsphere geospatial index on 'geometry' field")
    index_start_time = time.time()
    collection.create_index([("geometry", GEOSPHERE)])
    geospatial_index_time = time.time() - index_start_time
    logger.info(f"Geospatial index created successfully in {geospatial_index_time:.2f}s")
    
    batch_size = 10
    total_inserted = 0
    
    # Performance metrics
    start_time = time.time()
    batch_times = []
    
    for i in range(0, len(features), batch_size):
        batch_start_time = time.time()
        batch = features[i:i + batch_size]
        result = collection.insert_many(batch)
        batch_elapsed = time.time() - batch_start_time
        batch_times.append(batch_elapsed)
        
        total_inserted += len(result.inserted_ids)
        logger.info(f"Inserted {total_inserted}/{len(features)} documents")
        logger.info(f"Batch time: {batch_elapsed:.2f}s")
    
    insert_time = time.time() - start_time
    
    final_count = collection.count_documents({})
    
    grid_index_start_time = time.time()
    collection.create_index([("properties.grid_id", 1)])
    grid_index_time = time.time() - grid_index_start_time
    logger.info(f"Created index on properties.grid_id in {grid_index_time:.2f}s")
    
    total_time = time.time() - start_time + geospatial_index_time
    
    logger.info(f"Data loading complete. Total documents in collection: {final_count}")
    logger.info("=" * 60)
    logger.info("PERFORMANCE METRICS")
    logger.info("=" * 60)
    logger.info(f"Total time: {total_time:.2f}s ({total_time/60:.2f} minutes)")
    logger.info(f"Insert time: {insert_time:.2f}s ({insert_time/60:.2f} minutes)")
    logger.info(f"Geospatial index time: {geospatial_index_time:.2f}s")
    logger.info(f"Grid index time: {grid_index_time:.2f}s")
    
    if batch_times:
        avg_batch_time = sum(batch_times) / len(batch_times)
        logger.info(f"Number of batches: {len(batch_times)}")
        logger.info(f"Average time per batch: {avg_batch_time:.2f}s")
        logger.info(f"Min batch time: {min(batch_times):.2f}s")
        logger.info(f"Max batch time: {max(batch_times):.2f}s")
        logger.info(f"Average documents per second: {total_inserted/insert_time:.2f}")
    
    logger.info("=" * 60)
    
    client.close()
