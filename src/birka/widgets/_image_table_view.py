import logging
from pathlib import Path

from qtpy.QtCore import QMimeData, Qt  # type: ignore
from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from qtpy.QtWidgets import QTableView, QWidget

from ..utils import can_load_images, load_images
from ._consensus_image_list import ConsensusImageList

log = logging.getLogger(__name__)


class ImageTableView(QTableView):
    def __init__(
        self, images: ConsensusImageList, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._images = images
        self.setAcceptDrops(True)
        self.setSortingEnabled(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._check_mime_data(event.mimeData()):
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if event.dropAction() == Qt.DropAction.CopyAction and self._check_mime_data(
            event.mimeData()
        ):
            event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        if event.dropAction() == Qt.DropAction.CopyAction and self._check_mime_data(
            event.mimeData(), check_files=True
        ):
            for url in event.mimeData().urls():
                img_file_or_dir = Path(url.toLocalFile())
                try:
                    self._images += load_images(img_file_or_dir)
                except Exception as e:
                    log.error(f"Failed to load image(s) from {img_file_or_dir}: {e}")
            event.accept()

    def _check_mime_data(self, mime_data: QMimeData, check_files: bool = False) -> bool:
        if not mime_data.hasUrls() or any(
            not url.isLocalFile() for url in mime_data.urls()
        ):
            return False
        if check_files and (
            any(not Path(url.toLocalFile()).exists() for url in mime_data.urls())
            or any(not can_load_images(url.toLocalFile()) for url in mime_data.urls())
        ):
            return False
        return True
