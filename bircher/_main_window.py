import re

from qtpy.QtWidgets import QLineEdit, QMainWindow, QVBoxLayout, QWidget

from .widgets import ConsensusImageList, ImageTableModel, ImageTableView


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()
        self._images = ConsensusImageList()
        self._image_table_model = ImageTableModel(self._images)
        self._images.set_model(self._image_table_model)
        self._image_table_view = ImageTableView(self._images)
        self._image_table_view.setModel(self._image_table_model)
        central_widget_layout.addWidget(self._image_table_view)
        self._regex_line_edit = QLineEdit()
        self._regex_line_edit.setPlaceholderText(
            "File name pattern (regular expression, optional)"
        )
        self._regex_line_edit.textChanged.connect(self._on_regex_line_edit_text_changed)
        central_widget_layout.addWidget(self._regex_line_edit)
        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("bircher")

    def _on_regex_line_edit_text_changed(self, text: str) -> None:
        if text:
            try:
                file_name_pattern = re.compile(text)
                self._regex_line_edit.setStyleSheet("background-color: white")
            except re.error:
                file_name_pattern = None
                self._regex_line_edit.setStyleSheet("background-color: red")
        else:
            file_name_pattern = None
            self._regex_line_edit.setStyleSheet("background-color: white")
        self._image_table_model.set_file_name_pattern(file_name_pattern)

    @property
    def image_table_model(self) -> ImageTableModel:
        return self._image_table_model
