import logging
import sys
import time

from fastapi import Request

from core.config import settings

logger = logging.getLogger("Organization_manager_logger")

log_formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)
logger.handlers = [stream_handler]
logger.setLevel(getattr(logging, settings.log_level, logging.INFO))


async def request_log(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    log_data = {
        "method": request.method,
        "path": request.url.path,
        "process_time": str(process_time),
        "status_code": response.status_code,
    }
    logger.info(log_data)
    return response
