import asyncio
import subprocess
from torrent_agent.common import logger
from torrent_agent.common.metrics import MetricEmitter

log = logger.get_logger()
metric_emitter = MetricEmitter()

class VideoConverter:
    """
    A class to handle video file conversion using ffmpeg.
    Attributes:
        input_file (str): The path to the input video file.
        output_file (str): The path to the output video file.
    Methods:
        convert():
            Converts the input video file to the specified output format using ffmpeg.
            Tracks the duration of the conversion process and increments a conversion metric.
            Deletes the input file after successful conversion and logs the completion.
    """

    async def convert(self, input_file: str, output_file: str):
        try:
            command = [
                        "ffmpeg",
                        "-y",
                        "-i", input_file,
                        "-c:v", "libx264",  # Encode video to H.264 (AVC)
                        "-preset", "medium", # Controls encoding speed vs. compression efficiency (medium is a good balance)
                        "-crf", "23",       # Constant Rate Factor: controls video quality (23 is a good default, lower means higher quality/larger file)
                        "-pix_fmt", "yuv420p", # Ensures compatibility with older players/browsers
                        "-profile:v", "baseline", # Ensures compatibility with most browsers
                        "-level", "3.0",         # Ensures compatibility with most browsers
                        "-c:a", "aac",           # Encode audio to AAC
                        "-b:a", "128k",          # Audio bitrate (adjust as needed, 128k is common for good quality)
                        "-ac", "2",              # Force stereo audio
                        "-movflags", "+faststart",
                        output_file
                    ]
            log.info(f"Conversion started: {' '.join(command)}")
            with metric_emitter.file_conversion_duration.time():
                # Offload the blocking subprocess call to a separate thread
                await asyncio.to_thread(
                    subprocess.run,
                    command,
                    check=True
                )
            metric_emitter.files_converted.inc()

            # Offload the file removal to a separate thread
            await asyncio.to_thread(subprocess.run, ["rm", input_file], check=True)
            log.info(f"Conversion completed for file '{input_file}'")
        except Exception as e:
            log.error(f"Failed to convert video '{input_file}' to '{output_file}': {e}")
            try:
                remux_command = [
                        "ffmpeg",
                        "-y",
                        "-i", input_file,
                        "-c:v", "libx264",  # Encode video to H.264 (AVC)
                        "-preset", "medium", # Controls encoding speed vs. compression efficiency (medium is a good balance)
                        "-crf", "23",       # Constant Rate Factor: controls video quality (23 is a good default, lower means higher quality/larger file)
                        "-pix_fmt", "yuv420p", # Ensures compatibility with older players/browsers
                        "-c:a", "aac",      # Encode audio to AAC
                        "-b:a", "128k",     # Audio bitrate (adjust as needed, 128k is common for good quality)
                        "-movflags", "+faststart",
                        input_file  # Remux to the same file
                    ]
                log.info(f"Attempting remux operation: {' '.join(remux_command)}")
                await asyncio.to_thread(
                    subprocess.run,
                    remux_command,
                    check=True
                )
                log.info(f"Remux operation completed for file '{input_file}'")
            except Exception as remux_error:
                log.error(f"Failed to perform remux operation on '{input_file}': {remux_error}")
                raise e