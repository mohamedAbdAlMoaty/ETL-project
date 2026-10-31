import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler   # This is a special logging handler that automatically creates backup log files when the main log reaches a certain size.
from contextlib import contextmanager
import time


def setup_logging(log_file="logs/pipeline.log",level=logging.INFO):

    # Create log directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Log format : The formatter determines how each log message looks.
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler(terminal) A handler determines where the log message goes. StreamHandler() normally sends messages to the console/terminal.
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # File handler : a handler that writes logs to a file. The main log file can reach approximately: 5 MB and When it reaches that size, Python rotates it. becomes: pipeline.log.1 then pipeline.log.2 then pipeline.log.3 When another rotation happens, the oldest one is removed.This prevents unlimited disk usage
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5_000_000,   # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()            # getLogger() tells you where the message came from when I write logging.getLogger(__name__) on the class
    root_logger.setLevel(level)
    root_logger.handlers.clear()                 # Remove existing handlers

    # Prevent duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)


@contextmanager
def log_step(logger, step_name):
    # A custom context manager : logs START / DONE / FAILED + duration.
    logger.info(f"START  {step_name}")
    started = time.time()
    try:
        yield
    except Exception:
        logger.error(f"FAILED {step_name}", exc_info=True)
        raise
    else:
        logger.info(f"DONE   {step_name} ({time.time() - started:.2f}s)")        