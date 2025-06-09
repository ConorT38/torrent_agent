import torrent_agent.common.logger as logger
from torrent_agent.common.database_utils import is_file_in_database
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.cache.images_cache import ImagesRepositoryCache
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.common.constants import IMAGE_FILETYPES
from torrent_agent.model.image import Image

log = logger.get_logger()
metric_emitter = MetricEmitter()
connection = DatabaseConnector()

class ImageProcessor:
    def __init__(self, repository: ImagesRepositoryCache):
        self.repository = repository

    async def process_image(self, file_name, file_path):
        if await self.repository.get_image(file_name) is None:
            extension = "." + file_path.split(".")[-1].lower()

            if extension in IMAGE_FILETYPES:
                cdn_path = file_path.replace('/mnt/ext1', '')
                image = Image(file_name=file_name, cdn_path=cdn_path, uploaded=None)
                await self.repository.add_image(image)
            else:
                log.info(f"File '{file_name}' is not a supported image format. Skipping.")
                return
        else:
            log.info("File is already processed and stored: " + file_name)