import torrent_agent.common.logger as logger
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.database_connector import DatabaseConnector

log = logger.get_logger()
connection = DatabaseConnector()
metric_emitter = MetricEmitter()

async def is_file_in_database(file, table="videos"):
    log.debug("Checking if "+file+" exists in the database.")
    try:
        result = await connection.query("SELECT * FROM "+table+" WHERE title = \""+file+"\" OR filename = \""+file+"\"")
    except Exception as e:
        log.error(f'Failed to select from db, failed with error {e}', exc_info=True)
        metric_emitter.db_connection_failures.inc()
        raise e

    return len(result) > 0