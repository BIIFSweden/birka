# Birka

*The BioImage Archiver*

Birka is a tool for bioimage data validation and archival.


## Installation

**[Standalone installers](https://github.com/BIIFSweden/birka-installer/releases/latest/)** are available for Windows, Mac OS and Linux (x86-64 only).

On other (e.g., ARM64-based) platforms, Birka can be installed from [conda-forge](https://conda-forge.org) using [conda](https://github.com/conda-forge/miniforge):

    conda create -n birka -c conda-forge birka birka-menu pyside6

On conda-based installations, CZI and LIF file format support can be added using:

    conda activate birka
    python -m pip install aicspylibczi>=3.1.1 fsspec>=2022.8.0 readlif>=0.6.4

Finally, Birka can also be installed from [PyPI](https://pypi.org/project/birka/) using [pip](https://pip.pypa.io/en/stable/) (experts; not recommended):

    pip install birka[bioformats,czi,lif,pyside6]

Birka requires `Python>=3.10,<3.12` and PySide6/PyQt6 bindings for [qtpy](https://github.com/spyder-ide/qtpy).


## Usage

Please note that launching Birka can take some time.

To load an image, simply drag and drop the image file into Birka.

Images are validated against the consenus among all loaded images w.r.t.:
- Data type
- Time series (yes/no)
- Z-stack (yes/no)
- Number of channels
- Dimension order
- XYZ pixel size (6 decimal places)
- Channel names (order-sensitive)

Deviations from the consensus, as well as duplicated image file names/paths, are highlighted in red. For more fine-grained validation of image file names/paths, a [Python regular expression](https://docs.python.org/3/library/re.html) can be provided.

Loaded single-file images and their metadata (in CSV format) can be jointly archived into a single .tar.gz file. More complex (e.g., multi-file) images can be converted to OME-TIFF during archival. In both cases, the generated archive will be structured according to the information in the (editable) image file names/paths column.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Birka is implemented in [Python](https://www.python.org) and heavily relies on [qtpy](https://github.com/spyder-ide/qtpy) (with [PySide6](https://doc.qt.io/qtforpython-6/) or [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) bindings), [aicsimageio](https://allencellmodeling.github.io/aicsimageio/) and [constructor](https://github.com/conda/constructor). Much inspiration for this design has been drawn from the [napari](https://napari.org/stable/) project. Upon creating a release, the Python package is [automatically deployed](https://github.com/BIIFSweden/birka/actions/workflows/build-and-publish.yaml) to PyPI, triggering the creation of a pull request (PR) on [conda-forge/birka-feedstock](https://github.com/conda-forge/birka-feedstock). Once this PR has been merged and the updated package becomes available on conda-forge, updated installers can be [automatically built](https://github.com/BIIFSweden/birka-installer/actions/workflows/build-and-publish.yaml) by creating a matching release on [BIIFSweden/birka-installer](https://github.com/BIIFSweden/birka-installer).

## License

[GPL 3.0](https://choosealicense.com/licenses/gpl-3.0/)
