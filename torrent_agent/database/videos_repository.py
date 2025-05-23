from torrent_agent.common import logger
from torrent_agent.database.dao.video_dao import IVideosDAO
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.model.video import Video

log = logger.get_logger()

class VideosRepository(IVideosDAO):
    def __init__(self, db: 'DatabaseConnector'):
        self.db = db
        self.table_name = 'videos'

    async def add_video(self, video: 'Video'):
        log.info(f"Inserting {video.filename} into the database.")
        try:
            await self.db.insert(
                f"INSERT INTO {self.table_name} (filename, cdn_path, title, uploaded, entertainment_type) VALUES ('{video.filename}', '{video.cdn_path}', '{video.title}', NOW(), '{video.entertainment_type}')"
            )
        except Exception as e:
            log.error(f'Failed to insert to db, failed with error {e}')
            raise e
    
    async def get_video(self, video_id: str) -> 'Video':
        log.info(f"Retrieving video with ID: {video_id}")
        result = await self.db.query("SELECT filename, cdn_path, title, uploaded, entertainment_type FROM videos WHERE title = \""+video_id+"\" OR filename = \""+video_id+"\"")
        if result:
            video_data = result[0]
            return Video(
                file_name=video_data[0],
                cdn_path=video_data[1],
                title=video_data[2],
                uploaded=video_data[3],
                entertainment_type=video_data[4]
            )
        return None