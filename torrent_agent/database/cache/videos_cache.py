from torrent_agent.common import logger
from torrent_agent.database.cache.cache_entry import CacheEntry
from torrent_agent.database.dao.video_dao import IVideosDAO
from torrent_agent.database.videos_repository import VideosRepository
from torrent_agent.model.video import Video

log = logger.get_logger()

class VideosRepositoryCache(IVideosDAO):
    _instance = None

    def __new__(cls, repository: 'VideosRepository'):
        if cls._instance is None:
            cls._instance = super(VideosRepositoryCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, repository: 'VideosRepository'):
        if not self._initialized:
            self.cache: dict[str, 'CacheEntry'] = {}
            self.repository = repository
            self._initialized = True

    async def add_video(self, video: 'Video'):
        log.info(f"Adding video to cache: {video.title}")
        if video.title in self.cache:
            log.info(f"Video '{video.title}' already exists in cache. Skipping addition.")
            return
        if video.title not in self.cache:
            self.cache[video.title] = CacheEntry(data=video)
            await self.repository.add_video(video)
    
    async def get_video(self, video_id: str) -> 'Video':
        log.info(f"Retrieving video with ID: {video_id}")
        # Check if the video is in the cache
        if video_id in self.cache:
            cache_entry = self.cache[video_id]
            if not cache_entry.is_expired():
                return cache_entry.data
            else:
                log.info(f"Cache entry for video '{video_id}' is expired. Removing from cache.")
                del self.cache[video_id]
        
        # If not in cache or expired, retrieve from the repository
        log.info(f"Video '{video_id}' not found in cache. Fetching from repository.")
        video = await self.repository.get_video(video_id)
        if video:
            self.cache[video_id] = CacheEntry(data=video)
            return video
        return None
    
    async def update_video_thumbnail(self, video_id: str, thumbnail_path: str):
        log.info(f"Updating thumbnail for video with ID: {video_id}")
        if video_id in self.cache:
            cache_entry = self.cache[video_id]
            cache_entry.data.thumbnail_path = thumbnail_path
            log.info(f"Updated thumbnail in cache for video '{video_id}'.")
        else:
            log.info(f"Video '{video_id}' not found in cache. Fetching from repository to update thumbnail.")
        
        await self.repository.update_video_thumbnail(video_id, thumbnail_path)

    async def get_video_by_filename(self, filename: str) -> 'Video':
        log.info(f"Retrieving video with file path: {filename}")
        # Check if the video is in the cache
        for cache_entry in self.cache.values():
            if cache_entry.data.filename == filename:
                if not cache_entry.is_expired():
                    return cache_entry.data
                else:
                    log.info(f"Cache entry for file path '{filename}' is expired. Removing from cache.")
                    del self.cache[cache_entry.data.title]
        
        # If not in cache or expired, retrieve from the repository
        log.info(f"Video with file path '{filename}' not found in cache. Fetching from repository.")
        video = await self.repository.get_video_by_filename(filename)
        if video:
            self.cache[video.title] = CacheEntry(data=video)
            return video
        return None