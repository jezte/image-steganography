""" Image and payload file handling. """

from pathlib import Path
import filetype
from skimage import io


def read_image(path: str | Path):
    """ Read an image from disk. """
    return io.imread(path)


def write_image(image, path: str | Path) -> Path:
    """ Write an image to disk and return its path. """
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    io.imsave(output_path, image)
    return output_path


def read_bytes(path: str | Path) -> bytes:
    """Read any file as raw bytes."""
    with open(path, "rb") as f:
        return f.read()


def write_payload(data: bytes, output_path: str | Path) -> Path:
    """ Write extracted payload, appending its detected extension when possible. """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    detected_type = filetype.guess(data)
    if detected_type is not None and output.suffix == "":
        output = output.with_suffix(f".{detected_type.extension}")

    output.write_bytes(data)
    return output
