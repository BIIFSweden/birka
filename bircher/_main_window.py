from qtpy.QtWidgets import QMainWindow, QWidget

from .widgets import ConsensusImageList, ImageTableModel, ImageTableView


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Bircher")
        self._images = ConsensusImageList()
        self._image_table_model = ImageTableModel(self._images)
        self._images.set_model(self._image_table_model)
        self._image_table_view = ImageTableView(self._images)
        self._image_table_view.setModel(self._image_table_model)
        self.setCentralWidget(self._image_table_view)

    @property
    def image_table_model(self) -> ImageTableModel:
        return self._image_table_model
