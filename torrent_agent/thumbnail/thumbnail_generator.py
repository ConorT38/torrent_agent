import os
import cv2
from torrent_agent.common import logger
from torrent_agent.common.metrics import MetricEmitter
from torrent_agent.database.cache.images_cache import ImagesRepositoryCache
from torrent_agent.database.cache.videos_cache import VideosRepositoryCache
from torrent_agent.model.image import Image

log = logger.get_logger()
metric_emitter = MetricEmitter()

class ThumbnailGenerator:
    def __init__(self, video_repository: VideosRepositoryCache, image_repository: ImagesRepositoryCache):
        self.video_repository = video_repository
        self.image_repository = image_repository
        self.image_dir = "/mnt/ext1/images"
        log.debug(f"ThumbnailGenerator initialized with image_dir: {self.image_dir}")

    async def generate_thumbnail(self, file_path, file_name):
        log.debug(f"Starting thumbnail generation for file_path: {file_path}, file_name: {file_name}")

        # Check if the video exists and has no thumbnail_id
        video = await self.video_repository.get_video_by_filename(file_path)
        log.debug(f"Video lookup result for file_path: {file_path}: {video}")

        if not video:
            log.error("Video not found in the database.")
            return

        video_id = video.id
        thumbnail_id = video.thumbnail_id
        log.debug(f"Video ID: {video_id}, Thumbnail ID: {thumbnail_id}")

        if thumbnail_id:
            log.info("Video already has a thumbnail. Skipping thumbnail generation.")
            return

        # Ensure the file is an .mp4 file
        if not file_path.endswith(".mp4"):
            log.error(f"Unsupported file format for {file_path}. Only .mp4 files are supported.")
            return

        video_file = file_path
        log.debug(f"Constructed video file path: {video_file}")

        if not os.path.exists(video_file):
            log.error(f"Video file does not exist at path: {video_file}")
            return

        # Capture the video and get the half-point frame
        cap = cv2.VideoCapture(video_file)
        if not cap.isOpened():
            log.error(f"Failed to open video file: {video_file}")
            return

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        log.debug(f"Total frame count for video: {frame_count}")

        half_frame = frame_count // 2
        log.debug(f"Setting video capture to half-point frame: {half_frame}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, half_frame)

        ret, frame = cap.read()
        if not ret:
            log.error(f"Failed to read frame at position {half_frame} from video: {video_file}")
            cap.release()
            return

        # Save the frame as a JPEG
        os.makedirs(self.image_dir, exist_ok=True)
        log.debug(f"Ensured image directory exists: {self.image_dir}")

        image_path = os.path.join(self.image_dir, f"{os.path.splitext(file_name)[0]}-{video_id}.jpeg")
        log.debug(f"Saving thumbnail to path: {image_path}")

        if not cv2.imwrite(image_path, frame):
            log.error(f"Failed to write thumbnail image to path: {image_path}")
            cap.release()
            return

        cap.release()
        log.debug("Video capture released.")

        # Insert into images table and update videos table
        image = Image(
            file_name=os.path.basename(image_path),
            cdn_path=image_path.replace('/mnt/ext1', ''),
            uploaded=None
        )
        log.debug(f"Creating Image object: {image}")

        image_id = await self.image_repository.add_image(image)
        log.debug(f"Image inserted into repository with ID: {image_id}")

        await self.video_repository.update_video_thumbnail(video_id, image_id)
        log.debug(f"Updated video record with video_id: {video_id} to include thumbnail_id: {image_id}")

        log.info(f"Thumbnail generated and saved at {image_path}.")
