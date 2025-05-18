import asyncio

from torrent_agent.video.video_converter import VideoConverter

class VideoConversionQueueEntry:
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file
        self.is_converted = False
        self.is_failed = False
        self.error_message = None

    def mark_as_converted(self):
        self.is_converted = True
        print(f"Video {self.input_file} has been marked as converted.")

    def mark_as_failed(self, error_message: str):
        self.is_failed = True
        self.error_message = error_message
        print(f"Video {self.input_file} conversion failed: {error_message}")
    
    def __str__(self):
        status = "Converted" if self.is_converted else "Failed" if self.is_failed else "Pending"
        return f"VideoConversionQueueEntry(input_file={self.input_file}, output_file={self.output_file}, status={status}, error_message={self.error_message})"

class VideoConversionQueue:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VideoConversionQueue, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "queue"):  # Prevent reinitialization
            self.queue = asyncio.Queue()
            self.converter = VideoConverter()

    async def add_to_queue(self, video_conversion_entry: VideoConversionQueueEntry):
        await self.queue.put(video_conversion_entry)
        print(f"Added {str(video_conversion_entry)} to conversion queue.")
    
    async def get(self):
        if not self.queue.empty():
            video_conversion_entry = await self.queue.get()
            print(f"Retrieved {str(video_conversion_entry)} from conversion queue.")
            return video_conversion_entry
        else:
            print("Queue is empty.")
            return None

    async def process_queue(self):
        while not self.queue.empty():
            video_conversion_entry = await self.queue.get()
            try:
                await self.converter.convert(video_conversion_entry)
                video_conversion_entry.mark_as_converted()
            except Exception as e:
                video_conversion_entry.mark_as_failed(str(e))