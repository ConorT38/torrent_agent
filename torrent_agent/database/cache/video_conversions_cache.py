from torrent_agent.common import logger
from torrent_agent.database.dao.video_conversion_dao import IVideoConversionsDAO
from torrent_agent.database.video_conversions_repository import VideoConversionsRepository
from torrent_agent.database.cache.redis_connector import RedisConnector
from torrent_agent.model.video_conversion import VideoConversion
import json

log = logger.get_logger()

class VideoConversionsRepositoryCache(IVideoConversionsDAO):
    _instance = None

    def __new__(cls, repository: 'VideoConversionsRepository'):
        if cls._instance is None:
            cls._instance = super(VideoConversionsRepositoryCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, repository: 'VideoConversionsRepository'):
        if not self._initialized:
            self.repository = repository
            self.redis_connector = RedisConnector()
            self._initialized = True

    async def add_conversion(self, conversion: 'VideoConversion') -> int:
        log.info(f"Adding video conversion record to Redis cache: {conversion.original_filename}")
        conversion_key = f"conversion:{conversion.id}"
        existing_conversion = await self.redis_connector.get(conversion_key)
        if existing_conversion:
            log.info(f"Video conversion record '{conversion.original_filename}' already exists in Redis cache. Skipping addition.")
            return json.loads(existing_conversion)["id"]
        else:
            await self.redis_connector.set(conversion_key, json.dumps(conversion.to_dict()))
            return await self.repository.add_conversion(conversion)

    async def get_conversion(self, conversion_id: int) -> 'VideoConversion':
        log.info(f"Retrieving video conversion record with ID: {conversion_id}")
        conversion_key = f"conversion:{conversion_id}"
        cached_conversion = await self.redis_connector.get(conversion_key)
        if cached_conversion:
            log.info(f"Video conversion record '{conversion_id}' found in Redis cache.")
            return VideoConversion.from_dict(json.loads(cached_conversion))
        else:
            log.info(f"Video conversion record '{conversion_id}' not found in Redis cache. Fetching from repository.")
            conversion = await self.repository.get_conversion(conversion_id)
            if conversion:
                await self.redis_connector.set(conversion_key, json.dumps(conversion.to_dict()))
                return conversion
        return None

    async def update_conversion_status(self, conversion_id: int, status: str, error_message: str = None):
        log.info(f"Updating video conversion record status in Redis cache for ID: {conversion_id}")
        conversion_key = f"conversion:{conversion_id}"
        cached_conversion = await self.redis_connector.get(conversion_key)
        if cached_conversion:
            conversion = VideoConversion.from_dict(json.loads(cached_conversion))
            conversion.conversion_status = status
            conversion.error_message = error_message
            await self.redis_connector.set(conversion_key, json.dumps(conversion.to_dict()))
            log.info(f"Updated video conversion record status in Redis cache for ID: {conversion_id}")
        else:
            log.info(f"Video conversion record '{conversion_id}' not found in Redis cache. Fetching from repository to update status.")
        await self.repository.update_conversion_status(conversion_id, status, error_message)