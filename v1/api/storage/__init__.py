from typing import Protocol
import os

from storage.models.pixel import Pixel

class Storage(Protocol):
    async def get_pixel(self, longitude: float, latitude: float) -> Pixel | None:
        ...

    async def ping(self) -> None:
        ...

    async def close(self) -> None:
        ...


def get_storage() -> Storage:
    storage: Storage = None
    storage_type = os.getenv("STORAGE_TYPE", "mongo").lower()
    
    if storage_type == "psql":
        from storage.psql import PSQLStorage
        storage = PSQLStorage()
    else:
        from storage.mongo import MongoStorage
        storage = MongoStorage()

    return storage