import os
import pathlib
import subprocess
from torrent_agent.common import logger
from torrent_agent.common.configuration import Configuration

configuration = Configuration()
log = logger.get_logger()

class TorrentManager:
    def is_tv_show_downloading(self, file_path):
        """
        Checks if the directory containing the file is within a '/tv/' folder and,
        if not a remote agent, uses transmission-remote to check if any torrents
        in that directory are still downloading.
        Returns True if a TV show is still downloading in the folder, False otherwise.
        """
        if configuration.is_remote_agent():
            return False

        # Check if the file is in a '/tv/' directory
        path = pathlib.Path(file_path)
        if '/tv/' not in str(path).replace("\\", "/").lower():
            return False

        # Get the parent directory
        parent_dir = str(path.parent)

        try:
            # List all torrents with their download directories and status
            result = subprocess.run(
                ["transmission-remote", "--auth","pi:raspberry","-l"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            lines = result.stdout.splitlines()
            # Skip header lines, parse each torrent line
            for line in lines[1:]:
                if not line.strip() or line.startswith("Sum:"):
                    continue
                parts = line.split()
                if len(parts) < 9:
                    continue
                # The download directory is usually at the end, but may need to parse with -t <id> -i for more details
                torrent_id = parts[0]
                # Get detailed info for this torrent
                info_result = subprocess.run(
                    ["transmission-remote", "--auth","pi:raspberry","-t", torrent_id, "-i"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                info_lines = info_result.stdout.splitlines()
                download_dir = ""
                percent_done = ""
                for info_line in info_lines:
                    if info_line.strip().startswith("Location:"):
                        download_dir = info_line.split(":", 1)[1].strip()
                    if info_line.strip().startswith("Percent Done:"):
                        percent_done = info_line.split(":", 1)[1].strip()
                # Check if the download directory matches the parent directory
                if os.path.abspath(download_dir) == os.path.abspath(parent_dir):
                    # If percent done is not 100%, it's still downloading
                    if not percent_done.startswith("100%"):
                        log.info(f"TV show in '{parent_dir}' is still downloading (torrent id {torrent_id}). Skipping.")
                        return True
        except Exception as e:
            log.error(f"Error checking transmission-remote: {e}")
            return False

        return False