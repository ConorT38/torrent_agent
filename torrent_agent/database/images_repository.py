from torrent_agent.common import logger
from torrent_agent.database.dao.image_dao import IImagesDAO
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.model.image import Image

log = logger.get_logger()

class ImagesRepository(IImagesDAO):
    def __init__(self, db: 'DatabaseConnector'):
        self.db = db

    async def get_image(self, image_id) -> 'Image':
        log.info(f"Retrieving video with ID: {image_id}")
        result = await self.db.query("SELECT * FROM videos WHERE filename = ?", [image_id])
        if result:
            video_data = result[0]
            return Image(
            file_name=video_data[0],
            cdn_path=video_data[1],
            uploaded=video_data[2],
            )
        return None

    async def add_image(self, image: 'Image'):
        log.info(f"Inserting {image.file_name} into the database.")
        try:
            await self.db.insert(
                f"INSERT INTO images (filename, cdn_path, uploaded) VALUES ('{image.file_name}', '{image.cdn_path}', NOW())"
            )
        except Exception as e:
            log.error(f'Failed to insert image to db, failed with error {e}')
            raise e
