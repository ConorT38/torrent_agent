from abc import ABC, abstractmethod
from torrent_agent.model.show import Show, Episode

class IShowsDAO(ABC):
    @abstractmethod
    async def add_show(self, show: 'Show') -> int:
        """Add a show to the repository."""
        pass

    @abstractmethod
    async def get_show(self, show_id: str) -> 'Show':
        """Retrieve a show from the repository by its ID."""
        pass

    @abstractmethod
    async def get_show_by_folder(self, show_folder: str) -> 'Show':
        """Retrieve a show from the repository by its folder."""
        pass

    @abstractmethod
    async def add_season(self, show_id: str, season_number: int) -> int:
        """Add a season to a show in the repository."""
        pass

    @abstractmethod
    async def add_episode(self, show_id: str, season_id: int, episode: Episode) -> int:
        """Add an episode to a season in the repository."""
        pass

    @abstractmethod
    async def get_season_by_show_and_number(self, show_id: str, season_number: int) -> dict:
        """Retrieve a season by show ID and season number."""
        pass