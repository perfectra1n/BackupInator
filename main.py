#!/usr/bin/env python3
import argparse

from paramiko.ssh_exception import AuthenticationException
import pyfiglet
import pysftp
import paramiko

# Local import
import log


def get_pfsense_config():
    logger.info("Fetching pfSense config now...")

    # Have it ignore the hostkey checks
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    '''
     if args.pfsense == "false":
        logger.error("pfSense IP not provided")
        logger.info("Please provide the IP address / hostname of your pfSense")
        hostname = input("Hostname / IP address of pfSense: ")
    else:
    '''
    hostname = args.pfsense

    if args.username == "false":
        logger.error("Username not provided")
        logger.info("Please provide the username to connect to pfSense as")
        username = input("Username to SSH (SFTP) into pfSense as: ")
    else:
        username = args.username

    with pysftp.Connection(
        hostname,
        username=username,
        private_key=args.private_key,
        cnopts=cnopts,
    ) as sftp:
        try:
            sftp.get("/conf/config.xml", args.pfsense_output)
            logger.debug("Fetched SOMETHING, hopefully it's the pfSense config :)")
            logger.info(f"Saved pfSense config to '{args.pfsense_output}'")
        except AuthenticationException as e:
            logger.error(e)
            logger.info("It appears that the credentials that you provded aren't correct, please try again.")
    return


def get_pihole_config():
    logger.info("Fetching Pihole configs now...")
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    hostname = args.pihole

    if args.username == "false":
        logger.error("Username not provided")
        logger.info("Please provide the username to connect to Pihole as")
        user = input("Username to SSH (SFTP) into pihole as: ")
    else:
        username = args.username
    temp_output = "/tmp/asdf983hkadj"
    with pysftp.Connection(hostname, username=username, private_key=args.private_key, cnopts=cnopts) as sftp:
        filename = sftp.listdir_attr(f"{temp_output}")
        try:
            sftp.get(filename[0], args.pihole-output)
        except AuthenticationException as e:
            logger.error(e)
            logger.info("It appears that the credentials that you provided aren't correct, please try again.")
            

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="This is the description for the main parser!")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--pfsense", type=str, default="false", help="Provide the IP address / hostname of  PfSense that you wish to fetch the config of.")
    target_group.add_argument("--pihole", type=str, default="false",help="Provide the IP address / hostname of Pihole that you wish to fetch the config of.")

    parser.add_argument("--username",type=str,default="false",help="Required. Provide the username to connect as.")
    parser.add_argument("private_key", help="Required. Please provide the path to your private key to be used to SSH into pfSense.")

    parser.add_argument("--pfsense-output", type=str,default="pfsense_config.xml", help="Optional. Provide the output name of the pfsense config file.")
    parser.add_argument("--pihole-output", type=str,default="pihole-teleporter.tar.gz", help="Optional. Provide the output name of the pihole config file.")
    parser.add_argument("--debug", action="store_true", help="Optional. Use this argument if you are debugging any errors.")

    args = parser.parse_args()

    logger = log.get_logger(__file__, debug=args.debug)

    print(pyfiglet.figlet_format("pfSense and PiHole Backup", font="slant"))
    logger.warning(
        "Please be sure to enable SSH in your pfSense (System -> Advanced -> Admin Access"
    )
    if args.pfsense != "false":
        get_pfsense_config()
    elif args.pihole != "false":
        get_pihole_config()

    logger.info("Reached the end of Python, configs should be saved :)")
