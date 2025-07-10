from torrent_agent.common import logger
from torrent_agent.database.dao.video_dao import IVideosDAO
from torrent_agent.database.videos_repository import VideosRepository
from torrent_agent.model.video import Video
from torrent_agent.database.cache.redis_connector import RedisConnector  # Import RedisConnector
import json

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
            self.repository = repository
            self.redis_connector = RedisConnector()
            self._initialized = True

    async def add_video(self, video: 'Video'):
        log.info(f"Adding video to Redis cache: {video.title}")
        video_key = f"video:{video.title}"
        existing_video = await self.redis_connector.get(video_key)
        if existing_video:
            log.info(f"Video '{video.title}' already exists in Redis cache. Skipping addition.")
            return
        video_data = video.to_dict()  # Assuming Video has a `to_dict` method
        await self.redis_connector.set(video_key, json.dumps(video_data))
        await self.repository.add_video(video)

    async def get_video(self, video_id: str) -> 'Video':
        log.info(f"Retrieving video with ID: {video_id}")
        video_key = f"video:{video_id}"
        video_data = await self.redis_connector.get(video_key)
        if video_data:
            return Video.from_dict(json.loads(video_data))  # Assuming Video has a `from_dict` method

        log.info(f"Video '{video_id}' not found in Redis cache. Fetching from repository.")
        video = await self.repository.get_video(video_id)
        if video:
            await self.redis_connector.set(video_key, json.dumps(video.to_dict()))
            # Add an additional key for file path
            file_path_key = f"video:file_name:{video.file_name}"
            await self.redis_connector.set(file_path_key, json.dumps(video.to_dict()))
            return video
        return None

    async def update_video_thumbnail(self, video_id: int, thumbnail_id: int):
        log.info(f"Updating thumbnail for video with ID: {video_id}")
        video_key = f"video:{video_id}"
        video_data = await self.redis_connector.get(video_key)
        if video_data:
            video = Video.from_dict(json.loads(video_data))
            video.thumbnail_id = thumbnail_id
            await self.redis_connector.set(video_key, json.dumps(video.to_dict()))
            log.info(f"Updated thumbnail in Redis cache for video '{video_id}'.")
        else:
            log.info(f"Video '{video_id}' not found in Redis cache. Fetching from repository to update thumbnail.")

        await self.repository.update_video_thumbnail(video_id, thumbnail_id)

    async def get_video_by_filename(self, filename: str) -> 'Video':
        log.info(f"Retrieving video with file path: {filename}")
        file_path_key = f"video:file_name:{filename}"
        video_data = await self.redis_connector.get(file_path_key)
        if video_data:
            return Video.from_dict(json.loads(video_data))

        log.info(f"Video with file path '{filename}' not found in Redis cache. Fetching from repository.")
        video = await self.repository.get_video_by_filename(filename)
        if video:
            file_path_key = f"video:file_name:{video.file_name}"
            await self.redis_connector.set(file_path_key, json.dumps(video.to_dict()))
            return video
        return None
    
    async def update_video_details(self, video_id: int, file_name: str, cdn_path: str):
        log.info(f"Updating video details for video with ID: {video_id}")
        video_key = f"video:{video_id}"
        video_data = await self.redis_connector.get(video_key)
        if video_data:
            video = Video.from_dict(json.loads(video_data))
            video.file_name = file_name
            video.cdn_path = cdn_path
            await self.redis_connector.set(video_key, json.dumps(video.to_dict()))
            log.info(f"Updated video details in Redis cache for video '{video_id}'.")
        else:
            log.info(f"Video '{video_id}' not found in Redis cache. Fetching from repository to update details.")

        await self.repository.update_video_details(video_id, file_name, cdn_path)