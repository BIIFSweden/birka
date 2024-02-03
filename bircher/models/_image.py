from pydantic import BaseModel


class Image(BaseModel):
    file: str
    scenes: list[str]
    n_timepoints: int
    n_channels: int
    size_z_px: int
    size_y_px: int
    size_x_px: int
    dtype: str
    dimension_order: str
    channel_names: list[str]
    pixel_size_x: float | None
    pixel_size_y: float | None
    pixel_size_z: float | None
