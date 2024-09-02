import logging

# Define log format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create a custom logger
logger = logging.getLogger("shop_logger")
logger.setLevel(logging.DEBUG)

# Create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handler
formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)

# Special logging functions
def log_dust_collector(message):
    logger.info(f"🌀 {message}")

def log_error(message):
    logger.error(f"💢 {message}")

def log_info(message):
    logger.info(message)

def log_warning(message):
    logger.warning(message)

def log_debug(message):
    logger.debug(message)
