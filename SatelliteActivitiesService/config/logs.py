from dotenv import load_dotenv
import logging
import os

load_dotenv()

log_level = str(os.environ['LOG_LEVEL']).upper()
log_format = str(os.environ['LOG_FORMAT'])
logging.basicConfig(format=log_format, level=log_level)

logger = logging.getLogger(__name__)
logger.debug(f"Logging configurations set. Logging level: {log_level}, Logging format: {log_format}")