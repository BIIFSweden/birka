from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qtpy.QtCore import (  # type: ignore
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)

from ..models import Image


class ImageTableModel(QAbstractTableModel):
    @dataclass
    class Column:
        name: str
        getter: Callable[[Image], Any]

    _COLUMNS: list[Column] = [
        Column("File", lambda image: Path(image.file).name),
        Column("Data type", lambda image: image.dtype),
        Column("Scenes", lambda image: len(image.scenes)),
        Column("Timepoints", lambda image: image.n_timepoints),
        Column("Channels", lambda image: image.n_channels),
        Column("Width [px]", lambda image: image.size_x_px),
        Column("Height [px]", lambda image: image.size_y_px),
        Column("Depth [px]", lambda image: image.size_z_px),
        Column("Dimension order", lambda image: image.dimension_order),
        Column("Pixel size (X)", lambda image: image.pixel_size_x or "unknown"),
        Column("Pixel size (Y)", lambda image: image.pixel_size_y or "unknown"),
        Column("Pixel size (Z)", lambda image: image.pixel_size_z or "unknown"),
        Column("Channel names", lambda image: ", ".join(image.channel_names)),
    ]

    def __init__(self, images: Sequence[Image], parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._images: Sequence[Image] = images

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        assert parent is None or not parent.isValid()
        return len(self._images)

    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex | None = None
    ) -> int:
        assert parent is None or not parent.isValid()
        return len(self._COLUMNS)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            index.isValid()
            and 0 <= index.row() < len(self._images)
            and 0 <= index.column() < len(self._COLUMNS)
            and role == Qt.ItemDataRole.DisplayRole
        ):
            image = self._images[index.row()]
            return self._COLUMNS[index.column()].getter(image)
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if (
            0 <= section < len(self._COLUMNS)
            and orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._COLUMNS[section].name
        return None
