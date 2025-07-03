import asyncio
import glob
import os
from pathlib import Path

from torrent_agent.common import logger
from torrent_agent.common.constants import BROWSER_FRIENDLY_VIDEO_FILETYPES, IMAGE_FILETYPES, NON_BROWSER_FRIENDLY_VIDEO_FILETYPES
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.cache.images_cache import ImagesRepositoryCache
from torrent_agent.database.cache.shows_cache import ShowsRepositoryCache
from torrent_agent.database.cache.videos_cache import VideosRepositoryCache
from torrent_agent.database.database_connector import DatabaseConnector
from torrent_agent.database.images_repository import ImagesRepository
from torrent_agent.database.shows_repository import ShowsRepository
from torrent_agent.database.videos_repository import VideosRepository
from torrent_agent.image.image_processor import ImageProcessor
from torrent_agent.thumbnail.thumbnail_generator import ThumbnailGenerator
from torrent_agent.torrent.torrent_manager import TorrentManager
from torrent_agent.video.video_conversion_queue import VideoConversionQueue
from torrent_agent.video.video_processor import VideoProcessor
from torrent_agent.common.configuration import Configuration  # Import the Configuration class

metric_emitter = MetricEmitter()
log = logger.get_logger()

connection = DatabaseConnector()
video_repository = VideosRepositoryCache(VideosRepository(connection))
image_repository = ImagesRepositoryCache(ImagesRepository(connection))
shows_repository = ShowsRepositoryCache(ShowsRepository(connection))
torrent_manager = TorrentManager(shows_repository)
configuration = Configuration()

async def main():
    video_conversion_queue = VideoConversionQueue()
    video_processor = VideoProcessor(video_conversion_queue, video_repository)
    image_processor = ImageProcessor(image_repository)
    thumbnail_generator = ThumbnailGenerator(video_repository, image_repository)

    async def video_conversion_worker():
        """
        Worker task to process video conversion tasks from the queue.
        """
        try:
            await video_conversion_queue.process_queue()
        except Exception as e:
            log.error(f"Error while processing video conversion queue: {e}")

    for file_path in glob.glob(f"{configuration.get_media_directory()}/**/*.*", recursive=True):
        # Skip directories
        if not os.path.isfile(file_path):
            log.debug(f"Checking if directory is a TV show: {file_path}")
            await torrent_manager.add_show_to_database(file_path)
            log.debug(f"Skipping directory: {file_path}")
            continue

        file_name = Path(file_path).stem
        log.info("Processing file: " + file_name)

        try:
            extension = "." + file_path.split(".")[-1].lower()
            if extension in NON_BROWSER_FRIENDLY_VIDEO_FILETYPES or extension in BROWSER_FRIENDLY_VIDEO_FILETYPES:
                if torrent_manager.is_tv_show_downloading(file_name):
                    log.info(f"Show '{file_name}' is still downloading. Skipping.")
                    continue
                await video_processor.process_video(file_name, file_path)

                if not configuration.is_remote_agent():
                    await thumbnail_generator.generate_thumbnail(file_path, file_name)
            elif extension in IMAGE_FILETYPES:
                await image_processor.process_image(file_name, file_path)
            else:
                log.info(f"File '{file_name}' of type '{extension}' is not a supported format. Skipping.")
                continue
        except Exception as e:
            log.error(f"An error occurred while processing file '{file_name}': {e}")
            continue
    
    asyncio.create_task(video_conversion_worker())
    # Wait for all video conversions to complete
    await video_conversion_queue.queue.join()
    log.info("All video conversions completed.")
        
if __name__ == "__main__":
    log.info("Starting home media torrent util agent...")

    async def run_agent():
        while True:
            with metric_emitter.agent_runs_cycles_duration.time():
                try:
                    await main()
                    log.info("Completed processing.")
                    metric_emitter.agent_runs_cycles.inc()
                except Exception as e:
                    log.error(f"An error occurred: {e}")
                    metric_emitter.agent_runs_cycles_failed.inc()
                await asyncio.sleep(300)

    asyncio.run(run_agent())

