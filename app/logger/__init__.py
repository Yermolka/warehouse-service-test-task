import os
from logging import Formatter, StreamHandler, getLogger

is_debug = os.getenv("DEBUG", "False").lower() == "true"

handler = StreamHandler()
handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s"))

# Basic ugly logger, should use structured logging for better exceptions readability
logger = getLogger("warehouse-app")
logger.addHandler(handler)
logger.setLevel("DEBUG" if is_debug else "INFO")
