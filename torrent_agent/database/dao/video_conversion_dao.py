from abc import ABC, abstractmethod
from torrent_agent.model.video_conversion import VideoConversion

class IVideoConversionsDAO(ABC):
    @abstractmethod
    async def add_conversion(self, conversion: 'VideoConversion') -> int:
        """
        Adds a new video conversion record to the database.
        :param conversion: VideoConversion object containing the conversion details.
        :return: The ID of the newly inserted record.
        """
        pass

    @abstractmethod
    async def get_conversion(self, conversion_id: int) -> 'VideoConversion':
        """
        Retrieves a video conversion record by its ID.
        :param conversion_id: ID of the video conversion record.
        :return: VideoConversion object if found, otherwise None.
        """
        pass

    @abstractmethod
    async def update_conversion_status(self, conversion_id: int, status: str, error_message: str = None):
        """
        Updates the status and error message of a video conversion record.
        :param conversion_id: ID of the video conversion record.
        :param status: New status of the conversion.
        :param error_message: Error message if applicable.
        """
        pass