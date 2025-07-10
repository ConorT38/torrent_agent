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
    async def update_video_thumbnail(self, video_id: int, thumbnail_id: int):
        """Update the thumbnail path for a video in the repository."""
        pass

    @abstractmethod
    async def get_video_by_filename(self, filename: str) -> 'Video':
        """Retrieve a video from the repository by its file path."""
        pass

    @abstractmethod
    async def update_video_details(self, video_id: int, file_name: str, cdn_path: str):
        """Update the video details in the repository."""
        pass