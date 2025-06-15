from abc import ABC, abstractmethod
from torrent_agent.model.image import Image

class IImagesDAO(ABC):
    @abstractmethod
    async def add_image(self, image: 'Image') -> int:
        """Add a image to the repository."""
        pass

    @abstractmethod
    async def get_image(self, image_id: str) -> 'Image':
        """Retrieve a image from the repository by its ID."""
        pass