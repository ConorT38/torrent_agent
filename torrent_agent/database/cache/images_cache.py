from torrent_agent.common import logger
from torrent_agent.database.dao.image_dao import IImagesDAO
from torrent_agent.database.images_repository import ImagesRepository
from torrent_agent.model.image import Image
from torrent_agent.database.cache.redis_connector import RedisConnector
import json

log = logger.get_logger()

class ImagesRepositoryCache(IImagesDAO):
    _instance = None

    def __new__(cls, repository: 'ImagesRepository'):
        if cls._instance is None:
            cls._instance = super(ImagesRepositoryCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, repository: 'ImagesRepository'):
        if not self._initialized:
            self.repository = repository
            self.redis_connector = RedisConnector()
            self._initialized = True

    async def add_image(self, image: 'Image') -> int:
        log.info(f"Adding image to cache: {image.cdn_path}")
        await self.redis_connector.connect()
        cached_image = await self.redis_connector.get(image.cdn_path)
        if cached_image:
            log.info(f"Image '{image.cdn_path}' already exists in cache. Skipping addition.")
            return json.loads(cached_image)["id"]
        else:
            await self.redis_connector.set(image.cdn_path, json.dumps(image.to_dict()))
            return await self.repository.add_image(image)

    async def get_image(self, image_id: str) -> 'Image':
        log.info(f"Retrieving image with ID: {image_id}")
        await self.redis_connector.connect()
        cached_image = await self.redis_connector.get(image_id)
        if cached_image:
            log.info(f"Image '{image_id}' found in cache.")
            return Image.from_dict(json.loads(cached_image))
        else:
            log.info(f"Image '{image_id}' not found in cache. Fetching from repository.")
            image = await self.repository.get_image(image_id)
            if image:
                await self.redis_connector.set(image_id, json.dumps(image.to_dict()))
                return image
        return None
