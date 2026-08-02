import logging
import sys
from .config import settings

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "N/A"
        return True

def setup_logging():
    level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.addFilter(CorrelationIdFilter())
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s")
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        
    logger = logging.getLogger("pepr")
    return logger
