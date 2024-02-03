from collections.abc import Iterable, MutableSequence
from dataclasses import dataclass
from typing import overload

from qtpy.QtCore import QAbstractItemModel, QModelIndex  # type: ignore

from ..models import Image


class ConsensusImageList(MutableSequence[Image]):
    @dataclass(frozen=True)
    class Consensus:
        n_timepoints: int
        n_channels: int
        is_3D: bool
        dtype: str
        dimension_order: str
        channel_names: list[str]
        pixel_size_x: float | None
        pixel_size_y: float | None
        pixel_size_z: float | None

    _DEFAULT_CONSENSUS = Consensus(
        n_timepoints=1,
        n_channels=1,
        is_3D=False,
        dtype="uint16",
        dimension_order="TCZYX",
        channel_names=[],
        pixel_size_x=None,
        pixel_size_y=None,
        pixel_size_z=None,
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
        for img in sorted(self._images, key=lambda img: img.file):
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
                n_timepoints=self._find_consensus(lambda img: img.n_timepoints),
                n_channels=self._find_consensus(lambda img: img.n_channels),
                is_3D=self._find_consensus(lambda img: img.size_z_px > 1),
                dtype=self._find_consensus(lambda img: img.dtype),
                dimension_order=self._find_consensus(lambda img: img.dimension_order),
                channel_names=self._find_consensus(lambda img: img.channel_names),
                pixel_size_x=self._find_consensus(lambda img: img.pixel_size_x),
                pixel_size_y=self._find_consensus(lambda img: img.pixel_size_y),
                pixel_size_z=self._find_consensus(lambda img: img.pixel_size_z),
            )
        else:
            new_consensus = self._DEFAULT_CONSENSUS
        if new_consensus != self._consensus:
            if self._model is not None:
                self._model.beginResetModel()
            self._consensus = new_consensus
            if self._model is not None:
                self._model.endResetModel()
