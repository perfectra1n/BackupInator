#!/usr/bin/env python3
import argparse
import paramiko
from paramiko import client
from paramiko.client import SSHClient
import pyfiglet
import pysftp
import getpass
import tempfile
import tarfile
import os

from paramiko.ssh_exception import AuthenticationException

# Local import
import log


def get_pfsense_config():
    logger.info("Fetching pfSense config...")

    # Have it ignore the hostkey checks
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    hostname = args.pfsense

    if args.user == "false":
        logger.error("Username not provided")
        logger.info("Please provide the username to connect to pfSense as")
        username = input("Username to SSH (SFTP) into pfSense as: ")
    else:
        username = args.user

    with pysftp.Connection(
        hostname,
        username=username,
        private_key=args.private_key,
        cnopts=cnopts,
    ) as sftp:
        try:
            logger.info("Attempting to fetch pfSense config now...")
            sftp.get("/conf/config.xml", args.pfsense_output)
            logger.debug("Fetched SOMETHING, hopefully it's the pfSense config :)")
            logger.info(f"Saved pfSense config to '{args.pfsense_output}'")
        except AuthenticationException as e:
            logger.error(e)
            logger.info(
                "It appears that the credentials that you provded aren't correct, please try again."
            )
    return


def get_pihole_config():
    logger.info("Fetching Pihole configs...")
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    hostname = args.pihole

    if args.user == "false":
        logger.error("Username not provided")
        logger.info("Please provide the username to connect to Pihole as")
        args.user = input("Username to SSH (SFTP) into pihole as: ")

    if args.pihole_password == "false":
        logger.error("Pihole password not provided")
        logger.info(
            "Please enter the sudo password for your Pihole, so that a config package can be generated, as the Pihole command requires admin privilges"
        )
        args.pihole_password = getpass.getpass("Password for Pihole: ")

    logger.info("Connecting to Pihole now to create config package backup...")

    ssh_client = SSHClient()

    # Have it ignore host key warnings
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

    # Because paramiko requires loading the private key...
    while True:
        try:
            loaded_pkey = paramiko.RSAKey.from_private_key_file(args.private_key)
            break
        except FileNotFoundError as e:
            logger.error(e)
            logger.info("SSH file not found. Try again?")
            args.private_key = input("Enter the path to your private ssh key: ")


    ssh_client.connect(args.pihole, username=args.user, pkey=loaded_pkey)
    ssh_client_stdin, ssh_client_stdout, ssh_client_stderr = ssh_client.exec_command(
        f"mkdir -p /tmp/piholeconfigs; cd /tmp/piholeconfigs; echo {args.pihole_password} | sudo -S pihole -a -t"
    )
    logger.info(
        "New config backup package should be located in the '/tmp/piholeconfigs' of your Pihole, fetching the file now..."
    )

    # Have to close the connection before you can read from it :eyes:
    ssh_client.close()

    ssh_client2 = SSHClient()
    ssh_client2.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh_client2.connect(args.pihole, username=args.user, pkey=loaded_pkey)

    ssh_client_stdin, ssh_client_stdout, ssh_client_stderr = ssh_client2.exec_command(
        "cd /tmp/piholeconfigs; ls -t | head -n1", get_pty=True
    )
    # Have to do it in this weird order because of Paramiko
    file_list_output = ssh_client_stdout.readlines()
    # Since what is returned is a list, with newlines and stuff on the end, need to strip it
    filename = file_list_output[0].strip()
    logger.debug(f"Found the newest file to be: {filename}")
    
    while True:
        ssh_clientsdtin, ssh_client_stdout, ssh_client_stderr = ssh_client2.exec_command(f"du -sh /tmp/piholeconfigs/{filename} | cut -d 'K' -f 1", get_pty=True)
        file_size = ssh_client_stdout.readlines()[0]
        error = ssh_client_stderr.readlines()
        if len(error) > 0:
            logger.error(f"Error while getting file size: {error}")
            exit(1)
        logger.debug(f"Got file size of {file_size}")
        if file_size != "0":
            ssh_client2.close()
            break
    
    ssh_client2.close()



    with pysftp.Connection(
        hostname, username=args.user, private_key=args.private_key, cnopts=cnopts
    ) as sftp:
        try:
            logger.info("Attempting to fetch Pihole config backup now...")
            sftp.get(f"/tmp/piholeconfigs/{filename}", args.pihole_output)
            logger.debug("Fetched SOMETHING, hopefully it's the Pihole config :)")
            logger.info(f"Saved Pihole config to '{args.pihole_output}'")
        except AuthenticationException as e:
            logger.error(e)
            logger.info(
                "It appears that the credentials that you provided aren't correct, please try again."
            )

