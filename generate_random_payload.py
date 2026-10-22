from pathlib import Path
from stego.codec import _embedding_capacity, END_MARKER
from stego.file_io import read_image
import os


INPUT_DIR = Path("data/input")
RANDOM_BYTES_DIR = INPUT_DIR / "random_bytes"


def generate_random_payload(image_path: Path, output_dir: Path) -> Path:
    """
    Generate a random payload file with the maximum size that can be embedded
    into the given image and save it to the specified directory.
    """
    # Read the cover image
    cover_image = read_image(image_path)

    # Calculate the maximum embedding capacity in bits
    max_capacity_bits = _embedding_capacity(cover_image)

    # Subtract the bits required for the END_MARKER
    end_marker_bits = len(END_MARKER) * 8
    max_payload_bits = max_capacity_bits - end_marker_bits

    # Convert to bytes
    max_payload_bytes = max_payload_bits // 8

    # Generate random bytes
    random_bytes = os.urandom(max_payload_bytes)

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the random bytes to a file
    random_file_path = output_dir / f"random_bytes_{image_path.stem}.bin"
    random_file_path.write_bytes(random_bytes)

    print(f"Random payload file created: {random_file_path}")
    return random_file_path


if __name__ == "__main__":
    cover_image_path = INPUT_DIR / "images" / "lena.png"
    generate_random_payload(cover_image_path, RANDOM_BYTES_DIR)
