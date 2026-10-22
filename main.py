""" Run the steganography demonstration. """

from pathlib import Path
from stego.analysis import (
    calculate_psnr,
    generate_bit_plane_diff,
    generate_histogram,
    show_images
)
from stego.codec import embed_message, extract_message
from stego.file_io import read_bytes, read_image, write_image, write_payload


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

COVER_PATH = INPUT_DIR / "images" / "lena.png"
PAYLOAD_PATH = INPUT_DIR / "images" / "QR_code.png"

STEGO_PATH = OUTPUT_DIR / "encoded" / "stego_image.png"
DECODED_PATH = OUTPUT_DIR / "decoded" / "decoding_result"
HISTOGRAM_PATH = OUTPUT_DIR / "histograms" / "histogram.png"
BIT_PLANE_PREFIX = OUTPUT_DIR / "bit_planes" / "lena"


def main() -> None:
    cover = read_image(COVER_PATH)
    payload = read_bytes(PAYLOAD_PATH)

    stego = embed_message(cover, payload)
    write_image(stego, STEGO_PATH)

    decoded = extract_message(stego)
    decoded_path = write_payload(decoded, DECODED_PATH)

    print(f"Stego image: {STEGO_PATH}")
    print(f"Decoded payload: {decoded_path}")
    print(f"PSNR: {calculate_psnr(cover, stego):.2f} dB")

    fig_hist = generate_histogram(cover, stego, HISTOGRAM_PATH)
    fig_bplane = generate_bit_plane_diff(cover, stego, BIT_PLANE_PREFIX)

    # Show images
    show_images(cover, stego)

    # Show histogram
    fig_hist.show()

    # Show bitplanes
    if cover.ndim == 2:
        fig_bplane.show()

    elif cover.ndim == 3:
        for fig in fig_bplane:
            fig.show()

    else:
        raise ValueError("Image must be 2D or 3D.")


if __name__ == "__main__":
    main()
