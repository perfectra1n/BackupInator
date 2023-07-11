

from backupinatornextcloud import BackupinatorNextcloud
from backupinatorpfsense import BackupinatorPfSense
from backupinatoropnsense import BackupinatorOPNsense

import shutil
import datetime

class BackupinatorClient(BackupinatorNextcloud, BackupinatorPfSense, BackupinatorOPNsense):
    def __init__(self, debug=False):
        super().__init__(debug=debug)
    
    def handle_backup(self, file_path:str, system:str):
        formatted_date = datetime.date.today().strftime("%m_%d_%y")
        new_filename = f"{formatted_date}_{system}.txt"
        
        if self.config["backup_to"] == "nextcloud":
            
            path = f"{self.config['nextcloud']['remote_backup_path']}/{new_filename}"
            print("file_path")
            print(file_path)
            self.upload_file(file_path, path)
            
        if self.config["backup_to"] == "local":
            shutil.move(file_path, f"{self.config['local']['backup_path']}/{new_filename}")