from torrent_agent.common import logger
from torrent_agent.database.cache.cache_entry import CacheEntry
from torrent_agent.database.dao.show_dao import IShowsDAO
from torrent_agent.database.shows_repository import ShowsRepository
from torrent_agent.model.show import Episode, Show

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
            self.cache: dict[str, 'CacheEntry'] = {}
            self.repository = repository
            self._initialized = True

    async def add_show(self, show: 'Show') -> int:
        log.info(f"Adding show to cache: {show.show_folder}")
        if show.show_folder in self.cache:
            log.info(f"show '{show.show_folder}' already exists in cache. Skipping addition.")
            return self.cache[show.show_folder].data
        if show.show_folder not in self.cache:
            self.cache[show.show_folder] = CacheEntry(data=show)
            return await self.repository.add_show(show)
    
    async def get_show(self, show_id: str) -> 'Show':
        log.info(f"Retrieving show with ID: {show_id}")
        # Check if the show is in the cache
        if show_id in self.cache:
            cache_entry = self.cache[show_id]
            if not cache_entry.is_expired():
                return cache_entry.data
            else:
                log.info(f"Cache entry for show '{show_id}' is expired. Removing from cache.")
                del self.cache[show_id]
        
        # If not in cache or expired, retrieve from the repository
        log.info(f"show '{show_id}' not found in cache. Fetching from repository.")
        show = await self.repository.get_show(show_id)
        if show:
            self.cache[show_id] = CacheEntry(data=show)
            return show
        return None

    async def get_show_by_folder(self, show_folder: str) -> 'Show':
        log.info(f"Retrieving show by folder: {show_folder}")
        # Check if the show is in the cache
        if show_folder in self.cache:
            cache_entry = self.cache[show_folder]
            if not cache_entry.is_expired():
                return cache_entry.data
            else:
                log.info(f"Cache entry for show folder '{show_folder}' is expired. Removing from cache.")
                del self.cache[show_folder]
        
        # If not in cache or expired, retrieve from the repository
        log.info(f"Show folder '{show_folder}' not found in cache. Fetching from repository.")
        show = await self.repository.get_show_by_folder(show_folder)
        if show:
            self.cache[show_folder] = CacheEntry(data=show)
            return show
        return None
    
    async def add_season(self, show_id: str, season_number: int) -> int:
        log.info(f"Adding season {season_number} to show with ID: {show_id}")
        cache_key = f"{show_id}_season_{season_number}"
        
        if cache_key in self.cache:
            log.info(f"Season {season_number} for show ID {show_id} already exists in cache. Skipping addition.")
            return self.cache[cache_key].data
        
        try:
            season_id = await self.repository.add_season(show_id, season_number)
            self.cache[cache_key] = CacheEntry(data=season_id)
            return season_id
        except Exception as e:
            log.error(f"Failed to add season to repository, failed with error {e}")
            raise e

    async def add_episode(self, show_id: str, season_id: int, episode: 'Episode') -> int:
        log.info(f"Adding episode {episode.episode_number} to season {season_id} for show with ID: {show_id}")
        cache_key = f"{show_id}_season_{season_id}_episode_{episode.episode_number}"
        
        if cache_key in self.cache:
            log.info(f"Episode {episode.episode_number} for season {season_id} of show ID {show_id} already exists in cache. Skipping addition.")
            return self.cache[cache_key].data
        
        try:
            episode_id = await self.repository.add_episode(show_id, season_id, episode)
            self.cache[cache_key] = CacheEntry(data=episode_id)
            return episode_id
        except Exception as e:
            log.error(f"Failed to add episode to repository, failed with error {e}")
            raise e
        
    async def get_season_by_show_and_number(self, show_id: str, season_number: int) -> dict:
        log.info(f"Retrieving season {season_number} for show with ID: {show_id}")
        cache_key = f"{show_id}_season_{season_number}"
        
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if not cache_entry.is_expired():
                return cache_entry.data
            else:
                log.info(f"Cache entry for season {season_number} of show ID {show_id} is expired. Removing from cache.")
                del self.cache[cache_key]
        
        # If not in cache or expired, retrieve from the repository
        log.info(f"Season {season_number} for show ID {show_id} not found in cache. Fetching from repository.")
        season = await self.repository.get_season_by_show_and_number(show_id, season_number)
        if season:
            self.cache[cache_key] = CacheEntry(data=season)
            return season
        return None