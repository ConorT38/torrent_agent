import os
import paramiko
from scp import SCPClient
from torrent_agent.common.configuration import Configuration
from torrent_agent.common import logger

log = logger.get_logger()

class RemoteProcessor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RemoteProcessor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the RemoteProcessor with a list of remote hosts, username, and password.
        :param hosts: List of remote host IPs.
        :param username: SSH username.
        :param password: SSH password.
        """
        if not hasattr(self, "initialized"):
            self.configuration = Configuration()
            self.hosts = self.configuration.get_remote_hosts()
            self.current_host_index = 0
            self.initialized = True

    def _file_exists_on_remote(self, host, remote_path):
        """
        Check if a file exists on the remote host.
        :param host: Remote host IP.
        :param remote_path: Path to check on the remote host.
        :return: True if the file exists, False otherwise.
        """
        try:
            log.debug(f"Checking if file exists on remote host {host}: {remote_path}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=self.get_username(host))
            stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path} && echo exists || echo missing")
            result = stdout.read().decode().strip()
            ssh.close()
            return result == "exists"
        except Exception as e:
            log.error(f"Error checking file on remote host {host}: {e}")
            return False

    def _scp_file_to_remote(self, host, local_path, remote_path):
        """
        SCP a file to the remote host.
        :param host: Remote host IP.
        :param local_path: Path to the local file.
        :param remote_path: Path to copy the file to on the remote host.
        """
        try:
            log.debug(f"Copying file to remote host {host}: {local_path} -> {remote_path}")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=self.get_username(host))
            with SCPClient(ssh.get_transport()) as scp:
                scp.put(local_path, remote_path)
            log.debug(f"File {local_path} copied to {host}:{remote_path}")
            ssh.close()
        except Exception as e:
            log.error(f"Error copying file to remote host {host}: {e}")

    def _get_next_host(self):
        """
        Get the next host in a round-robin fashion.
        :return: The next host IP.
        """
        host = self.hosts[self.current_host_index]
        self.current_host_index = (self.current_host_index + 1) % len(self.hosts)
        return host

    def process_file(self, local_path):
        """
        Process a file by SCPing it to a remote host in a round-robin fashion and removing it locally.
        :param local_path: Path to the local file.
        """
        if not os.path.exists(local_path):
            log.log(f"File {local_path} does not exist locally.")
            return
        base_remote_path = "/mnt/ext1/torrents"
        host = None
        remote_path = None
        if self.configuration.is_remote_host:
            if "movies" in local_path:
                remote_path = f"{base_remote_path}/movies/{os.path.basename(local_path)}"
            elif "tv" in local_path:
                remote_path = f"{base_remote_path}/tv/{os.path.basename(local_path)}"
            else:
                remote_path = f"{base_remote_path}/videos/{os.path.basename(local_path)}"
            host = "192.168.0.23"
        else:
            host = self._get_next_host()
            remote_path = f"/home/{self.get_username(host)}/conversions/{os.path.basename(local_path)}"
            
        if not self._file_exists_on_remote(host, remote_path):
            log.log(f"Copying {local_path} to {host}:{remote_path}")
            self._scp_file_to_remote(host, local_path, remote_path)
            log.log(f"File {local_path} copied to {host}. Removing local file.")
            os.remove(local_path)
        else:
            log.log(f"File already exists on remote host {host}. No action taken.")

    def get_username(self, host):
        """
        Get the SSH username based on the host.
        :param host: Remote host IP.
        :return: SSH username.
        """
        return "conor" if host in ["192.168.0.25", "192.168.0.28"] else "pi"

        
