import argparse

from classes.backupinatortruenas import BackupinatorTrueNAS

if __name__ == "__main__":
    backup_client = BackupinatorTrueNAS(debug=True)
    
    #backup_client.handle_backup(backup_client.get_opnsense_config(), "opnsense")
    backup_client.handle_backup(backup_client.download_truenas_config(), "truenas")


