
import os
import pathlib
import time
import torrent_agent.common.logger as logger
from torrent_agent.common.database_utils import is_file_in_database
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.cache.videos_cache import VideosRepositoryCache
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.common.constants import NON_BROWSER_FRIENDLY_VIDEO_FILETYPES
from torrent_agent.database.videos_repository import VideosRepository
from torrent_agent.model.video import Video
from torrent_agent.video.video_conversion_queue import VideoConversionQueue, VideoConversionQueueEntry

log = logger.get_logger()
metric_emitter = MetricEmitter()
connection = DatabaseConnector()
repository = VideosRepositoryCache(VideosRepository(connection))
video_conversion_queue = VideoConversionQueue()

async def process_video(file_name, file_path):
    if await repository.get_video(file_name) is None:

        # Skip files that are still downloading
        if not is_file_fully_downloaded(file_path):
            log.info(f"File '{file_name}' is still downloading. Skipping.")
            return

        extension = "."+file_path.split(".")[-1].lower()
        clean_file_name = scrub_file_name(file_path)

        if extension in NON_BROWSER_FRIENDLY_VIDEO_FILETYPES:
            clean_file_name = await convert_to_browser_friendly_file_type(file_path, extension)

        entertainment_type = str(clean_file_name.split("/")[3])  # Extract the entertainment type from the path
        cdn_path = clean_file_name.replace('/mnt/ext1', '')
        title = clean_file_name.split("/")[-1].replace(extension, "")  # Extract the title from the file name

        video = Video(file_name=clean_file_name, cdn_path=cdn_path, title=title, entertainment_type=entertainment_type, uploaded=None)
        await repository.add_video(video)
        metric_emitter.files_processed.inc()
    else:
        log.info("File is already processed and stored")
    
async def convert_to_browser_friendly_file_type(file, extension):
    log.info(f"Converting '{file}' to a browser-friendly format. '{extension}' -> '.mp4'")
    new_file = file.replace(extension, ".mp4")
    conversion_job = VideoConversionQueueEntry(file, new_file)
    await video_conversion_queue.add_to_queue(conversion_job)

    return new_file

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
