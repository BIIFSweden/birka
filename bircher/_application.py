from qtpy.QtWidgets import QApplication

from ._main_window import MainWindow


class Application(QApplication):
    def run(self):
        window = MainWindow()
        window.show()
        self.exec()
