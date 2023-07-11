
import argparse

from backupinatorclient import BackupinatorClient


if __name__ == "__main__":
    
    backup_client = BackupinatorClient(debug=True)
    backup_client.handle_backup(backup_client.get_opnsense_config(), "opnsense")