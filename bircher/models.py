from dataclasses import dataclass


@dataclass(frozen=True)
class Image:
    file: str
    dtype: str
    n_scenes: int
    n_timepoints: int
    n_channels: int
    size_z_px: int
    size_y_px: int
    size_x_px: int
    dimension_order: str
    pixel_size_x: float | None
    pixel_size_y: float | None
    pixel_size_z: float | None
    channel_names: list[str]

    @property
    def is_timeseries(self) -> bool:
        return self.n_timepoints > 1

    @property
    def is_zstack(self) -> bool:
        return self.size_z_px > 1
