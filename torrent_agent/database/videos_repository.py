from torrent_agent.common import logger
from torrent_agent.database.dao.video_dao import IVideosDAO
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.model.video import Video

log = logger.get_logger()

class VideosRepository(IVideosDAO):
    def __init__(self, db: 'DatabaseConnector'):
        self.db = db
        self.table_name = 'videos'

    async def add_video(self, video: 'Video') -> 'Video':
        sql = f"INSERT INTO {self.table_name} (filename, cdn_path, title, uploaded, entertainment_type) VALUES ('{video.file_name}', '{video.cdn_path}', '{video.title}', NOW(), '{video.entertainment_type}')"

        log.info(f"Inserting {video.file_name} into the videos table. [{sql}]")
        try:
            last_row_id = await self.db.insert(sql)
            if "/movies/" in video.cdn_path:
                movie_sql = f"INSERT INTO movies (name, video_id) VALUES ('{video.title}', {last_row_id})"
                log.info(f"Inserting {video.file_name} into the movies table. [{movie_sql}]")
                await self.db.insert(movie_sql)
            
            # Retrieve the inserted video by ID
            return await self.get_video(last_row_id)
        except Exception as e:
            log.error(f'Failed to insert to db, failed with error {e}', exc_info=True)
            raise e
    
    async def get_video(self, video_id: str) -> 'Video':
        log.info(f"Retrieving video with ID: {video_id}")
        result = await self.db.query("SELECT filename, cdn_path, title, uploaded, entertainment_type, id, thumbnail_id FROM videos WHERE title = \""+video_id+"\" OR filename = \""+video_id+"\"")
        if result:
            video_data = result[0]
            return Video(
                file_name=video_data[0],
                cdn_path=video_data[1],
                title=video_data[2],
                uploaded=video_data[3],
                entertainment_type=video_data[4],
                id=video_data[5],
                thumbnail_id=video_data[6]
            )
        return None
    
    async def update_video_thumbnail(self, video_id: int, thumbnail_id: int):
        sql = f"UPDATE {self.table_name} SET thumbnail_id = {thumbnail_id} WHERE id = {video_id}"
        log.info(f"Updating thumbnail for video with ID: {video_id}. [{sql}]")
        try:
            await self.db.insert(sql)
        except Exception as e:
            log.error(f'Failed to update thumbnail in db, failed with error {e}', exc_info=True)
            raise e
        
    async def get_video_by_filename(self, filename: str) -> 'Video':
        log.info(f"Retrieving video with filename: {filename}: [SELECT filename, cdn_path, title, uploaded, entertainment_type, id, thumbnail_id FROM videos WHERE filename = '{filename}']")
        result = await self.db.query(f"SELECT filename, cdn_path, title, uploaded, entertainment_type, id, thumbnail_id FROM videos WHERE filename = '{filename}'")
        if result:
            video_data = result[0]
            log.debug(f"Video data retrieved: {video_data}")
            return Video(
                file_name=video_data[0],
                cdn_path=video_data[1],
                title=video_data[2],
                uploaded=video_data[3],
                entertainment_type=video_data[4],
                id= video_data[5],
                thumbnail_id=video_data[6] 
            )
        return None
    
    async def update_video_details(self, video_id: int, file_name: str, cdn_path: str, is_browser_friendly: bool = False):
        sql = f"UPDATE {self.table_name} SET filename = '{file_name}', cdn_path = '{cdn_path}', browser_friendly = {is_browser_friendly} WHERE id = {video_id}"
        log.info(f"Updating video details for video with ID: {video_id}. [{sql}]")
        try:
            await self.db.insert(sql)
        except Exception as e:
            log.error(f'Failed to update video details in db, failed with error {e}', exc_info=True)
            raise e