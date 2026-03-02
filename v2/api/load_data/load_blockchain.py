import os
import json
import logging
import time
from web3 import Web3
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "https://otter.bordel.wtf/erigon")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ABI_PATH = os.getenv("CONTRACT_ABI_PATH", "./contract_abi.json")
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "../../gridmaker/output/city_grid.geojson")


def get_pixel_bounds(coordinates):
    """
    Extract min/max lat/lon from polygon coordinates.
    Coordinates are in format [[[lon, lat], [lon, lat], ...]]
    """
    coords = coordinates[0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    
    return {
        'min_lat': min(lats),
        'max_lat': max(lats),
        'min_lon': min(lons),
        'max_lon': max(lons)
    }


def wait_for_pending_transactions(w3, account_address, max_wait=60):
    """
    Wait for any pending transactions to be mined before proceeding.
    """
    start_time = time.time()
    while True:
        pending_count = w3.eth.get_transaction_count(account_address, 'pending')
        confirmed_count = w3.eth.get_transaction_count(account_address, 'latest')
        
        if pending_count == confirmed_count:
            return True
        
        if time.time() - start_time > max_wait:
            logger.warning(f"Timeout waiting for pending transactions. Pending: {pending_count}, Confirmed: {confirmed_count}")
            return False
        
        logger.info(f"Waiting for pending transactions... (Pending: {pending_count}, Confirmed: {confirmed_count})")
        time.sleep(2)


def load_geojson_data():
    logger.info(f"Connecting to blockchain at {WEB3_PROVIDER_URI}")
    
    if not CONTRACT_ADDRESS:
        logger.error("CONTRACT_ADDRESS not set. Cannot load data.")
        raise ValueError("CONTRACT_ADDRESS environment variable is required")
    
    if not PRIVATE_KEY:
        logger.error("PRIVATE_KEY not set. Cannot load data.")
        raise ValueError("PRIVATE_KEY environment variable is required")
    
    w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URI))
    
    if not w3.is_connected():
        logger.error(f"Failed to connect to blockchain at {WEB3_PROVIDER_URI}")
        raise Exception(f"Failed to connect to blockchain at {WEB3_PROVIDER_URI}")
    
    logger.info("Successfully connected to blockchain")
    
    with open(CONTRACT_ABI_PATH, 'r') as f:
        contract_abi = json.load(f)
    
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(CONTRACT_ADDRESS),
        abi=contract_abi
    )
    
    account = w3.eth.account.from_key(PRIVATE_KEY)
    logger.info(f"Using account {account.address}")
    
    # Check if pixels already exist by trying to get pixel 0
    try:
        pixel_details = contract.functions.getPixelById(0).call()
        if pixel_details[5]:  # exists field
            logger.info("Pixels already loaded into blockchain. Skipping data load.")
            return
    except Exception:
        logger.info("No existing pixels found. Proceeding with data load.")
    
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
    
    logger.info(f"Found {len(features)} pixels to insert")
    
    # Prepare batch data
    batch_size = 10  # Smaller batch size to avoid gas limits
    total_inserted = 0
    
    # Performance metrics
    start_time = time.time()
    batch_times = []
    gas_used_list = []
    
    # Track nonce to ensure proper sequencing
    current_nonce = None
    
    for i in range(0, len(features), batch_size):
        batch_start_time = time.time()
        batch = features[i:i + batch_size]
        
        pixel_ids = []
        min_lats = []
        min_lons = []
        max_lats = []
        max_lons = []
        
        for feature in batch:
            properties = feature.get("properties", {})
            geometry = feature.get("geometry")
            
            grid_id = properties.get("grid_id")
            bounds = get_pixel_bounds(geometry.get("coordinates"))
            
            # Scale coordinates by 1e6 to match smart contract precision
            pixel_ids.append(grid_id)
            min_lats.append(int(bounds['min_lat'] * 1e6))
            min_lons.append(int(bounds['min_lon'] * 1e6))
            max_lats.append(int(bounds['max_lat'] * 1e6))
            max_lons.append(int(bounds['max_lon'] * 1e6))
        
        try:
            if current_nonce is None:
                wait_for_pending_transactions(w3, account.address)
                current_nonce = w3.eth.get_transaction_count(account.address, 'latest')
            
            logger.info(f"Preparing batch {i//batch_size + 1}: {len(pixel_ids)} pixels (nonce: {current_nonce})")
            
            base_gas_price = w3.eth.gas_price
            gas_price = int(base_gas_price * 1.1)
            
            transaction = contract.functions.batchAddPixels(
                pixel_ids,
                min_lats,
                min_lons,
                max_lats,
                max_lons
            ).build_transaction({
                'from': account.address,
                'nonce': current_nonce,
                'gas': 5000000,
                'gasPrice': gas_price
            })
            
            signed_txn = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            logger.info("Waiting for transaction receipt...")
            
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt['status'] == 1:
                batch_elapsed = time.time() - batch_start_time
                batch_times.append(batch_elapsed)
                gas_used_list.append(tx_receipt['gasUsed'])
                
                total_inserted += len(pixel_ids)
                current_nonce += 1
                logger.info(f"Batch inserted successfully. Total: {total_inserted}/{len(features)}")
                logger.info(f"Gas used: {tx_receipt['gasUsed']}")
                logger.info(f"Batch time: {batch_elapsed * 1000:.2f}ms")
            else:
                raise Exception(f"Transaction failed with status {tx_receipt['status']}")
        
        except Exception as e:
            logger.error(f"Error inserting batch: {e}")
            raise
    
    total_time = time.time() - start_time
    
    logger.info(f"Data loading complete. Total pixels inserted: {total_inserted}")
    logger.info("=" * 60)
    logger.info("PERFORMANCE METRICS")
    logger.info("=" * 60)
    logger.info(f"Total time: {total_time * 1000:.2f}ms ({total_time/60:.2f} minutes)")
    
    if batch_times:
        avg_batch_time = sum(batch_times) / len(batch_times)
        logger.info(f"Number of batches: {len(batch_times)}")
        logger.info(f"Average time per batch: {avg_batch_time * 1000:.2f}ms")
        logger.info(f"Min batch time: {min(batch_times) * 1000:.2f}ms")
        logger.info(f"Max batch time: {max(batch_times) * 1000:.2f}ms")
    
    if gas_used_list:
        avg_gas = sum(gas_used_list) / len(gas_used_list)
        total_gas = sum(gas_used_list)
        logger.info(f"Total gas used: {total_gas:,}")
        logger.info(f"Average gas per batch: {avg_gas:,.0f}")
        logger.info(f"Min gas per batch: {min(gas_used_list):,}")
        logger.info(f"Max gas per batch: {max(gas_used_list):,}")
    
    logger.info("=" * 60)
