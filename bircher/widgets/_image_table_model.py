from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from re import Pattern
from typing import Any

from qtpy.QtCore import (  # type: ignore
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)
from qtpy.QtGui import QColor

from ..models import Image
from ._consensus_image_list import ConsensusImageList


class ImageTableModel(QAbstractTableModel):
    VALID_COLOR = Qt.GlobalColor.white
    INVALID_COLOR = Qt.GlobalColor.red

    @dataclass(frozen=True)
    class Column:
        header: str | None = None
        selector: Callable[[Image], Any] | None = None
        validator: Callable[[Image], bool] | None = None

    def __init__(
        self, images: ConsensusImageList, parent: QObject | None = None
    ) -> None:
        super().__init__(parent)
        self._images = images
        self._file_name_pattern: Pattern[str] | None = None
        self._columns: list[ImageTableModel.Column] = [
            ImageTableModel.Column(
                header="File",
                selector=lambda img: Path(img.file).name,
                validator=(
                    lambda img: (
                        len([x for x in images if x.file == img.file]) == 1
                        and (
                            bool(self._file_name_pattern.fullmatch(Path(img.file).name))
                            if self._file_name_pattern is not None
                            else True
                        )
                    )
                ),
            ),
            ImageTableModel.Column(
                header="Data type",
                selector=lambda img: img.dtype,
                validator=lambda img: img.dtype == images.consensus.dtype,
            ),
            ImageTableModel.Column(
                header="Scenes",
                selector=lambda img: img.n_scenes,
            ),
            ImageTableModel.Column(
                header="Timepoints",
                selector=lambda img: img.n_timepoints,
                validator=lambda img: (
                    img.is_timeseries == images.consensus.is_timeseries
                ),
            ),
            ImageTableModel.Column(
                header="Channels",
                selector=lambda img: img.n_channels,
                validator=lambda img: img.n_channels == images.consensus.n_channels,
            ),
            ImageTableModel.Column(
                header="Width [px]",
                selector=lambda img: img.size_x_px,
            ),
            ImageTableModel.Column(
                header="Height [px]",
                selector=lambda img: img.size_y_px,
            ),
            ImageTableModel.Column(
                header="Depth [px]",
                selector=lambda img: img.size_z_px,
                validator=lambda img: img.is_zstack == images.consensus.is_zstack,
            ),
            ImageTableModel.Column(
                header="Dimension order",
                selector=lambda img: img.dimension_order,
                validator=lambda img: (
                    img.dimension_order == images.consensus.dimension_order
                ),
            ),
            ImageTableModel.Column(
                header="Pixel size (X)",
                selector=lambda img: img.pixel_size_x or "unknown",
                validator=lambda img: img.pixel_size_x == images.consensus.pixel_size_x,
            ),
            ImageTableModel.Column(
                header="Pixel size (Y)",
                selector=lambda img: img.pixel_size_y or "unknown",
                validator=lambda img: img.pixel_size_y == images.consensus.pixel_size_y,
            ),
            ImageTableModel.Column(
                header="Pixel size (Z)",
                selector=lambda img: img.pixel_size_z or "unknown",
                validator=lambda img: img.pixel_size_z == images.consensus.pixel_size_z,
            ),
            ImageTableModel.Column(
                header="Channel names",
                selector=lambda img: ", ".join(img.channel_names),
                validator=(
                    lambda img: tuple(img.channel_names)
                    == tuple(images.consensus.channel_names)
                ),
            ),
        ]

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        assert parent is None or not parent.isValid()
        return len(self._images)

    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        assert parent is None or not parent.isValid()
        return len(self._columns)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            index.isValid()
            and 0 <= index.row() < len(self._images)
            and 0 <= index.column() < len(self._columns)
        ):
            image = self._images[index.row()]
            column = self._columns[index.column()]
            if role == Qt.ItemDataRole.DisplayRole and column.selector is not None:
                return column.selector(image)
            if role == Qt.ItemDataRole.BackgroundRole and column.validator is not None:
                return (
                    QColor(self.VALID_COLOR)
                    if column.validator(image)
                    else QColor(self.INVALID_COLOR)
                )
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            0 <= section < len(self._columns)
            and orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._columns[section].header
        return None

    def set_file_name_pattern(self, pattern: Pattern[str] | None) -> None:
        self._file_name_pattern = pattern
        col = next(i for i, c in enumerate(self._columns) if c.header == "File")
        self.dataChanged.emit(self.index(0, col), self.index(self.rowCount() - 1, col))
