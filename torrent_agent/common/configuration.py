import os
from dotenv import load_dotenv

class Configuration:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # File system configuration
        self.media_directory = os.getenv("MEDIA_DIRECTORY", "/mnt/ext1")

        # Database configuration
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")

        # Redis configuration
        self.redis_host = os.getenv("REDIS_HOST", "192.168.0.26")
        self.redis_port = os.getenv("REDIS_PORT", "6379")
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.redis_db = os.getenv("REDIS_DB", "0")

        self.control_agent_host = os.getenv("CONTROL_AGENT_HOST")

        # Remote agent configuration
        self.is_remote_agent_host = os.getenv("IS_REMOTE_AGENT_HOST")
        self.remote_agent_hosts = os.getenv("REMOTE_AGENT_HOSTS", "").split(",") if os.getenv("REMOTE_AGENT_HOSTS") else []

    def get_database_config(self):
        return {
            "host": self.db_host,
            "port": self.db_port,
            "name": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }
    
    def get_redis_config(self):
        return {
            "host": self.redis_host,
            "port": self.redis_port,
            "password": self.redis_password,
            "db": self.redis_db,
        }
    
    def is_remote_agent(self):
        return  bool(int(self.is_remote_agent_host))

    def get_media_directory(self):
        return self.media_directory
    
    def get_remote_hosts(self):
        """
        Returns a list of remote hosts configured in the environment variables.
        If no remote hosts are configured, returns an empty list.
        """
        return self.remote_agent_hosts if self.remote_agent_hosts else []
    
    def get_control_agent_host(self):
        """
        Returns the control agent host configured in the environment variables.
        If not configured, returns None.
        """
        return self.control_agent_host if self.control_agent_host else None