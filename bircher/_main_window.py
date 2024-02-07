import re
from collections.abc import Sequence
from pathlib import Path

from qtpy.QtCore import QObject, QSortFilterProxyModel, Qt, QThread, Signal
from qtpy.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .models import Image
from .utils import write_archive
from .widgets import ConsensusImageList, ImageTableModel, ImageTableView


class MainWindow(QMainWindow):
    class ArchiveWriterThread(QThread):
        step = Signal(int, Image)
        completed = Signal()
        error = Signal(Exception)

        def __init__(
            self,
            archive_file: str | Path,
            images: Sequence[Image],
            ome_tiff: bool = False,
            compresslevel: int = 5,
            parent: QObject | None = None,
        ) -> None:
            super().__init__(parent)
            self._archive_file = archive_file
            self._images = images
            self._ome_tiff = ome_tiff
            self._compresslevel = compresslevel

        def run(self) -> None:
            try:
                archive_writer = write_archive(
                    self._archive_file,
                    self._images,
                    ome_tiff=self._ome_tiff,
                    compresslevel=self._compresslevel,
                )
                for i, img in enumerate(archive_writer):
                    self.step.emit(i, img)
                self.completed.emit()
            except Exception as e:
                self.error.emit(e)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._archive_writer_thread: MainWindow.ArchiveWriterThread | None = None
        central_widget = QWidget()
        central_widget_layout = QVBoxLayout()
        edit_widget = QWidget()
        edit_widget_layout = QHBoxLayout()
        self._regex_line_edit = QLineEdit()
        self._regex_line_edit.setPlaceholderText(
            "POSIX file path pattern (Python regular expression, optional)"
        )
        self._regex_line_edit.textChanged.connect(self._on_regex_line_edit_text_changed)
        edit_widget_layout.addWidget(self._regex_line_edit)
        edit_widget_layout.addStretch()
        self._remove_selected_rows_button = QPushButton("Remove selected rows")
        self._remove_selected_rows_button.clicked.connect(
            self._on_remove_selected_rows_button_clicked
        )
        edit_widget_layout.addWidget(self._remove_selected_rows_button)
        edit_widget.setLayout(edit_widget_layout)
        central_widget_layout.addWidget(edit_widget)
        self._images = ConsensusImageList()
        self._image_table_model = ImageTableModel(self._images)
        self._image_table_model.modelReset.connect(lambda: self._update_button_states())
        self._image_table_model.dataChanged.connect(
            lambda top_left, bottom_right: self._update_button_states()
        )
        self._images.set_model(self._image_table_model)
        self._image_table_view = ImageTableView(self._images)
        sorted_image_table_model = QSortFilterProxyModel()
        sorted_image_table_model.setSourceModel(self._image_table_model)
        self._image_table_view.setModel(sorted_image_table_model)
        self._image_table_view.selectionModel().selectionChanged.connect(
            lambda selected, deselected: self._update_button_states()
        )
        central_widget_layout.addWidget(self._image_table_view)
        actions_widget = QWidget()
        actions_widget_layout = QHBoxLayout()
        actions_widget_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._compresslevel_label = QLabel("Compression level (1=fastest, 9=smallest):")
        actions_widget_layout.addWidget(self._compresslevel_label)
        self._compresslevel_spin_box = QSpinBox()
        self._compresslevel_spin_box.setRange(1, 9)
        self._compresslevel_spin_box.setValue(5)
        actions_widget_layout.addWidget(self._compresslevel_spin_box)
        actions_widget_layout.addStretch()
        self._convert_and_archive_button = QPushButton("Convert to OME-TIFF && archive")
        self._convert_and_archive_button.clicked.connect(
            self._on_convert_and_archive_button_clicked
        )
        actions_widget_layout.addWidget(self._convert_and_archive_button)
        self._archive_only_button = QPushButton("Archive only")
        self._archive_only_button.clicked.connect(self._on_archive_only_button_clicked)
        actions_widget_layout.addWidget(self._archive_only_button)
        actions_widget.setLayout(actions_widget_layout)
        central_widget_layout.addWidget(actions_widget)
        central_widget.setLayout(central_widget_layout)
        self.setCentralWidget(central_widget)
        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready")
        self._progress_bar = QProgressBar()
        self._progress_bar.setHidden(True)
        self._status_bar.addPermanentWidget(self._progress_bar)
        self.setStatusBar(self._status_bar)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("bircher")
        self._update_button_states()

    def _on_regex_line_edit_text_changed(self, text: str) -> None:
        if text:
            try:
                posix_path_pattern = re.compile(text)
                self._regex_line_edit.setStyleSheet("background-color: white")
            except re.error:
                posix_path_pattern = None
                self._regex_line_edit.setStyleSheet("background-color: red")
        else:
            posix_path_pattern = None
            self._regex_line_edit.setStyleSheet("background-color: white")
        self._image_table_model.set_posix_path_pattern(posix_path_pattern)

    def _on_remove_selected_rows_button_clicked(self) -> None:
        for index in sorted(
            self._image_table_view.selectionModel().selectedRows(),
            key=lambda index: index.row(),
            reverse=True,
        ):
            self._images.pop(index.row())

    def _on_convert_and_archive_button_clicked(self) -> None:
        self._create_archive(ome_tiff=True)

    def _on_archive_only_button_clicked(self) -> None:
        self._create_archive()

    def _create_archive(self, ome_tiff: bool = False) -> None:
        archive_file, selected_filter = QFileDialog.getSaveFileName(
            parent=self,
            dir=str(Path.home() / "Untitled"),
            filter="Image archive (*.tar.gz)",
            selectedFilter="Image archive (*.tar.gz)",
        )
        if archive_file:
            self._archive_writer_thread = MainWindow.ArchiveWriterThread(
                archive_file,
                self._images,
                ome_tiff=ome_tiff,
                compresslevel=self._compresslevel_spin_box.value(),
            )
            self._update_button_states()

            @self._archive_writer_thread.step.connect
            def on_archive_writer_thread_step(i, img):
                self._progress_bar.setValue(i + 1)

            @self._archive_writer_thread.completed.connect
            def on_archive_writer_thread_completed():
                self._status_bar.showMessage("Images archived")
                self._progress_bar.setHidden(True)
                self._archive_writer_thread = None
                self._update_button_states()

            @self._archive_writer_thread.error.connect
            def on_archive_writer_thread_error(e):
                self._status_bar.showMessage(f"Error: {e}")
                self._progress_bar.setHidden(True)
                self._archive_writer_thread = None
                self._update_button_states()

            self._status_bar.showMessage("Archiving images...")
            self._progress_bar.setMaximum(len(self._images))
            self._progress_bar.setHidden(False)
            self._progress_bar.setValue(0)
            self._archive_writer_thread.start()

    def _update_button_states(self) -> None:
        self._remove_selected_rows_button.setEnabled(
            self._archive_writer_thread is None
            and self._image_table_view.selectionModel().hasSelection()
        )
        self._convert_and_archive_button.setEnabled(
            self._archive_writer_thread is None
            and len(self._images) > 0
            and len(set(img.posix_path for img in self._images)) == len(self._images)
        )
        self._archive_only_button.setEnabled(
            self._archive_writer_thread is None
            and len(self._images) > 0
            and len(set(img.posix_path for img in self._images)) == len(self._images)
        )
