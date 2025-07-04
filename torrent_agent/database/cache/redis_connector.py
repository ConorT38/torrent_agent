import redis.asyncio as redis
from threading import Lock

from torrent_agent.common.configuration import Configuration  # Import the Configuration class

class RedisConnector:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(RedisConnector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            config = Configuration()
            redis_config = config.get_redis_config()

            print("Redis configuration:", redis_config)

            # Use configuration values
            self.host = redis_config["host"]
            self.port = redis_config["port"]
            self.password = redis_config.get("password", None)
            self.db = redis_config.get("db", 0)

            self._initialized = True

    async def connect(self):
        self.redis = await redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            db=self.db,
            decode_responses=True,
        )

    async def set(self, key, value, expire=None):
        await self.redis.set(key, value, ex=expire)

    async def get(self, key):
        return await self.redis.get(key)

    async def delete(self, key):
        await self.redis.delete(key)

    async def fetch_all_keys(self, pattern="*"):
        return await self.redis.keys(pattern)

    async def close(self):
        await self.redis.close()