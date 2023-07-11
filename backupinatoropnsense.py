import pysftp
from paramiko import client
from paramiko.client import SSHClient
from paramiko.ssh_exception import AuthenticationException

from baseclass import BaseBackupClass

class BackupinatorOPNsense(BaseBackupClass):
    def __init__(self, debug=False) -> None:
        super().__init__(debug=debug)
        
        self.system = "opnsense"
        keys_required = ["api_key", "api_secret", "ip"]
        self.validate_config(required_keys=keys_required, system=self.system)
    
        self.values = self.config[self.system]
        
        self.opnsense_url = self.values["ip"] + "/api"
        self.opnsense_session = self.get_requests_session()
        self.opnsense_session.auth = (self.values["api_key"], self.values["api_secret"])
    
    def get_opnsense_config(self):
        self.logger.info("Fetching opnsense config...")
        
        response = self.opnsense_session.request("GET", self.opnsense_url + "/backup/backup/download?format=plain")
        return self.put_data_in_tempfile(response.content)

        