from motor.motor_asyncio import AsyncIOMotorClient
import os

from storage.models.pixel import Pixel

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:example@localhost:27017/")
MONGO_DB = os.getenv("MONGO_DB", "tcc")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "pixels")

    
class MongoStorage:
    def __init__(self, uri: str = MONGO_URI, MONGO_DB: str = MONGO_DB, MONGO_COLLECTION: str = MONGO_COLLECTION):
        self.db_client = AsyncIOMotorClient(uri)
        self.pixel_collection = self.db_client[MONGO_DB][MONGO_COLLECTION]
    
    async def get_pixel(self, longitude: float, latitude: float) -> Pixel | None:
        point = {
            "type": "Point",
            "coordinates": [longitude, latitude]
        }
        
        result = await self.pixel_collection.find_one(
            {
                "geometry": {
                    "$geoIntersects": {
                        "$geometry": point
                    }
                }
            },
            {
                "_id": 0,
                "properties.grid_id": 1,
                "properties.area": 1,
                "properties.centroid_lon": 1,
                "properties.centroid_lat": 1
            }
        )
        
        if result is None:
            return None
        
        return Pixel(
            result["properties"]["grid_id"],
            result["properties"]["area"],
            result["properties"]["centroid_lon"],
            result["properties"]["centroid_lat"],
        )

    async def ping(self) -> None:
        await self.db_client.admin.command('ping')

    async def close(self) -> None:
        if self.db_client:
            self.db_client.close()