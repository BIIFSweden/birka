from collections.abc import Iterable, MutableSequence
from typing import overload

from qtpy.QtCore import QAbstractItemModel, QModelIndex  # type: ignore

from ..models import Image


class ImageList(MutableSequence[Image]):
    def __init__(self, images: Iterable[Image] | None = None) -> None:
        super().__init__()
        self._model: QAbstractItemModel | None = None
        self._images: list[Image] = list(images) if images is not None else []

    @overload
    def __getitem__(self, key: int) -> Image:
        ...

    @overload
    def __getitem__(self, key: slice) -> "ImageList":
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

    def __len__(self) -> int:
        return len(self._images)

    def insert(self, index: int, value: Image) -> None:
        if self._model is not None:
            self._model.beginInsertRows(QModelIndex(), index, index)
        self._images.insert(index, value)
        if self._model is not None:
            self._model.endInsertRows()

    def set_model(self, model: QAbstractItemModel | None) -> None:
        self._model = model
