from collections.abc import Callable
from dataclasses import dataclass
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
        self._posix_path_pattern: Pattern[str] | None = None
        self._posix_path_column = ImageTableModel.Column(
            header="Image",
            selector=lambda img: img.posix_path,
            validator=lambda img: (
                (
                    bool(self._posix_path_pattern.fullmatch(img.posix_path))
                    if self._posix_path_pattern is not None
                    else True
                )
                and not any(
                    other_img.posix_path == img.posix_path
                    for other_img in images
                    if other_img is not img
                )
            ),
        )
        self._columns = [
            self._posix_path_column,
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
                selector=lambda img: img.pixel_size_x_str or "unknown",
                validator=lambda img: (
                    img.pixel_size_x_str == images.consensus.pixel_size_x_str
                ),
            ),
            ImageTableModel.Column(
                header="Pixel size (Y)",
                selector=lambda img: img.pixel_size_y_str or "unknown",
                validator=lambda img: (
                    img.pixel_size_y_str == images.consensus.pixel_size_y_str
                ),
            ),
            ImageTableModel.Column(
                header="Pixel size (Z)",
                selector=lambda img: img.pixel_size_z_str or "unknown",
                validator=lambda img: (
                    img.pixel_size_z_str == images.consensus.pixel_size_z_str
                ),
            ),
            ImageTableModel.Column(
                header="Channel names",
                selector=lambda img: ", ".join(img.channel_names),
                validator=lambda img: (
                    tuple(img.channel_names) == tuple(images.consensus.channel_names)
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
            img = self._images[index.row()]
            col = self._columns[index.column()]
            if role == Qt.ItemDataRole.DisplayRole and col.selector is not None:
                return col.selector(img)
            if role == Qt.ItemDataRole.BackgroundRole and col.validator is not None:
                return (
                    QColor(Qt.GlobalColor.white)
                    if col.validator(img)
                    else QColor(Qt.GlobalColor.red)
                )
            if (
                role == Qt.ItemDataRole.EditRole
                and index.column() == self._columns.index(self._posix_path_column)
            ):
                return img.posix_path
        return None

    def setData(
        self,
        index: QModelIndex | QPersistentModelIndex,
        value: Any,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
        if (
            index.isValid()
            and 0 <= index.row() < len(self._images)
            and index.column() == self._columns.index(self._posix_path_column)
            and role == Qt.ItemDataRole.EditRole
        ):
            img = self._images[index.row()]
            img.posix_path = str(value)
            self.dataChanged.emit(index, index)
            return True
        return super().setData(index, value, role)

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

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if index.isValid() and index.column() == self._columns.index(
            self._posix_path_column
        ):
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def set_posix_path_pattern(self, pattern: Pattern[str] | None) -> None:
        self._posix_path_pattern = pattern
        posix_path_col = self._columns.index(self._posix_path_column)
        self.dataChanged.emit(
            self.index(0, posix_path_col),
            self.index(self.rowCount() - 1, posix_path_col),
        )
