from abc import ABC, abstractmethod
from torrent_agent.model.video import Video

class IVideosDAO(ABC):
    @abstractmethod
    async def add_video(self, video: 'Video'):
        """Add a video to the repository."""
        pass

    @abstractmethod
    async def get_video(self, video_id: str) -> 'Video':
        """Retrieve a video from the repository by its ID."""
        pass

    @abstractmethod
    async def update_video_thumbnail(self, video_id: str, thumbnail_path: str):
        """Update the thumbnail path for a video in the repository."""
        pass

    @abstractmethod
    async def get_video_by_filename(self, filename: str) -> 'Video':
        """Retrieve a video from the repository by its file path."""
        pass