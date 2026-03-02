from typing import Annotated
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from blockchain import BlockchainClient
from time import time

from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


blockchain_client: BlockchainClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global blockchain_client
    
    logger.info(f"Connecting to blockchain")
    try:
        blockchain_client = BlockchainClient()
        blockchain_client.connect()
        logger.info("Successfully connected to blockchain")
    except Exception as e:
        logger.error(f"Failed to connect to blockchain: {e}")
        raise 
    
    yield


app = FastAPI(
    title="Notification per pixel API",
    description="Notify a pixel based on its coordinates",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateNotificationRequest(BaseModel):
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)
    content: str = Field(..., min_length=1, max_length=256)


@app.post("/notifications")
async def notify(
    request: CreateNotificationRequest
):
    try:
        tx_hash = blockchain_client.add_notification(
            request.latitude,
            request.longitude,
            request.content
        )
        
        return {
            "transaction_hash": tx_hash,
            "content": request.content,
            "latitude": request.latitude,
            "longitude": request.longitude,
        }
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


class GetNotificationsQueryParams(BaseModel):
    long: float = Field(..., ge=-180, le=180),
    lat: float = Field(..., ge=-90, le=90),
    since: int | None = Field(None, ge=0)


@app.get("/notifications")
async def get_notifications(
    params: Annotated[GetNotificationsQueryParams, Query()]
):
    if params.since is None:
        params.since = int(time.time()) - 600
    try:
        notifications = blockchain_client.get_notifications(
            params.lat,
            params.long,
            params.since
        )
        
        return {
            "latitude": params.lat,
            "longitude": params.long,
            "notifications": notifications,
        }
    except Exception as e:
        logger.error(f"Error reading notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
