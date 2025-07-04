import asyncio

from torrent_agent.common import logger
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.remote.remote_processor import RemoteProcessor
from torrent_agent.video.video_converter import VideoConverter
from torrent_agent.common.configuration import Configuration

log = logger.get_logger()
metric_emitter = MetricEmitter()
remote_processor = RemoteProcessor()  # Assuming RemoteProcessor is defined elsewhere
configuration = Configuration()

class VideoConversionQueueEntry:
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.is_converted = False
        self.is_failed = False
        self.error_message = None

    def mark_as_converted(self):
        self.is_converted = True
        log.info(f"Video {self.input_file} has been marked as converted.")

    def mark_as_failed(self, error_message: str):
        self.is_failed = True
        self.error_message = error_message
        log.info(f"Video {self.input_file} conversion failed: {error_message}")
    
    def __str__(self):
        status = "Converted" if self.is_converted else "Failed" if self.is_failed else "Pending"
        return f"VideoConversionQueueEntry(input_file={self.input_file}, output_file={self.output_file}, status={status}, error_message={self.error_message})"

class VideoConversionQueue:
    _instance = None

    def __init__(self):
        self.queue = asyncio.Queue()
        self.converter = VideoConverter()
        self.remote_requests_left = len(configuration.get_remote_hosts())

    async def add_to_queue(self, video_conversion_entry: VideoConversionQueueEntry):
        if not configuration.is_remote_agent():
            if self.remote_requests_left > 0:
                log.info(f"Adding {str(video_conversion_entry)} to remote conversion queue.")
                remote_processor.process_file(video_conversion_entry.input_file)
                self.remote_requests_left -= 1
                return
            else:
                log.warning("No remote requests left, skipping remote conversion.")
                self.remote_requests_left = len(configuration.get_remote_hosts())
        await self.queue.put(video_conversion_entry)
        log.info(f"Added {str(video_conversion_entry)} to conversion queue.")
    
    async def get(self):
        if not self.queue.empty():
            video_conversion_entry = await self.queue.get()
            return video_conversion_entry
        else:
            return None
    
    async def get_entry(self, input_file: str) -> VideoConversionQueueEntry:
        temp_queue = asyncio.Queue()
        target_entry = None

        while not self.queue.empty():
            entry = await self.queue.get()
            if entry.input_file == input_file:
                target_entry = entry
            await temp_queue.put(entry)

        while not temp_queue.empty():
            await self.queue.put(await temp_queue.get())

        return target_entry

    async def process_queue(self):
        while not self.queue.empty():
            video_conversion_entry: VideoConversionQueueEntry = await self.queue.get()
            try:
                log.info(f"Converting {str(video_conversion_entry)}")
                with metric_emitter.file_conversion_duration.time():
                    await self.converter.convert(video_conversion_entry.input_file, video_conversion_entry.output_file)
                video_conversion_entry.mark_as_converted()
                metric_emitter.files_converted.inc()
            except Exception as e:
                video_conversion_entry.mark_as_failed(str(e))
                log.error(f"Failed to perform conversion, skipping:  {str(video_conversion_entry)}: {e}")
            finally:
                self.queue.task_done()