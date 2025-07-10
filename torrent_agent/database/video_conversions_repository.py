from torrent_agent.common import logger
from torrent_agent.database.dao.video_conversion_dao import IVideoConversionsDAO
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.model.video_conversion import VideoConversion

log = logger.get_logger()

class VideoConversionsRepository(IVideoConversionsDAO):
    def __init__(self, db: 'DatabaseConnector'):
        self.db = db
        self.table_name = 'video_conversions'

    async def add_conversion(self, conversion: 'VideoConversion') -> int:
        sql = f"""
        INSERT INTO {self.table_name} (original_video_id, original_filename, converted_filename, conversion_status, error_message, created_at, updated_at)
        VALUES ({conversion.original_video_id}, '{conversion.original_filename}', '{conversion.converted_filename}', '{conversion.conversion_status}', '{conversion.error_message}', NOW(), NOW())
        """
        log.info(f"Inserting video conversion record into the database. [{sql}]")
        try:
            last_row_id = await self.db.insert(sql)
            return last_row_id
        except Exception as e:
            log.error(f"Failed to insert video conversion record to db, failed with error {e}", exc_info=True)
            raise e

    async def get_conversion(self, conversion_id: int) -> 'VideoConversion':
        sql = f"SELECT * FROM {self.table_name} WHERE id = {conversion_id}"
        log.info(f"Retrieving video conversion record with ID: {conversion_id}. [{sql}]")
        result = await self.db.query(sql)
        if result:
            conversion_data = result[0]
            return VideoConversion.from_dict({
                "id": conversion_data[0],
                "original_video_id": conversion_data[1],
                "original_filename": conversion_data[2],
                "converted_filename": conversion_data[3],
                "conversion_status": conversion_data[4],
                "error_message": conversion_data[5],
                "created_at": conversion_data[6],
                "updated_at": conversion_data[7],
            })
        return None

    async def update_conversion_status(self, conversion_id: int, status: str, error_message: str = None):
        sql = f"UPDATE {self.table_name} SET conversion_status = '{status}', error_message = '{error_message}', updated_at = NOW() WHERE id = {conversion_id}"
        log.info(f"Updating video conversion record with ID: {conversion_id}. [{sql}]")
        try:
            await self.db.insert(sql)
        except Exception as e:
            log.error(f"Failed to update video conversion record in db, failed with error {e}", exc_info=True)
            raise e