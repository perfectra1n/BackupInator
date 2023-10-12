import pysftp
import requests
import os
import tempfile
from datetime import datetime

from classes.baseclass import BaseBackupClass
from classes.backupinatornextcloud import BackupinatorNextcloud


class BackupinatorTrueNAS(BackupinatorNextcloud):
    def __init__(self, debug=False) -> None:
        super().__init__(debug=debug)

        self.system = "truenas"
        keys_required = ["username", "private_key_path", "ip", "api_key"]
        self.validate_config(required_keys=keys_required, system=self.system)
        self.values = self.config[self.system]
        self.file_ending = ".tar"

    def download_truenas_config(self):
        headers = {
            'Authorization': f'Bearer {self.values["api_key"]}',
            'accept': '*/*',
            'Content-Type': 'application/json',
        }
        data = '{"secretseed": true}'
        response = requests.post(f'http://{self.values["ip"]}/api/v2.0/config/save', headers=headers, data=data)

        if response.status_code == 200:

            return self.put_data_in_tempfile(response.content, 'tar')
        else:
            self.logger.error(f'Error downloading TrueNAS config: {response.status_code}')
            self.logger.error(response.content)
            return ''
