from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_to_mongo():
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}...")
        db.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=30000,  # 30s to find a server (Atlas can be slow to wake)
            connectTimeoutMS=30000,          # 30s for initial TCP connection
            socketTimeoutMS=30000,           # 30s per query (prevents hanging)
            maxPoolSize=10,                  # Keep connections warm
            minPoolSize=1,                   # Always keep at least 1 connection alive
        )
        db.db = db.client[settings.MONGODB_DATABASE]
        
        # Verify connection
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        # Not raising so the API can still start and respond to /health checks.


async def close_mongo_connection():
    if db.client:
        logger.info("Closing MongoDB connection...")
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    return db.db

