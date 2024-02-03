import re

from qtpy.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .widgets import ConsensusImageList, ImageTableModel, ImageTableView


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()
        self._images = ConsensusImageList()
        self._image_table_model = ImageTableModel(self._images)
        self._image_table_model.modelReset.connect(
            lambda: self._update_delete_push_button_state()
        )
        self._images.set_model(self._image_table_model)
        self._image_table_view = ImageTableView(self._images)
        self._image_table_view.setModel(self._image_table_model)
        self._image_table_view.selectionModel().selectionChanged.connect(
            lambda selected, deselected: self._update_delete_push_button_state()
        )
        central_widget_layout.addWidget(self._image_table_view)
        regex_delete_widget = QWidget()
        regex_delete_widget_layout = QHBoxLayout()
        self._regex_line_edit = QLineEdit()
        self._regex_line_edit.setPlaceholderText(
            "File name pattern (regular expression, optional)"
        )
        self._regex_line_edit.textChanged.connect(self._on_regex_line_edit_text_changed)
        regex_delete_widget_layout.addWidget(self._regex_line_edit)
        regex_delete_widget_layout.addStretch()
        self._delete_push_button = QPushButton("Delete selected rows")
        self._delete_push_button.setEnabled(False)
        self._delete_push_button.clicked.connect(self._on_delete_push_button_clicked)
        regex_delete_widget_layout.addWidget(self._delete_push_button)
        regex_delete_widget.setLayout(regex_delete_widget_layout)
        central_widget_layout.addWidget(regex_delete_widget)
        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("bircher")

    def _update_delete_push_button_state(self) -> None:
        self._delete_push_button.setEnabled(
            self._image_table_view.selectionModel().hasSelection()
        )

    def _on_delete_push_button_clicked(self) -> None:
        for index in sorted(
            self._image_table_view.selectionModel().selectedRows(),
            key=lambda index: index.row(),
            reverse=True,
        ):
            self._image_table_model.removeRow(index.row())

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
