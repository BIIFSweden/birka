import tarfile
from collections.abc import Generator, Sequence
from io import BytesIO
from pathlib import Path
from tarfile import TarInfo

import pandas as pd
from aicsimageio import AICSImage
from aicsimageio.exceptions import UnsupportedFileFormatError

from .models import Image


def load_image(img_file: str | Path) -> Image:
    aics_img = AICSImage(img_file)
    return Image(
        file=str(Path(img_file).resolve()),
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


def can_load_image(img_file: str | Path) -> bool:
    try:
        AICSImage.determine_reader(img_file)
    except UnsupportedFileFormatError:
        return False
    return True


def write_archive(
    archive_file: str | Path, images: Sequence[Image]
) -> Generator[Image, None, None]:
    with tarfile.open(archive_file, mode="w:gz") as tar_file:
        for img in images:
            tar_file.add(img.file, arcname=Path(img.file).name)
            yield img
        df = pd.DataFrame(
            data=[
                {
                    "file": Path(img.file).name,
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
        with BytesIO(data) as f:
            tar_info = TarInfo(name="images.csv")
            tar_info.size = len(data)
            tar_file.addfile(tar_info, fileobj=f)