def get_truenas_config():
    logger.info("Fetching Truenas config. . .")
    logger.debug("Please make sure ssh is enabled on the Truenas system and your user has your public key.")

    if args.user != "root":
        logger.debug("Non-root user used. This will likely not work.")

    if args.user == "false":
        logger.error("Username not provided")
        logger.info("Please provide the username to connect to Truenas as")
        args.user = input("Username to SSH (SFTP) into Truenas as: ")

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    hostname = args.truenas
    tempdir = tempfile.gettempdir()

    logger.debug(f"Using {tempdir} for temp files")

    with pysftp.Connection(hostname, username=args.user,private_key=args.private_key,cnopts=cnopts) as sftp:
        try:
            logger.info("Attempting to fetch Truenas config now")
            sftp.get(f"/data/freenas-v1.db", f"{tempdir}/freenas-v1.db")
            if not args.no_secrets:
                sftp.get(f"/data/pwenc_secret", f"{tempdir}/pwenc_secret")
        except AuthenticationException as e:
            logger.error(e)
            logger.info("Credentials provided are not correct, please try again.")
    
    logger.debug(f"Writing tar file to {args.truenas_output}...")
    
    with tarfile.open(args.truenas_output, "w") as tar:
        tar.add(f"{tempdir}/freenas-v1.db",arcname="freenas-v1.db")
        if not args.no_secrets:
            tar.add(f"{tempdir}/pwenc_secret",arcname="pwenc_secret")
    
    logger.debug(f"Removing temp files.")
    os.remove(f"{tempdir}/freenas-v1.db")
    if not args.no_secrets:
        os.remove(f"{tempdir}/pwenc_secret")
    logger.info(f"Trunas config saved to {args.truenas_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Back up Pfsense/Pihole config remotely."
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--pfsense",
        type=str,
        default="false",
        help="Provide the IP address / hostname of the PfSense system that you wish to fetch the config of.",
    )
    target_group.add_argument(
        "--pihole",
        type=str,
        default="false",
        help="Provide the IP address / hostname of the Pihole instance that you wish to fetch the config of.",
    )
    target_group.add_argument(
        "--truenas",
        type=str,
        default="false",
        help="Provide the IP address / hostname of the TrueNas system that you wish to fetch the config for."
    )

    parser.add_argument(
        "--user",
        type=str,
        default="false",
        help="Required. Provide the username to connect as.",
    )
    parser.add_argument(
        "private_key",
        help="Required. Please provide the path to your private key to be used to SSH into PfSense/Pihole.",
    )
    output_group = parser.add_mutually_exclusive_group(required=False)

    output_group.add_argument(
        "--pfsense-output",
        type=str,
        default="pfsense_config.xml",
        help="Optional. Provide the output name of the pfsense config file.",
    )
    output_group.add_argument(
        "--pihole-output",
        type=str,
        default="pihole-teleporter.tar.gz",
        help="Optional. Provide the output name of the PiHole config file.",
    )
    output_group.add_argument(
        "--truenas-output",
        type=str,
        default="truenas.tar",
        help="Optional. Provide the output name of the Truenas config file."
    )
    parser.add_argument(
        "--pihole-password",
        type=str,
        default="false",
        help="Required. Provide the password for your PiHole user sudo password so that the config package can be generated.",
    )
    parser.add_argument(
        "--no-secrets",
        action="store_true",
        default=False,
        help="Use to not store secrets (from Truenas)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Optional. Use this argument if you are debugging any errors.",
    )

    args = parser.parse_args()

    logger = log.get_logger(__file__, debug=args.debug)

    print(pyfiglet.figlet_format("pfSense and PiHole Backup", font="slant"))
    logger.warning(
        "Please be sure to enable SSH in your pfSense (System -> Advanced -> Admin Access)"
    )
    if args.pfsense != "false":
        get_pfsense_config()
    elif args.pihole != "false":
        get_pihole_config()
    elif args.truenas != "false":
        get_truenas_config()

    logger.debug("Reached the end of Python, configs should be saved :)")
