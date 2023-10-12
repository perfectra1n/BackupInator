import requests
import datetime
import shutil
import os

from classes.baseclass import BaseBackupClass


class BackupinatorNextcloud(BaseBackupClass):
    def __init__(self, debug=False) -> None:
        """
        Initializes a new instance of the BackupinatorNextcloud class.

        :param url: The URL of the Nextcloud server.
        :param username: The username to use for authentication.
        :param password: The password to use for authentication.
        """
        super().__init__(debug=debug)

        system = "nextcloud"
        self.nextcloud_values = self.config[system]

        self.nextcloud_url = self.nextcloud_values["ip"]
        self.nextcloud_username = self.nextcloud_values["username"]
        self.nextcloud_session = self.get_requests_session()
        self.nextcloud_session.auth = (self.nextcloud_values["username"], self.nextcloud_values["password"])
        
        

    def list_files(self, directory):
        """
        Lists the files in the specified directory.

        :param directory: The directory to list the files in.
        :return: A list of the names of the files in the directory.
        """
        url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{directory}"
        response = self.nextcloud_session.request("PROPFIND", url)
        response.raise_for_status()
        files = []
        for item in response.xml.findall(".//{DAV:}response"):
            href = item.find(".//{DAV:}href").text
            if href.endswith("/"):
                files.append(href.split("/")[-2])
        return files

    def upload_file(self, local_path, remote_backup_path):
        """
        Uploads a file to the specified remote path.

        :param local_path: The local path of the file to upload.
        :param remote_backup_path: The remote path to upload the file to.
        """
        url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{remote_backup_path}"
        with open(local_path, "rb") as f:
            response = self.nextcloud_session.put(url, data=f)
        response.raise_for_status()

    def download_file(self, remote_backup_path, local_path):
        """
        Downloads a file from the specified remote path to the specified local path.

        :param remote_backup_path: The remote path of the file to download.
        :param local_path: The local path to download the file to.
        """
        url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{remote_backup_path}"
        response = self.nextcloud_session.get(url)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(response.content)

    def create_folder(self, folder_path):
        """
        Creates a folder at the specified path.

        :param folder_path: The path of the folder to create.
        """
        url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{folder_path}"
        response = self.nextcloud_session.request("MKCOL", url)
        response.raise_for_status()

    def delete_file_or_folder(self, path):
        """
        Deletes the file or folder at the specified path.

        :param path: The path of the file or folder to delete.
        """
        url = f"{self.nextcloud_url}/remote.php/dav/files/{self.nextcloud_username}/{path}"
        response = self.nextcloud_session.delete(url)
        response.raise_for_status()

    def handle_backup(self, source_file_path: str, file_name: str):
        
        formatted_date = datetime.date.today().strftime("%m_%d_%y")
        final_file_name = f"{file_name}_{formatted_date}{self.file_ending}"
        
        self.logger.info(f"Backing up {source_file_path} to {self.config['backup_to']}")

        if self.config["backup_to"] == "nextcloud":
            path = f"{self.config['nextcloud']['remote_backup_path']}/{final_file_name}"
            self.upload_file(source_file_path, path)

        if self.config["backup_to"] == "local":
            shutil.move(
                source_file_path, f"{self.config['local']['backup_path']}/{final_file_name}"
            )