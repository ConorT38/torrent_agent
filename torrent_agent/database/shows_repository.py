from torrent_agent.common import logger
from torrent_agent.database.dao.show_dao import IShowsDAO
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.model.show import Show, Episode

log = logger.get_logger()

class ShowsRepository(IShowsDAO):
    def __init__(self, db: 'DatabaseConnector'):
        self.db = db

    async def get_show(self, show_id) -> 'Show':
        log.info(f"Retrieving show with ID: {show_id}")
        result = await self.db.query(f"SELECT * FROM shows WHERE id = {show_id}")
        if result:
            show_data = result[0]
            return Show(
                id=show_data[0],
                name=show_data[1],
                description=show_data[2],
                thumbnail_id=show_data[3],
                show_folder=show_data[4] if len(show_data) > 4 else None
            )
        return None

    async def add_show(self, show: 'Show') -> int:
        log.info(f"Inserting show {show.name} into the database.")
        try:
            last_row_id = await self.db.insert(
                f"INSERT INTO shows (name, description, thumbnail_id) VALUES ('{show.name}', '{show.description}', {show.thumbnail_id})")
            return last_row_id
        except Exception as e:
            log.error(f'Failed to insert show to db, failed with error {e}', exc_info=True)
            raise e
        
    async def get_show_by_folder(self, show_folder: str) -> 'Show':
        log.info(f"Retrieving show with folder: {show_folder}")
        result = await self.db.query(f"SELECT * FROM shows WHERE show_folder = '{show_folder}'")
        if result:
            show_data = result[0]
            return Show(
                id=show_data[0],
                name=show_data[1],
                description=show_data[2],
                thumbnail_id=show_data[3],
                show_folder=show_data[4]
            )
        return None
    
    async def add_season(self, show_id: str, season_number: int) -> int:
        log.info(f"Adding season {season_number} to show with ID: {show_id}")
        try:
            last_row_id = await self.db.insert(
                f"INSERT INTO seasons (show_id, season_number) VALUES ({show_id}, {season_number})"
            )
            return last_row_id
        except Exception as e:
            log.error(f"Failed to add season to db, failed with error {e}", exc_info=True)
            raise e

    async def add_episode(self, show_id: str, season_id: int, episode: 'Episode') -> int:
        log.info(f"Adding episode {episode.episode_number} to season {season_id} for show with ID: {show_id}")
        try:
            last_row_id = await self.db.insert(
                f"INSERT INTO episodes (video_id, episode_number, show_id, description, season_id) "
                f"VALUES ({episode.video_id}, {episode.episode_number}, {show_id}, '{episode.description}', {season_id})"
            )
            return last_row_id
        except Exception as e:
            log.error(f"Failed to add episode to db, failed with error {e}", exc_info=True)
            raise e
        
    async def get_season_by_show_and_number(self, show_id: str, season_number: int) -> dict:
        log.info(f"Retrieving season {season_number} for show with ID: {show_id}")
        result = await self.db.query(
            f"SELECT * FROM seasons WHERE show_id = {show_id} AND season_number = {season_number}"
        )
        if result:
            return {
                'id': result[0][0],
                'show_id': result[0][1],
                'season_number': result[0][2]
            }
        return None
