import logging
from logging.handlers import RotatingFileHandler #writes logs into logging destination(app.log)
#rotating - file is archived or replaced when it becomes larger

logger = logging.getLogger("online-shopping-api")

logger.setLevel(logging.INFO)

logger.propagate = False #it prevents from printing the same message twice


if not logger.handlers: #it prevents duplicate log entries
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    #handler writes log
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=5 * 1024 * 1024, #(5MB)
        backupCount=3, #3 backup files - app.log(newest logs), app.log.1,...3
        encoding="utf-8"
    )

    file_handler.setFormatter(formatter) #it writes to app.log

    console_handler = logging.StreamHandler() #it wrtites to the console

    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.addHandler(console_handler)
