import tarfile
from collections.abc import Generator, Sequence
from io import BytesIO
from pathlib import Path
from tarfile import TarInfo
from tempfile import TemporaryDirectory

import pandas as pd
from aicsimageio import AICSImage
from aicsimageio.exceptions import UnsupportedFileFormatError

from .models import Image


def load_images(path: str | Path, _base_path: Path | None = None) -> Sequence[Image]:
    images = []
    path = Path(path)
    if _base_path is None:
        _base_path = path.parent
        assert _base_path.is_dir()
    try:
        aics_img = AICSImage(path)
        img = Image(
            orig_path=str(path),
            posix_path=str(path.relative_to(_base_path).as_posix()),
            n_scenes=len(aics_img.scenes),
            n_timepoints=aics_img.dims.T if "T" in aics_img.dims.order else 1,
            n_channels=aics_img.dims.C if "C" in aics_img.dims.order else 1,
            size_z_px=aics_img.dims.Z if "Z" in aics_img.dims.order else 1,
            size_y_px=aics_img.dims.Y if "Y" in aics_img.dims.order else 1,
            size_x_px=aics_img.dims.X if "X" in aics_img.dims.order else 1,
            dtype=aics_img.dtype.name,
            dimension_order=aics_img.dims.order,
            channel_names=list(aics_img.channel_names),
            pixel_size_x=aics_img.physical_pixel_sizes[-1],
            pixel_size_y=aics_img.physical_pixel_sizes[-2],
            pixel_size_z=aics_img.physical_pixel_sizes[-3],
        )
        images.append(img)
    except UnsupportedFileFormatError:
        if path.is_dir():
            for subpath in sorted(path.iterdir()):
                images += load_images(subpath, _base_path=_base_path)
    return images


def can_load_images(path: str | Path) -> bool:
    path = Path(path)
    if path.is_dir():
        return True
    try:
        AICSImage.determine_reader(path)
    except UnsupportedFileFormatError:
        return False
    return True


def write_archive(
    archive_file: str | Path,
    images: Sequence[Image],
    ome_tiff: bool = False,
    compresslevel: int = 5,
) -> Generator[Image, None, None]:
    with tarfile.open(
        archive_file, mode="w:gz", compresslevel=compresslevel
    ) as tar_file:
        for img in images:
            if ome_tiff:
                aics_img = AICSImage(img.orig_path)
                with TemporaryDirectory() as temp_dir:
                    img_file = Path(temp_dir) / f"{Path(img.orig_path).stem}.tiff"
                    posix_path = str(Path(img.posix_path).with_suffix(".tiff"))
                    aics_img.save(img_file)
                    tar_file.add(img_file, arcname=posix_path)
            else:
                tar_file.add(img.orig_path, arcname=img.posix_path)
            yield img
        df = pd.DataFrame(
            data=[
                {
                    "image": (
                        img.posix_path
                        if not ome_tiff
                        else str(Path(img.posix_path).with_suffix(".tiff"))
                    ),
                    "dtype": img.dtype,
                    "n_scenes": img.n_scenes,
                    "n_timepoints": img.n_timepoints,
                    "n_channels": img.n_channels,
                    "size_z_px": img.size_z_px,
                    "size_y_px": img.size_y_px,
                    "size_x_px": img.size_x_px,
                    "dimension_order": img.dimension_order,
                    "pixel_size_x": img.pixel_size_x,
                    "pixel_size_y": img.pixel_size_y,
                    "pixel_size_z": img.pixel_size_z,
                    "channel_names": ",".join(img.channel_names),
                }
                for img in images
            ]
        )
        data = df.to_csv(index=False).encode()
        with BytesIO(data) as buf:
            tar_info = TarInfo(name="images.csv")
            tar_info.size = len(data)
            tar_file.addfile(tar_info, fileobj=buf)
