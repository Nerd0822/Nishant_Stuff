import logging


class Logger:
    _logger = None

    @staticmethod
    def make_logger(name="applog", output="app.log"):
        if Logger._logger is None:
            logger = logging.getLogger(name)

            logger.setLevel(level=logging.DEBUG)

            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
            )

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            # logger.addHandler(console_handler)

            file_handler = logging.FileHandler(output)
            file_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            
            Logger._logger = logger

        return Logger._logger
