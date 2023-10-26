#! python3
from PyQt6.QtWidgets import QApplication
from settings import UISettings
from ui import UI

if __name__ == "__main__":
    app = QApplication([])
    settings = UISettings()
    ui = UI(settings)
    app.exec()

    exit()
