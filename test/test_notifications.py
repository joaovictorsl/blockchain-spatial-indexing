#!/usr/bin/env python3
import json
import requests
import time
import statistics
from typing import List, Dict, Tuple
from pathlib import Path
from web3 import Web3
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
GEOJSON_PATH = os.getenv("GEOJSON_PATH", "./gridmaker/output/city_grid.geojson")
WEB3_PROVIDER_URI = os.getenv("WEB3_PROVIDER_URI", "https://sepolia.base.org")
NOTIFICATIONS_PER_PIXEL = 3
NUM_PIXELS_TO_TEST = 10


class NotificationTester:
    def __init__(self, api_url: str, geojson_path: str, web3_provider: str):
        self.api_url = api_url
        self.geojson_path = geojson_path
        self.w3 = Web3(Web3.HTTPProvider(web3_provider))
        
        self.post_latencies = []
        self.get_latencies = []
        self.gas_used = []
        self.pixel_coordinates = []
        self.posted_notifications = []
        
    def load_pixel_coordinates(self, num_pixels: int) -> List[Tuple[float, float]]:
        """Load pixel coordinates from GeoJSON file."""
        print(f"\n{'='*60}")
        print(f"Loading pixel coordinates from {self.geojson_path}")
        print(f"{'='*60}")
        
        geojson_file = Path(self.geojson_path)
        if not geojson_file.exists():
            raise FileNotFoundError(f"GeoJSON file not found at {self.geojson_path}")
        
        with open(geojson_file, 'r') as f:
            data = json.load(f)
        
        features = data.get("features", [])
        if not features:
            raise ValueError("No features found in GeoJSON file")
        
        coordinates = []
        for i, feature in enumerate(features[:num_pixels]):
            props = feature.get("properties", {})
            centroid_lon = props.get("centroid_lon")
            centroid_lat = props.get("centroid_lat")
            grid_id = props.get("grid_id")
            
            if centroid_lon is not None and centroid_lat is not None:
                coordinates.append((centroid_lon, centroid_lat, grid_id))
                print(f"  Pixel {grid_id}: ({centroid_lon:.6f}, {centroid_lat:.6f})")
        
        print(f"\nLoaded {len(coordinates)} pixel coordinates")
        return coordinates
    
    def post_notification(self, longitude: float, latitude: float, content: str) -> Dict:
        """Post a notification and return response with latency."""
        payload = {
            "longitude": longitude,
            "latitude": latitude,
            "content": content
        }
        
        start_time = time.time()
        response = requests.post(
            f"{self.api_url}/notifications",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        latency = time.time() - start_time
        
        response.raise_for_status()
        return {
            "response": response.json(),
            "latency": latency,
            "status_code": response.status_code
        }
    
    def get_notifications(self, longitude: float, latitude: float, since: int = 0) -> Dict:
        """Get notifications and return response with latency."""
        params = {
            "long": longitude,
            "lat": latitude,
            "since": since
        }
        
        start_time = time.time()
        response = requests.get(
            f"{self.api_url}/notifications",
            params=params
        )
        latency = time.time() - start_time
        
        response.raise_for_status()
        return {
            "response": response.json(),
            "latency": latency,
            "status_code": response.status_code
        }
    
    def get_gas_used(self, tx_hash: str) -> int:
        """Get gas used from transaction receipt."""
        try:
            if not self.w3.is_connected():
                print("Warning: Not connected to blockchain, cannot fetch gas data")
                return 0
            
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return receipt['gasUsed']
        except Exception as e:
            print(f"Warning: Could not fetch gas for tx {tx_hash}: {e}")
            return 0
    
    def populate_notifications(self):
        """Populate notifications across multiple pixels."""
        print(f"\n{'='*60}")
        print(f"POSTING NOTIFICATIONS")
        print(f"{'='*60}")
        print(f"Pixels to test: {NUM_PIXELS_TO_TEST}")
        print(f"Notifications per pixel: {NOTIFICATIONS_PER_PIXEL}")
        print(f"Total notifications to post: {NUM_PIXELS_TO_TEST * NOTIFICATIONS_PER_PIXEL}")
        
        total_notifications = 0
        
        for pixel_idx, (lon, lat, grid_id) in enumerate(self.pixel_coordinates):
            print(f"\n--- Pixel {grid_id} ({pixel_idx + 1}/{len(self.pixel_coordinates)}) ---")
            print(f"Coordinates: ({lon:.6f}, {lat:.6f})")
            
            for notif_idx in range(NOTIFICATIONS_PER_PIXEL):
                content = f"Notification {notif_idx + 1} for pixel {grid_id}"
                
                try:
                    result = self.post_notification(lon, lat, content)
                    total_notifications += 1
                    
                    tx_hash = result["response"].get("transaction_hash")
                    latency_ms = result["latency"] * 1000
                    
                    self.post_latencies.append(result["latency"])
                    self.posted_notifications.append({
                        "pixel_id": grid_id,
                        "longitude": lon,
                        "latitude": lat,
                        "content": content,
                        "tx_hash": tx_hash
                    })
                    
                    print(f"  ✓ Posted notification {notif_idx + 1}/{NOTIFICATIONS_PER_PIXEL}")
                    print(f"    Latency: {latency_ms:.2f}ms")
                    print(f"    TX Hash: {tx_hash[:20]}...")
                    
                    if tx_hash and self.w3.is_connected():
                        gas = self.get_gas_used(tx_hash)
                        if gas > 0:
                            self.gas_used.append(gas)
                            print(f"    Gas Used: {gas:,}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  ✗ Error posting notification: {e}")
        
        print(f"\n{'='*60}")
        print(f"Successfully posted {total_notifications} notifications")
        print(f"{'='*60}")
    
    def retrieve_notifications(self):
        """Retrieve notifications from all tested pixels."""
        print(f"\n{'='*60}")
        print(f"RETRIEVING NOTIFICATIONS")
        print(f"{'='*60}")
        
        pixels_tested = set()
        for notif in self.posted_notifications:
            pixel_key = (notif["longitude"], notif["latitude"], notif["pixel_id"])
            if pixel_key not in pixels_tested:
                pixels_tested.add(pixel_key)
        
        total_retrieved = 0
        
        for lon, lat, grid_id in pixels_tested:
            print(f"\n--- Pixel {grid_id} ---")
            print(f"Coordinates: ({lon:.6f}, {lat:.6f})")
            
            try:
                result = self.get_notifications(lon, lat, since=0)
                latency_ms = result["latency"] * 1000
                
                self.get_latencies.append(result["latency"])
                
                notifications = result["response"].get("notifications", [])
                total_retrieved += len(notifications)
                
                print(f"  ✓ Retrieved {len(notifications)} notification(s)")
                print(f"    Latency: {latency_ms:.2f}ms")
                
                for idx, notif in enumerate(notifications):
                    print(f"    Notification {idx + 1}:")
                    print(f"      Content: {notif.get('content', 'N/A')}")
                    print(f"      Sender: {notif.get('sender', 'N/A')[:20]}...")
                    print(f"      Timestamp: {notif.get('timestamp', 'N/A')}")
                
            except Exception as e:
                print(f"  ✗ Error retrieving notifications: {e}")
        
        print(f"\n{'='*60}")
        print(f"Retrieved {total_retrieved} total notifications")
        print(f"{'='*60}")
    
    def print_metrics(self):
        """Print comprehensive metrics."""
        print(f"\n{'='*60}")
        print(f"PERFORMANCE METRICS")
        print(f"{'='*60}")
        
        print(f"\n📊 POST Operations:")
        if self.post_latencies:
            avg_post = statistics.mean(self.post_latencies) * 1000
            min_post = min(self.post_latencies) * 1000
            max_post = max(self.post_latencies) * 1000
            median_post = statistics.median(self.post_latencies) * 1000
            
            print(f"  Total requests: {len(self.post_latencies)}")
            print(f"  Average latency: {avg_post:.2f}ms")
            print(f"  Median latency: {median_post:.2f}ms")
            print(f"  Min latency: {min_post:.2f}ms")
            print(f"  Max latency: {max_post:.2f}ms")
            
            if len(self.post_latencies) > 1:
                stdev = statistics.stdev(self.post_latencies) * 1000
                print(f"  Std deviation: {stdev:.2f}ms")
        else:
            print("  No data available")
        
        print(f"\n📊 GET Operations:")
        if self.get_latencies:
            avg_get = statistics.mean(self.get_latencies) * 1000
            min_get = min(self.get_latencies) * 1000
            max_get = max(self.get_latencies) * 1000
            median_get = statistics.median(self.get_latencies) * 1000
            
            print(f"  Total requests: {len(self.get_latencies)}")
            print(f"  Average latency: {avg_get:.2f}ms")
            print(f"  Median latency: {median_get:.2f}ms")
            print(f"  Min latency: {min_get:.2f}ms")
            print(f"  Max latency: {max_get:.2f}ms")
            
            if len(self.get_latencies) > 1:
                stdev = statistics.stdev(self.get_latencies) * 1000
                print(f"  Std deviation: {stdev:.2f}ms")
        else:
            print("  No data available")
        
        print(f"\n⛽ Gas Consumption:")
        if self.gas_used:
            avg_gas = statistics.mean(self.gas_used)
            min_gas = min(self.gas_used)
            max_gas = max(self.gas_used)
            total_gas = sum(self.gas_used)
            median_gas = statistics.median(self.gas_used)
            
            print(f"  Transactions tracked: {len(self.gas_used)}")
            print(f"  Total gas used: {total_gas:,}")
            print(f"  Average gas per tx: {avg_gas:,.0f}")
            print(f"  Median gas per tx: {median_gas:,.0f}")
            print(f"  Min gas per tx: {min_gas:,}")
            print(f"  Max gas per tx: {max_gas:,}")
            
            if len(self.gas_used) > 1:
                stdev = statistics.stdev(self.gas_used)
                print(f"  Std deviation: {stdev:,.0f}")
        else:
            print("  No gas data available (blockchain connection issue or no receipts)")
        
        print(f"\n{'='*60}")
    
    def run_tests(self):
        """Run the complete test suite."""
        print(f"\n{'#'*60}")
        print(f"# NOTIFICATION TESTING SUITE")
        print(f"{'#'*60}")
        print(f"API URL: {self.api_url}")
        print(f"Web3 Provider: {WEB3_PROVIDER_URI}")
        print(f"Blockchain connected: {self.w3.is_connected()}")
        
        try:
            self.pixel_coordinates = self.load_pixel_coordinates(NUM_PIXELS_TO_TEST)
            
            self.populate_notifications()
            
            print("\nWaiting 5 seconds before retrieval...")
            time.sleep(5)
            
            self.retrieve_notifications()
            
            self.print_metrics()
            
            print(f"\n{'#'*60}")
            print(f"# TEST COMPLETE")
            print(f"{'#'*60}\n")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tester = NotificationTester(
        api_url=API_BASE_URL,
        geojson_path=GEOJSON_PATH,
        web3_provider=WEB3_PROVIDER_URI
    )
    tester.run_tests()
