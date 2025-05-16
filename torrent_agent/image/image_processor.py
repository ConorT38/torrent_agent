import torrent_agent.common.logger as logger
from torrent_agent.common.database_utils import is_file_in_database
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.common.constants import IMAGE_FILETYPES

log = logger.get_logger()
metric_emitter = MetricEmitter()
connection = DatabaseConnector()

async def process_image(file_name, file_path):
    if not await is_file_in_database(file_name, 'images'):
        extension = "." + file_path.split(".")[-1].lower()

        if extension in IMAGE_FILETYPES:
            await insert_file_metadata(file_name)
        else:
            log.info(f"File '{file_name}' is not a supported image format. Skipping.")
            return
    else:
        log.info("File is already processed and stored: " + file_name)

async def insert_file_metadata(filename):
    log.info("Inserting "+filename+" into the database.")
    try:
        await connection.insert("INSERT INTO images (filename, cdn_path, uploaded) VALUES (\""+filename+"\",\""+filename.replace("/mnt/ext1","")+"\", NOW())")
        metric_emitter.db_inserts.inc()
    except Exception as e:
        log.error(f'Failed to insert to db, failed with error {e}')
        metric_emitter.db_connection_failures.inc()
        raise e