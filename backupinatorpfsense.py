import pysftp
from paramiko import client
from paramiko.client import SSHClient
from paramiko.ssh_exception import AuthenticationException

from baseclass import BaseBackupClass

class BackupinatorPfSense(BaseBackupClass):
    def __init__(self, debug=False) -> None:
        super().__init__(debug=debug)
        
        self.system = "pfsense"
        keys_required = ["username", "private_key_path", "ip"]
        self.validate_config(required_keys=keys_required, system=self.system)
    
        self.values = self.config[self.system]
    
    def get_pfsense_config(self):
        self.logger.info("Fetching pfSense config...")

        # Have it ignore the hostkey checks
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(
            self.values["hostname"],
            username=self.values["username"],
            private_key=self.values["ssh_key_path"],
            cnopts=cnopts,
        ) as sftp:
            try:
                self.logger.info("Attempting to fetch pfSense config now...")
                with sftp.open("/conf/config.xml", "r") as f:
                    config_loc = self.put_data_in_tempfile(f.read())
                self.logger.debug("Fetched SOMETHING, hopefully it's the pfSense config :)")
                self.logger.info(f"Saved pfSense config to '{args.pfsense_output}'")
            except AuthenticationException as e:
                self.logger.error(e)
                self.logger.info(
                    "It appears that the credentials that you provded aren't correct, please try again."
                )

        