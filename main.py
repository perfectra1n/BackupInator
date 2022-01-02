#!/usr/bin/env python3
import argparse
import paramiko
from paramiko import client
from paramiko.client import SSHClient
import pyfiglet
import pysftp
import getpass
import sys

from paramiko.ssh_exception import AuthenticationException

# Local import
import log


def get_pfsense_config():
    logger.info("Fetching pfSense config now...")

    # Have it ignore the hostkey checks
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    """
     if args.pfsense == "false":
        logger.error("pfSense IP not provided")
        logger.info("Please provide the IP address / hostname of your pfSense")
        hostname = input("Hostname / IP address of pfSense: ")
    else:
    """
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
            logger.info("Fetched SOMETHING, hopefully it's the pfSense config :)")
            logger.info(f"Saved pfSense config to '{args.pfsense_output}'")
        except AuthenticationException as e:
            logger.error(e)
            logger.info(
                "It appears that the credentials that you provded aren't correct, please try again."
            )
    return


def get_pihole_config():
    logger.info("Fetching Pihole configs now...")
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
    loaded_pkey = paramiko.RSAKey.from_private_key_file(args.private_key)

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
    ssh_client2.close()

    # Since what is returned is a list, with newlines and stuff on the end, need to strip it
    filename = file_list_output[0].strip()

    logger.info(f"Found the newest file to be: {filename}")

    with pysftp.Connection(
        hostname, username=args.user, private_key=args.private_key, cnopts=cnopts
    ) as sftp:
        try:
            logger.info("Attempting to fetch Pihole config backup now...")
            sftp.get(f"/tmp/piholeconfigs/{filename}", args.pihole_output)
            logger.info("Fetched SOMETHING, hopefully it's the Pihole config :)")
            logger.info(f"Saved Pihole config to '{args.pihole_output}'")
        except AuthenticationException as e:
            logger.error(e)
            logger.info(
                "It appears that the credentials that you provided aren't correct, please try again."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This is the description for the main parser!"
    )
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--pfsense",
        type=str,
        default="false",
        help="Provide the IP address / hostname of  PfSense that you wish to fetch the config of.",
    )
    target_group.add_argument(
        "--pihole",
        type=str,
        default="false",
        help="Provide the IP address / hostname of Pihole that you wish to fetch the config of.",
    )

    parser.add_argument(
        "--user",
        type=str,
        default="false",
        help="Required. Provide the username to connect as.",
    )
    parser.add_argument(
        "private_key",
        help="Required. Please provide the path to your private key to be used to SSH into pfSense.",
    )

    parser.add_argument(
        "--pfsense-output",
        type=str,
        default="pfsense_config.xml",
        help="Optional. Provide the output name of the pfsense config file.",
    )
    parser.add_argument(
        "--pihole-output",
        type=str,
        default="pihole-teleporter.tar.gz",
        help="Optional. Provide the output name of the PiHole config file.",
    )
    parser.add_argument(
        "--pihole-password",
        type=str,
        default="false",
        help="Optional. Provide the password for your PiHole installation so that the config package can be generated.",
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

    logger.info("Reached the end of Python, configs should be saved :)")
