import argparse

# Local import
import log

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This is the description for the main parser!"
    )
    parser.add_argument(
        "required_arg",
        help="Required. This is the description for the main requirement.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Optional. Use this argument if you are debugging any errors.",
    )

    args = parser.parse_args()

    logger = log.get_logger(__file__, debug=args.debug)

    logger.debug("This is the debug logger!")
    logger.info(f"This is {__file__}")
