from torrent_agent.common import logger
from torrent_agent.database.dao.show_dao import IShowsDAO
from torrent_agent.database.shows_repository import ShowsRepository
from torrent_agent.model.show import Episode, Show
from torrent_agent.database.cache.redis_connector import RedisConnector  # Import RedisConnector
import json

log = logger.get_logger()

class ShowsRepositoryCache(IShowsDAO):
    _instance = None

    def __new__(cls, repository: 'ShowsRepository'):
        if cls._instance is None:
            cls._instance = super(ShowsRepositoryCache, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, repository: 'ShowsRepository'):
        if not self._initialized:
            self.repository = repository
            self.redis_connector = RedisConnector()
            self._initialized = True

    async def initialize_redis(self):
        await self.redis_connector.connect()

    async def add_show(self, show: 'Show') -> int:
        log.info(f"Adding show to cache: {show.show_folder}")
        cached_show = await self.redis_connector.get(show.show_folder)
        if cached_show:
            log.info(f"Show '{show.show_folder}' already exists in cache. Skipping addition.")
            return json.loads(cached_show)["id"]

        show_id = await self.repository.add_show(show)
        await self.redis_connector.set(show.show_folder, json.dumps(show.to_dict()))
        return show_id

    async def get_show(self, show_id: str) -> 'Show':
        log.info(f"Retrieving show with ID: {show_id}")
        cached_show = await self.redis_connector.get(show_id)
        if cached_show:
            return Show.from_dict(json.loads(cached_show))

        log.info(f"Show '{show_id}' not found in cache. Fetching from repository.")
        show = await self.repository.get_show(show_id)
        if show:
            await self.redis_connector.set(show_id, json.dumps(show.to_dict()))
        return show

    async def get_show_by_folder(self, show_folder: str) -> 'Show':
        log.info(f"Retrieving show by folder: {show_folder}")
        cached_show = await self.redis_connector.get(show_folder)
        if cached_show:
            return Show.from_dict(json.loads(cached_show))

        log.info(f"Show folder '{show_folder}' not found in cache. Fetching from repository.")
        show = await self.repository.get_show_by_folder(show_folder)
        if show:
            await self.redis_connector.set(show_folder, json.dumps(show.to_dict()))
        return show

    async def add_season(self, show_id: str, season_number: int) -> int:
        log.info(f"Adding season {season_number} to show with ID: {show_id}")
        cache_key = f"{show_id}_season_{season_number}"
        cached_season = await self.redis_connector.get(cache_key)
        if cached_season:
            log.info(f"Season {season_number} for show ID {show_id} already exists in cache. Skipping addition.")
            return json.loads(cached_season)["id"]

        season_id = await self.repository.add_season(show_id, season_number)
        await self.redis_connector.set(cache_key, json.dumps({"id": season_id}))
        return season_id

    async def add_episode(self, show_id: str, season_id: int, episode: 'Episode') -> int:
        log.info(f"Adding episode {episode.episode_number} to season {season_id} for show with ID: {show_id}")
        cache_key = f"{show_id}_season_{season_id}_episode_{episode.episode_number}"
        cached_episode = await self.redis_connector.get(cache_key)
        if cached_episode:
            log.info(f"Episode {episode.episode_number} for season {season_id} of show ID {show_id} already exists in cache. Skipping addition.")
            return json.loads(cached_episode)["id"]

        episode_id = await self.repository.add_episode(show_id, season_id, episode)
        await self.redis_connector.set(cache_key, json.dumps({"id": episode_id}))
        return episode_id

    async def get_season_by_show_and_number(self, show_id: str, season_number: int) -> dict:
        log.info(f"Retrieving season {season_number} for show with ID: {show_id}")
        cache_key = f"{show_id}_season_{season_number}"
        cached_season = await self.redis_connector.get(cache_key)
        if cached_season:
            return json.loads(cached_season)

        log.info(f"Season {season_number} for show ID {show_id} not found in cache. Fetching from repository.")
        season = await self.repository.get_season_by_show_and_number(show_id, season_number)
        if season:
            await self.redis_connector.set(cache_key, json.dumps(season))
        return season
