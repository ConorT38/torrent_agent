
import os
import pathlib
import subprocess
import time
import torrent_agent.common.logger as logger
from torrent_agent.common.database_utils import is_file_in_database
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.common.constants import NON_BROWSER_FRIENDLY_VIDEO_FILETYPES

log = logger.get_logger()
metric_emitter = MetricEmitter()
connection = DatabaseConnector()

async def process_video(file_name, file_path):
    if not await is_file_in_database(file_name):

            # Skip files that are still downloading
            if not is_file_fully_downloaded(file_path):
                log.info(f"File '{file_name}' is still downloading. Skipping.")
                return

            extension = "."+file_path.split(".")[-1].lower()

            if extension in NON_BROWSER_FRIENDLY_VIDEO_FILETYPES:
                file_path = convert_to_browser_friendly_file_type(file_path, extension)

            clean_file_name = scrub_file_name(file_path)
            insert_file_metadata(file_name, clean_file_name)
    else:
        log.info("File is already processed and stored")

async def insert_file_metadata(filename, file_uuid):
    log.info("Inserting " + filename + " into the database.")
    entertainment_type = file_uuid.split("/")[3]  # Extract the entertainment type from the path
    try:
        await connection.insert(
            "INSERT INTO videos (filename, cdn_path, title, uploaded, entertainment_type) VALUES (%s, %s, %s, NOW(), %s)",
            (file_uuid, file_uuid.replace("/media", ""), filename, entertainment_type)
        )
        metric_emitter.db_inserts.inc()
    except Exception as e:
        log.error(f"Failed to insert to db, failed with error {e}")
        metric_emitter.db_connection_failures.inc()
        raise e
    
def convert_to_browser_friendly_file_type(file, extension):
    try:
        log.info("Starting file format conversion for '"+file+"'.")
        new_file = file.replace(extension, ".mp4")
        with metric_emitter.file_conversion_duration.time():
            subprocess.run(["ffmpeg", "-y","-i", file, "-c", "copy", new_file], check=True) #added check = True
        metric_emitter.files_converted.inc()
        subprocess.run(["rm", file], check=True) #added check=True
        log.info("Conversion completed for file '"+file+"'")

        return new_file
    except subprocess.CalledProcessError as e:
        print(f'Command {e.cmd} failed with error {e.returncode}')
        log.error(f'Command {e.cmd} failed with error {e.returncode}')
        raise e

def scrub_file_name(filePath):
    """
    Renames only the file within a given path, leaving the directory structure intact.
    """
    path_object = pathlib.Path(filePath)
    directory = path_object.parent  # Get the directory part
    original_filename = path_object.name  # Get the original file name
    extension = path_object.suffix #get the file extension

    # Scrub the file name (without the directory)
    scrubbed_filename = original_filename.replace(" ", "_")
    chars = "'`*{}[]()>#+-!$"
    for c in chars:
        scrubbed_filename = scrubbed_filename.replace(c, "")

    # Reconstruct the full path with the scrubbed file name
    new_file_path = os.path.join(directory, scrubbed_filename)

    #rename the file, keeping the same extension.
    new_file_path = new_file_path.replace(extension, "") + extension

    os.rename(filePath, new_file_path)
    log.info(f"renamed '{filePath}' to '{new_file_path}'.") #Using f strings is cleaner.
    metric_emitter.files_processed.inc()
    return new_file_path

def is_file_fully_downloaded(file_path, check_interval=5):
    if file_path.endswith(".part"):
        log.info(f"File '{file_path}' is a partial download (.part). Skipping.")
        return False
    
    """
    Checks if a file is fully downloaded by verifying that its size remains constant over a short period.
    """
    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(check_interval)
        final_size = os.path.getsize(file_path)
        return initial_size == final_size
    except FileNotFoundError:
        log.warning(f"File '{file_path}' not found during download check.")
        return False
