import os

from storage.models.pixel import Pixel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "example")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "tcc")
POSTGRES_TABLE = os.getenv("POSTGRES_TABLE", "pixels")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


class PSQLStorage:
    def __init__(self, uri: str = DATABASE_URL):
        self.engine = create_async_engine(DATABASE_URL, echo=False)
        self.async_session_maker = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
    
    async def get_pixel(self, longitude: float, latitude: float) -> Pixel | None:
        async with self.async_session_maker() as session:
            query = text(f"""
                SELECT 
                    grid_id,
                    area,
                    centroid_lon,
                    centroid_lat
                FROM {POSTGRES_TABLE}
                WHERE ST_Intersects(
                    geometry,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
                )
                LIMIT 1
            """)
            
            result = await session.execute(
                query,
                {"longitude": longitude, "latitude": latitude}
            )
            row = result.fetchone()
            
            if row is None:
                return None
            
            return Pixel(
                row[0],
                row[1],
                row[2],
                row[3]
            )

    async def ping(self) -> None:
        async with self.engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()