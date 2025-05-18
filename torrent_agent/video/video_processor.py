
import asyncio
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
                file_path = await convert_to_browser_friendly_file_type(file_path, extension)

            clean_file_name = scrub_file_name(file_path)
            await insert_file_metadata(file_name, clean_file_name)
            metric_emitter.files_processed.inc()
    else:
        log.info("File is already processed and stored")

async def insert_file_metadata(filename, file_uuid):
    
    entertainment_type = str(file_uuid.split("/")[3])  # Extract the entertainment type from the path
    log.info("Inserting " + filename + " into the database. "+entertainment_type)
    log.debug(f"Insert values: file_uuid={file_uuid}, cdn_path={file_uuid.replace('/media', '')}, title={filename}, entertainment_type={entertainment_type}")
    try:
        await connection.insert(
            f"INSERT INTO videos (filename, cdn_path, title, uploaded, entertainment_type) VALUES ('{file_uuid}', '{file_uuid.replace('/media', '')}', '{filename}', NOW(), '{entertainment_type}')"
        )
        metric_emitter.db_inserts.inc()
    except Exception as e:
        log.error(f"Failed to insert to db, failed with error {e}")
        metric_emitter.db_connection_failures.inc()
        raise e
    
async def convert_to_browser_friendly_file_type(file, extension):
    try:
        log.info(f"Starting file format conversion for '{file}'.")
        new_file = file.replace(extension, ".mp4")
        with metric_emitter.file_conversion_duration.time():
            # Start the FFmpeg process
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-i", file, "-c", "copy", new_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Check the return code
            if process.returncode != 0:
                log.error(f"FFmpeg failed with return code {process.returncode}. Command: ffmpeg -y -i {file} -c copy {new_file}")
                log.error(f"FFmpeg stderr: {stderr.decode().strip()}")
                raise Exception(f"FFmpeg failed with return code {process.returncode}")

        metric_emitter.files_converted.inc()

        # Remove the original file
        process = await asyncio.create_subprocess_exec("rm", file)
        await process.communicate()
        if process.returncode != 0:
            log.error(f"Failed to remove original file '{file}' with return code {process.returncode}")
            raise Exception(f"Failed to remove original file '{file}'")

        log.info(f"Conversion completed for file '{file}'")
        return new_file
    except Exception as e:
        log.error(f"An error occurred during file conversion: {e}")
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
