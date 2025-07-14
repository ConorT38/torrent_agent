import asyncio
import subprocess
from torrent_agent.common import logger
from torrent_agent.common.configuration import Configuration
from torrent_agent.common.metrics import MetricEmitter
import os

log = logger.get_logger()
metric_emitter = MetricEmitter()
configuration = Configuration()

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
            # Check if the input file has "converting_" prefix
            if "converting_" in input_file:
                log.error(f"Input file '{input_file}' indicates a previous failed conversion. Deleting it.", exc_info=True)
                await asyncio.to_thread(os.remove, input_file)
                return

            dir_name, base_name = os.path.split(output_file)
            temp_output_file = os.path.join(dir_name, f"converting_{base_name}")

            command = [
                "ffmpeg",
                "-y",
                "-i", input_file,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-profile:v", "baseline",  # Change to baseline for broader compatibility
                "-level", "3.1",          # Lower level for older devices
                "-c:a", "aac",
                "-b:a", "192k",           # Increase audio bitrate for better compatibility
                "-ac", "2",
                "-movflags", "+faststart",
                temp_output_file
            ]
            if not configuration.is_remote_agent:
                command = ['nice', '-n', '15', 'ionice', '-c', '3'] + command
            log.info(f"Conversion started: {' '.join(command)}")
            with metric_emitter.file_conversion_duration.time():
                # Offload the blocking subprocess call to a separate thread
                await asyncio.to_thread(
                    subprocess.run,
                    command,
                    check=True
                )
            metric_emitter.files_converted.inc()

            # Rename the temporary output file to the final output file
            await asyncio.to_thread(os.rename, temp_output_file, output_file)

            # Offload the file removal to a separate thread
            await asyncio.to_thread(os.remove, input_file)
            log.info(f"Conversion completed for file '{input_file}'")
        except Exception as e:
            log.error(f"Failed to convert video '{input_file}' to '{output_file}': {e}", exc_info=True)
            try:
                remux_command = [
                    "ffmpeg",
                    "-y",
                    "-i", input_file,
                    "-c:v", "libx264",
                    "-preset", "medium",
                    "-crf", "23",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-movflags", "+faststart",
                    input_file  # Remux to the same file
                ]
                if not configuration.is_remote_agent:
                    remux_command = ['nice', '-n', '15', 'ionice', '-c', '3'] + remux_command
                log.info(f"Attempting remux operation: {' '.join(remux_command)}")
                await asyncio.to_thread(
                    subprocess.run,
                    remux_command,
                    check=True
                )
                log.info(f"Remux operation completed for file '{input_file}'")
            except Exception as remux_error:
                log.error(f"Failed to perform remux operation on '{input_file}': {remux_error}", exc_info=True)
                # Delete the temporary output file if it exists
                if os.path.exists(temp_output_file):
                    await asyncio.to_thread(os.remove, temp_output_file)
                raise e