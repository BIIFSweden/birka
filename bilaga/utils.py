from pathlib import Path

from aicsimageio import AICSImage
from aicsimageio.exceptions import UnsupportedFileFormatError

from .models import Image


def load_image(img_file: str | Path) -> Image:
    aics_img = AICSImage(img_file)
    return Image(
        filename=Path(img_file).name,
        scenes=list(aics_img.scenes),
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
