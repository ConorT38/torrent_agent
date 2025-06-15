from torrent_agent.common import logger
from torrent_agent.database.cache.cache_entry import CacheEntry
from torrent_agent.database.dao.image_dao import IImagesDAO
from torrent_agent.database.images_repository import ImagesRepository
from torrent_agent.model.image import Image

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
            self.cache: dict[str, 'CacheEntry'] = {}
            self.repository = repository
            self._initialized = True

    async def add_image(self, image: 'Image') -> int:
        log.info(f"Adding image to cache: {image.title}")
        if image.title in self.cache:
            log.info(f"Image '{image.title}' already exists in cache. Skipping addition.")
            return self.cache[image.title].data.id
        if image.title not in self.cache:
            self.cache[image.title] = CacheEntry(data=image)
            return await self.repository.add_image(image)
    
    async def get_image(self, image_id: str) -> 'Image':
        log.info(f"Retrieving image with ID: {image_id}")
        # Check if the image is in the cache
        if image_id in self.cache:
            cache_entry = self.cache[image_id]
            if not cache_entry.is_expired():
                return cache_entry.data
            else:
                log.info(f"Cache entry for image '{image_id}' is expired. Removing from cache.")
                del self.cache[image_id]
        
        # If not in cache or expired, retrieve from the repository
        log.info(f"image '{image_id}' not found in cache. Fetching from repository.")
        image = await self.repository.get_image(image_id)
        if image:
            self.cache[image_id] = CacheEntry(data=image)
            return image
        return None
