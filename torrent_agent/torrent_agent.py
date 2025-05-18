import asyncio
import glob
import os
from pathlib import Path

from torrent_agent.common import logger
from torrent_agent.common.constants import BROWSER_FRIENDLY_VIDEO_FILETYPES, IMAGE_FILETYPES, NON_BROWSER_FRIENDLY_VIDEO_FILETYPES
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.image.image_processor import process_image
from torrent_agent.video.video_conversion_queue import VideoConversionQueue
from torrent_agent.video.video_processor import process_video

metric_emitter = MetricEmitter()
log = logger.get_logger()
video_conversion_queue = VideoConversionQueue()

async def video_conversion_worker():
    """
    Worker task to process video conversion tasks from the queue.
    """
    try:
        await video_conversion_queue.process_queue()
    except Exception as e:
        log.error(f"Error while processing video conversion queue: {e}")

async def main():
    asyncio.create_task(video_conversion_worker())

    for file_path in glob.glob("/mnt/ext1/**/*.*", recursive=True):
        # Skip directories
        if not os.path.isfile(file_path):
            log.debug(f"Skipping directory: {file_path}")
            continue

        file_name = Path(file_path).stem
        log.info("Processing file: " + file_name)

        try:
            extension = "." + file_path.split(".")[-1].lower()
            if extension in NON_BROWSER_FRIENDLY_VIDEO_FILETYPES or extension in BROWSER_FRIENDLY_VIDEO_FILETYPES:
                await process_video(file_name, file_path)
            elif extension in IMAGE_FILETYPES:
                await process_image(file_name, file_path)
            else:
                log.info(f"File '{file_name}' of type '{extension}' is not a supported format. Skipping.")
                continue
        except Exception as e:
            log.error(f"An error occurred while processing file '{file_name}': {e}")
            continue
        
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
                await asyncio.sleep(10)

    asyncio.run(run_agent())

