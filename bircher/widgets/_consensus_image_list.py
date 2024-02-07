from collections.abc import Iterable, MutableSequence
from dataclasses import dataclass
from typing import overload

from qtpy.QtCore import QAbstractItemModel, QModelIndex  # type: ignore

from ..models import Image


class ConsensusImageList(MutableSequence[Image]):
    @dataclass(frozen=True)
    class Consensus:
        dtype: str
        is_timeseries: bool
        is_zstack: bool
        n_channels: int
        dimension_order: str
        pixel_size_x_str: str | None
        pixel_size_y_str: str | None
        pixel_size_z_str: str | None
        channel_names: list[str]

    _DEFAULT_CONSENSUS = Consensus(
        dtype="uint16",
        is_timeseries=False,
        is_zstack=False,
        n_channels=1,
        dimension_order="TCZYX",
        pixel_size_x_str=None,
        pixel_size_y_str=None,
        pixel_size_z_str=None,
        channel_names=[],
    )

    def __init__(self, images: Iterable[Image] | None = None) -> None:
        super().__init__()
        self._model: QAbstractItemModel | None = None
        self._images: list[Image] = list(images) if images is not None else []
        self._consensus = self._DEFAULT_CONSENSUS
        self._update_consensus()

    @overload
    def __getitem__(self, key: int) -> Image:
        ...

    @overload
    def __getitem__(self, key: slice) -> "ConsensusImageList":
        ...

    def __getitem__(self, key):
        if isinstance(key, slice):
            raise NotImplementedError("Slicing not implemented")
        return self._images[key]

    @overload
    def __setitem__(self, key: int, value: Image) -> None:
        ...

    @overload
    def __setitem__(self, key: slice, value: Iterable[Image]) -> None:
        ...

    def __setitem__(self, key, value) -> None:
        if isinstance(key, slice):
            raise NotImplementedError("Slicing not implemented")
        self._images[key] = value
        if self._model is not None:
            self._model.dataChanged.emit(
                self._model.index(key, 0),
                self._model.index(key, self._model.columnCount() - 1),
            )
        self._update_consensus()

    @overload
    def __delitem__(self, key: int) -> None:
        ...

    @overload
    def __delitem__(self, key: slice) -> None:
        ...

    def __delitem__(self, key) -> None:
        if isinstance(key, slice):
            raise NotImplementedError("Slicing not implemented")
        if self._model is not None:
            self._model.beginRemoveRows(QModelIndex(), key, key)
        del self._images[key]
        if self._model is not None:
            self._model.endRemoveRows()
        self._update_consensus()

    def __len__(self) -> int:
        return len(self._images)

    def insert(self, index: int, value: Image) -> None:
        if self._model is not None:
            self._model.beginInsertRows(QModelIndex(), index, index)
        self._images.insert(index, value)
        if self._model is not None:
            self._model.endInsertRows()
        self._update_consensus()

    def set_model(self, model: QAbstractItemModel | None) -> None:
        self._model = model

    @property
    def consensus(self) -> "ConsensusImageList.Consensus":
        return self._consensus

    def _find_consensus(self, key):
        counts = {}
        for img in sorted(self._images, key=lambda img: img.posix_path):
            value = key(img)
            if isinstance(value, list):
                value = tuple(value)
            counts[value] = counts.get(value, 0) + 1
        if not counts:
            return None
        value = max(counts, key=lambda value: counts[value])
        if isinstance(value, tuple):
            return list(value)
        return value

    def _update_consensus(self) -> None:
        if self._images:
            new_consensus = ConsensusImageList.Consensus(
                dtype=self._find_consensus(lambda img: img.dtype),
                is_timeseries=self._find_consensus(lambda img: img.is_timeseries),
                is_zstack=self._find_consensus(lambda img: img.is_zstack),
                n_channels=self._find_consensus(lambda img: img.n_channels),
                dimension_order=self._find_consensus(lambda img: img.dimension_order),
                pixel_size_x_str=self._find_consensus(lambda img: img.pixel_size_x_str),
                pixel_size_y_str=self._find_consensus(lambda img: img.pixel_size_y_str),
                pixel_size_z_str=self._find_consensus(lambda img: img.pixel_size_z_str),
                channel_names=self._find_consensus(lambda img: img.channel_names),
            )
        else:
            new_consensus = self._DEFAULT_CONSENSUS
        if new_consensus != self._consensus:
            if self._model is not None:
                self._model.beginResetModel()
            self._consensus = new_consensus
            if self._model is not None:
                self._model.endResetModel()
