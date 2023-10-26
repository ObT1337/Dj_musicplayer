import logging
import os


class UISettings:
    def __init__(self) -> None:
        self.window_title = "ID3 Tagedit"
        self.screen_width = 800
        self.screen_height = 600


class IOSettings:
    wd = os.path.abspath(os.path.dirname(__file__))


class LoggerSettings:
    log_level = logging.DEBUG
    log_file = "debug.log"
    log_dir = os.path.join(IOSettings.wd, "logs")
