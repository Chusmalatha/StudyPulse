import logging
import sys

def setup_logging():
    # Setup basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Silence third-party loggers if necessary
    logging.getLogger("pymongo").setLevel(logging.WARNING)

logger = logging.getLogger("ai_study_companion")
