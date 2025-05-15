import glob
import logging
import os
import pathlib
import sys
import subprocess
import mysql.connector
from pathlib import Path
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import time

logger = logging.getLogger('home-media-torrent-util')
formatter = logging.Formatter('[%(asctime)s][%(levelname)s] -- %(message)s')

fh = logging.FileHandler('/var/log/home-media-torrent-util/info.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

files_processed = Counter('files_processed_total', 'Total number of files processed')
db_inserts = Counter('db_inserts_total', 'Total number of database inserts')
file_conversion_duration = Histogram('file_conversion_duration_seconds', 'Duration of file conversions in seconds')
db_connection_failures = Counter('db_connection_failures_total', 'Total number of database connection failures')
files_converted = Counter('files_converted_total', 'Total number of files converted')
agent_runs_cycles = Counter('agent_run_cycles', 'Total number of run cycles the agent performed')
agent_runs_cycles_failed = Counter('agent_runs_cycles_failed', 'Total number of run cycles the agent performed that failed')
agent_runs_cycles_duration = Histogram('agent_run_cycles_duration_seconds', 'Duration of agent run cycles in seconds')

BROWSER_FRIENDLY_FILETYPES = [".mp4",".webm"]
NON_BROWSER_FRIENDLY_FILETYPES = [".avi",".mov", ".mkv"]

def main():
    db_connection = DB()
    for file_path in glob.glob("/mnt/ext1/torrents/**/*.*", recursive=True):
        # Skip directories
        if not os.path.isfile(file_path):
            logger.debug(f"Skipping directory: {file_path}")
            continue

        file_name = Path(file_path).stem
        logger.info("Processing file: " + file_name)

        if not IsFileInDatabase(file_name, db_connection):

            # Skip files that are still downloading
            if not IsFileFullyDownloaded(file_path):
                logger.info(f"File '{file_name}' is still downloading. Skipping.")
                continue

            extension = "."+file_path.split(".")[-1].lower()

            if extension in NON_BROWSER_FRIENDLY_FILETYPES:
                file_path = ConvertToBroswerFriendlyFileType(file_path, extension)

            clean_file_name = ScrubFileName(file_path)
            InsertFileMetadata(file_name, clean_file_name, db_connection)
        else:
            logger.info("File is already processed and stored")

def IsFileFullyDownloaded(file_path, check_interval=5):
    """
    Checks if a file is fully downloaded by verifying that its size remains constant over a short period.
    """
    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(check_interval)
        final_size = os.path.getsize(file_path)
        return initial_size == final_size
    except FileNotFoundError:
        logger.warning(f"File '{file_path}' not found during download check.")
        return False

def ScrubFileName(filePath):
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
    logger.info(f"renamed '{filePath}' to '{new_file_path}'.") #Using f strings is cleaner.
    files_processed.inc()
    return new_file_path

def IsFileInDatabase(file, connection):
    logger.debug("Checking if "+file+" exists in the database.")
    try:
        result = connection.query("SELECT * FROM videos WHERE title = \""+file+"\" OR filename = \""+file+"\"")
    except Exception as e:
        logger.error(f'Failed to select from db, failed with error {e}')
        db_connection_failures.inc()
        raise e

    return len(result) > 0

def InsertFileMetadata(filename, file_uuid, connection):
    logger.info("Inserting "+filename+" into the database.")
    try:
        connection.insert("INSERT INTO videos (filename, cdn_path, title, uploaded) VALUES (\""+file_uuid+"\",\""+file_uuid.replace("/media","")+"\",\""+filename+"\", NOW())")
        db_inserts.inc()
    except Exception as e:
        logger.error(f'Failed to insert to db, failed with error {e}')
        db_connection_failures.inc()
        raise e

def ConvertToBroswerFriendlyFileType(file, extension):
    try:
        logger.info("Starting file format conversion for '"+file+"'.")
        new_file = file.replace(extension, ".mp4")
        with file_conversion_duration.time():
            subprocess.run(["ffmpeg", "-y","-i", file, "-c", "copy", new_file], check=True) #added check = True
        files_converted.inc()
        subprocess.run(["rm", file], check=True) #added check=True
        logger.info("Conversion completed for file '"+file+"'")

        return new_file
    except subprocess.CalledProcessError as e:
        print(f'Command {e.cmd} failed with error {e.returncode}')
        logger.error(f'Command {e.cmd} failed with error {e.returncode}')
        raise e

class DB:
    def __init__(self):
        self.host = "192.168.0.23"
        self.user = "root"
        self.password = "raspberry"
        self.database = "homemedia"

    def query(self, sql, retry_count=0):
        try:
            with mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database) as conn:
                with conn.cursor() as mycursor:
                    mycursor.execute(sql)
                    return mycursor.fetchall()
        except mysql.connector.Error as e:
            retry_count += 1
            if retry_count < 3:
                return self.query(sql, retry_count)
            raise e

    def insert(self, sql, retry_count=0):
        try:
            with mysql.connector.connect(host=self.host, user=self.user, password=self.password, database=self.database) as conn:
                with conn.cursor() as mycursor:
                    mycursor.execute(sql)
                    conn.commit()
        except mysql.connector.Error as e:
            retry_count += 1
            if retry_count < 3:
                return self.insert(sql, retry_count)
            raise e

if __name__ == "__main__":
    logger.info("Starting home media torrent util agent...")
    start_http_server(8002)
    while True:
        with agent_runs_cycles_duration.time():
            try:
                main()
                logger.info("Completed processing.")
                agent_runs_cycles.inc()
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                agent_runs_cycles_failed.inc()
            time.sleep(10)

