"""
Helper function that generates random data to use as a hidden message.
The payload is intended to fill as much of the image's embedding capacity
as possible, allowing us to visualize "fully covered" bit planes and
analyze the effects of embedding a maximum-size message.
"""

from pathlib import Path
import os
import numpy as np

from stego.codec import (
    END_MARKER,
    _iter_blocks,
    _capacity_bits,
    _embedding_offset,
    _apply_modification,
)
from stego.file_io import read_image


INPUT_DIR = Path("data/input")
RANDOM_BYTES_DIR = INPUT_DIR / "random_bytes"


def generate_random_payload(image_path: Path, output_dir: Path) -> Path:
    """Generate a random payload that approximately fills the image capacity."""

    cover = read_image(image_path)

    # Generate more random data than the image can hold.
    random_bytes = os.urandom(cover.size)
    bits = "".join(f"{byte:08b}" for byte in random_bytes)

    # Simulate embedding on a copy of the image.
    simulated = cover.astype(np.int16, copy=True)
    bit_index = 0

    for center, neighborhood in _iter_blocks(simulated):
        if bit_index >= len(bits):
            break

        n_bits = _capacity_bits(neighborhood)
        chunk = bits[bit_index:bit_index + n_bits].ljust(n_bits, "0")
        payload_value = int(chunk, 2)

        current_value = int(simulated[center])
        offset = _embedding_offset(current_value, payload_value, n_bits)
        simulated[center] = _apply_modification(
            current_value, offset, n_bits
        )

        bit_index += n_bits

    # Reserve space for the end marker and keep only complete bytes.
    marker_bits = len(END_MARKER.encode("utf-8")) * 8
    payload_size = max(0, (bit_index - marker_bits) // 8)
    payload = random_bytes[:payload_size]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"random_bytes_{image_path.stem}.bin"
    output_path.write_bytes(payload)

    print(f"Payload size: {len(payload)} bytes")
    print(f"Payload file created: {output_path}")

    return output_path


if __name__ == "__main__":
    cover_image_path = INPUT_DIR / "images" / "lena.png"
    generate_random_payload(cover_image_path, RANDOM_BYTES_DIR)
