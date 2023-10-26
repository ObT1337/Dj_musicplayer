import inspect
import logging
import os


class Logger:
    def __init__(self, name, ch_level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        os.makedirs("logs", exist_ok=True)
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.ch = logging.StreamHandler()
        self.ch.setLevel(ch_level)
        self.fh = logging.FileHandler(f"{self.dir_path}/debug.log")
        self.fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.ch.setFormatter(formatter)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.ch)
        self.logger.addHandler(self.fh)

    def setLevel(self, level):
        self.ch.setLevel(level)

    def add_file_handler(self, file_handler_name, level):
        self.__dict__[file_handler_name] = logging.FileHandler(
            f"{self.dir_path}/{file_handler_name}.log"
        )
        self.__dict__[file_handler_name].setLevel(level)

    def manipulate_message(self, msg, caller_line):
        frame, filename, line_num, func_name, lines, index = inspect.getouterframes(
            caller_line
        )[1]
        return f"{line_num}:\n{msg}\n" + "=" * 20

    def debug(self, msg):
        msg = self.manipulate_message(msg, inspect.currentframe())
        self.logger.debug(msg)

    def info(self, msg):
        msg = self.manipulate_message(msg, inspect.currentframe())
        self.logger.info(msg)

    def warning(self, msg):
        msg = self.manipulate_message(msg, inspect.currentframe())
        self.logger.warning(msg)

    def error(self, msg):
        msg = self.manipulate_message(msg, inspect.currentframe())
        self.logger.error(msg)

    def critical(self, msg):
        msg = self.manipulate_message(msg, inspect.currentframe())
        self.logger.critical(msg)
