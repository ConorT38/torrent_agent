import os
import pathlib
import subprocess
from torrent_agent.common import logger
from torrent_agent.common.configuration import Configuration
from torrent_agent.database.cache.shows_cache import ShowsRepositoryCache
from torrent_agent.database.dao.show_dao import IShowsDAO
import re

from torrent_agent.model.show import Show

configuration = Configuration()
log = logger.get_logger()

class TorrentManager:
    def __init__(self, shows_repository: IShowsDAO):
        """
        Initializes the TorrentManager with a ShowsRepository instance.
        :param shows_repository: An instance of IShowsDAO to interact with the shows database.
        """
        self.shows_repository = shows_repository

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
            log.error(f"Error checking transmission-remote: {e}", exc_info=True)
            return False

        return False
    
    async def add_show_to_database(self, folder_path):
        """
        Adds a show to the database by checking the folder structure and adding seasons and episodes.
        """

        # Ensure the folder is within '/torrents/tv/'
        path = pathlib.Path(folder_path)
        # Ensure the folder is within '/torrents/tv/' and is not deeper than one level (xyz format)
        path_parts = str(path).replace("\\", "/").lower().split('/torrents/tv/')
        if len(path_parts) != 2 or '/' in path_parts[1]:
            log.error(f"Folder '{folder_path}' is not in the expected '/torrents/tv/xyz' format.", exc_info=True)
            return

        # Extract the show folder name (xyz)
        show_folder = path.name
        show = await self.shows_repository.get_show_by_folder(show_folder)

        if not show:
            log.warning(f"Show folder '{show_folder}' does not exist in the database.", exc_info=True)

            # Add the show to the database
            show = await self.shows_repository.add_show(
                Show(
                    name=show_folder,
                    description="",
                    thumbnail_id=1,
                    show_folder=show_folder
                )
            )
            log.info(f"Added show '{show_folder}' to the database.")
            return

        show_id = show['id']

        # Iterate through subfolders (seasons)
        for subfolder in path.iterdir():
            if subfolder.is_dir():
                try:
                    # Extract season number from folder name
                    match = re.search(r'\d+', subfolder.name)
                    if match:
                        season_number = int(match.group())
                    else:
                        raise ValueError(f"Could not extract season number from folder name '{subfolder.name}'.")
                except ValueError:
                    log.warning(f"Skipping folder '{subfolder}' as it does not represent a season.")
                    continue

                # Check if the season already exists
                existing_season = await self.shows_repository.get_season_by_show_and_number(show_id, season_number)
                if existing_season:
                    log.info(f"Season {season_number} for show '{show_folder}' already exists. Skipping.")
                    continue

                # Add the season
                await self.shows_repository.add_season(show_id, season_number)
                log.info(f"Added season {season_number} for show '{show_folder}'.")

                # Check for episodes within the season folder
                for file in subfolder.iterdir():
                    if file.is_file():
                        # Extract season and episode numbers from the filename (e.g., S01E06)
                        match = re.search(r'[Ss](\d+)[Ee](\d+)', file.stem)
                        if match:
                            season_from_file = int(match.group(1))
                            episode_number = int(match.group(2))

                            # Ensure the season matches the folder's season
                            if season_from_file != season_number:
                                log.warning(f"File '{file.name}' does not match season {season_number}. Skipping.")
                                continue

                            # Add the episode
                            await self.shows_repository.add_episode(show_id, season_number, episode_number)
                            log.info(f"Added episode {episode_number} to season {season_number} for show '{show_folder}'.")
                        else:
                            log.warning(f"Skipping file '{file.name}' as it does not match the SxxExx pattern.")