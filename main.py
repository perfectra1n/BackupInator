#!/usr/bin/env python3
import argparse

from paramiko.ssh_exception import AuthenticationException
import pyfiglet
import pysftp

# Local import
import log

def get_pfsense_config():
    # Have it ignore the hostkey checks
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    if args.pfsense == 'false':
        logger.error("pfSense IP not provided")
        logger.info("Please provide the IP address / hostname of your pfSense")
        hostname = input("Hostname / IP address of pfSense: ")
    else:
        hostname = args.pfsense[0]

    if args.username == 'false':
        logger.error("Username not provided")
        logger.info("Please provide the username to connect to pfSense as")
        username = input("Username to SSH (SFTP) into pfSense as: ")
    else:
        username = args.username[0]

    with pysftp.Connection(hostname, username=username, private_key=args.pfsense_ssh_private_key, cnopts=cnopts) as sftp:
        try:
            sftp.get('/conf/config.xml', "pfsense_config.xml")
        except AuthenticationException:
            print("Exception")
            
    return



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This is the description for the main parser!"
    )
    parser.add_argument(
        "pfsense_ssh_private_key",
        help="Required. Please provide the path to your private key to be used to SSH into pfSense.",
    )
    parser.add_argument(
        "--pfsense",
        type=str,
        nargs=1,
        default="false",
        help="Optional. Provide the IP address / hostname of the pfSense that you wish to fetch the config of.",
    )
    parser.add_argument(
        "--username",
        type=str,
        nargs=1,
        default="false",
        help="Optional. Provide the username to connect to pfSense as.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Optional. Use this argument if you are debugging any errors.",
    )

    args = parser.parse_args()

    logger = log.get_logger(__file__, debug=args.debug)

    print(pyfiglet.figlet_format("pfSense and PiHole Backup", font = "slant"))
    logger.warning("Please be sure to enable SSH in your pfSense (System -> Advanced -> Admin Access")

    get_pfsense_config()

    logger.debug("Configs successfully retrieved.")
