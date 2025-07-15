
import os
import pathlib
import time
import torrent_agent.common.logger as logger
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.common.constants import NON_BROWSER_FRIENDLY_VIDEO_FILETYPES
from torrent_agent.database.dao.video_conversion_dao import IVideoConversionsDAO
from torrent_agent.database.dao.video_dao import IVideosDAO
from torrent_agent.model.video import Video
from torrent_agent.remote.remote_processor import RemoteProcessor
from torrent_agent.video.video_conversion_queue import VideoConversionQueue, VideoConversionQueueEntry
from torrent_agent.common.configuration import Configuration  # Import the Configuration class

log = logger.get_logger()
metric_emitter = MetricEmitter()
configuration = Configuration()
remote_processor = RemoteProcessor()

class VideoProcessor:
    def __init__(self, conversion_queue: VideoConversionQueue, repository: IVideosDAO, conversion_dao: IVideoConversionsDAO):
        self.conversion_queue = conversion_queue
        self.repository = repository

    async def process_video(self,file_name, file_path):
        if await self.repository.get_video(file_path) is None:

            # Skip files that start with 'converting_'
            if file_name.startswith('converting_'):
                log.info(f"File '{file_name}' starts with 'converting_'. Skipping.")
                return

            # Skip files that are still downloading
            if not self.is_file_fully_downloaded(file_path):
                log.info(f"File '{file_name}' is still downloading. Skipping.")
                return

            extension = "."+file_path.split(".")[-1].lower()
            clean_file_name = self.scrub_file_name(file_path)
            
            # Wait for the conversion to complete before adding to the repository
            queue_entry = await self.conversion_queue.get_entry(clean_file_name)
            if queue_entry is not None:
                if queue_entry.is_failed:
                    log.error(f"Conversion of '{clean_file_name}' failed: {queue_entry.error_message}", exc_info=True)
                    return
                if not queue_entry.is_converted:
                    log.info(f"Waiting for conversion of '{clean_file_name}' to complete.")
                    return
                log.info(f"File '{clean_file_name}' is already in the conversion queue. Skipping.")
                return

            
            
            log.debug(f"File '{clean_file_name}' is already in a browser-friendly format: {extension}")
            if configuration.is_remote_agent():
                log.info(f"Using remote processor for file '{clean_file_name}'.")
                # Logic for remote processing can be added here
                # For example, sending the file to a remote processing service
                remote_processor.process_file(clean_file_name)
                return

            # Once processing is complete, add the video to the repository
            entertainment_type = str(clean_file_name.split("/")[3])  # Extract the entertainment type from the path
            cdn_path = clean_file_name.replace(configuration.get_media_directory(), '')
            title = clean_file_name.split("/")[-1].replace(extension, "")  # Extract the title from the file name
            clean_file_name = clean_file_name.replace(configuration.get_media_directory(), '/mnt/ext1')
            video = Video(file_name=clean_file_name, cdn_path=cdn_path, title=title, entertainment_type=entertainment_type, uploaded=None)
            added_video = await self.repository.add_video(video)
            metric_emitter.files_processed.inc()

            # Add to the queue if the file type is non-browser-friendly
            if extension in NON_BROWSER_FRIENDLY_VIDEO_FILETYPES:
                log.debug(f"File '{clean_file_name}' is a non-browser-friendly format: {extension}. Adding to conversion queue.")
                await self.convert_to_browser_friendly_file_type(added_video.id, clean_file_name, extension)
                return
        else:
            log.info(f"File is already processed and stored {file_path}")
        
    async def convert_to_browser_friendly_file_type(self, id, file, extension):
        log.info(f"Converting '{file}' to a browser-friendly format. '{extension}' -> '.mp4'")
        new_file = file.replace(extension, ".mp4")
        conversion_job = VideoConversionQueueEntry(id, file, new_file)
        await self.conversion_queue.add_to_queue(conversion_job)

        return new_file

    def scrub_file_name(self, filePath):
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

    def is_file_fully_downloaded(self, file_path, check_interval=5):
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