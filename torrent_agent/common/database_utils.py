import torrent_agent.common.logger as logger
from torrent_agent.common.metrics import MetricEmitter

log = logger.get_logger()
metric_emitter = MetricEmitter()

def is_file_in_database(file, connection, table="videos"):
    log.debug("Checking if "+file+" exists in the database.")
    try:
        result = connection.query("SELECT * FROM "+table+" WHERE title = \""+file+"\" OR filename = \""+file+"\"")
    except Exception as e:
        log.error(f'Failed to select from db, failed with error {e}')
        metric_emitter.db_connection_failures.inc()
        raise e

    return len(result) > 0