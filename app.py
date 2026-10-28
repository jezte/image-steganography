from pathlib import Path
import streamlit as st

from stego.analysis import (
    calculate_psnr,
    generate_bit_plane_diff,
    generate_histogram,
)
from stego.codec import embed_message, extract_message
from stego.file_io import read_bytes, read_image, write_image, write_payload

# Define output paths
OUTPUT_DIR = Path("data/output")
INPUT_DIR = Path("data/input")

UPLOADED_PATH = INPUT_DIR / "uploaded"

STEGO_PATH = OUTPUT_DIR / "encoded" / "stego_image.png"
DECODED_PATH = OUTPUT_DIR / "decoded" / "decoding_result"
HISTOGRAM_PATH = OUTPUT_DIR / "histograms" / "histogram.png"
BIT_PLANE_PREFIX = OUTPUT_DIR / "bit_planes" / "bit_plane"


# Create directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOADED_PATH.mkdir(parents=True, exist_ok=True)
STEGO_PATH.parent.mkdir(parents=True, exist_ok=True)
DECODED_PATH.parent.mkdir(parents=True, exist_ok=True)
HISTOGRAM_PATH.parent.mkdir(parents=True, exist_ok=True)
BIT_PLANE_PREFIX.parent.mkdir(parents=True, exist_ok=True)


st.title("Image Steganography Tool")

# User selects mode: Encpde or Decode
mode = st.radio("Choose Mode", ["Encode", "Decode"])


# ============================================================
# ENCODE
# ============================================================

if mode == "Encode":
    st.header("Step 1: Upload Cover Image")

    cover_file = st.file_uploader(
        "Choose a cover image",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        key="cover_uploader",
    )

    st.header("Step 2: Upload Payload File")

    payload_file = st.file_uploader(
        "Choose a payload file",
        type=None,
        key="payload_uploader",
    )

    encode_button_disabled = not (cover_file and payload_file)

    if st.button("Embed Message", disabled=encode_button_disabled):
        # Clear previous encoding results before generating new ones
        for key in (
            "cover",
            "stego",
            "stego_image",
            "stego_filename",
            "psnr",
        ):
            st.session_state.pop(key, None)

        try:
            with st.spinner("Reading input files..."):
                cover_extension = Path(cover_file.name).suffix
                cover_path = UPLOADED_PATH / f"uploaded_cover{cover_extension}"
                cover_path.write_bytes(cover_file.getvalue())

                payload_extension = Path(payload_file.name).suffix
                payload_path = UPLOADED_PATH / f"uploaded_payload{payload_extension}"
                payload_path.write_bytes(payload_file.getvalue())

                cover = read_image(cover_path)
                payload = read_bytes(payload_path)

            with st.spinner("Embedding message into the cover image..."):
                stego = embed_message(cover, payload)
                write_image(stego, STEGO_PATH)

            with st.spinner("Calculating PSNR..."):
                psnr = calculate_psnr(cover, stego)

            with st.spinner("Generating histogram..."):
                generate_histogram(cover, stego, HISTOGRAM_PATH)

            with st.spinner("Generating bit-plane differences..."):
                generate_bit_plane_diff(cover, stego, BIT_PLANE_PREFIX)

            # Store results so they survive Streamlit reruns
            st.session_state["cover"] = cover
            st.session_state["stego"] = stego
            st.session_state["stego_image"] = STEGO_PATH.read_bytes()
            st.session_state["stego_filename"] = STEGO_PATH.name
            st.session_state["psnr"] = psnr

            st.success("Message embedded successfully!")

        except ValueError as e:
            st.error(f"Encoding failed: {e}")

    # Display results outside the button block
    # so they remain visible after clicking Download
    if "stego_image" in st.session_state:
        st.header("Cover and Stego Images")

        col1, col2 = st.columns(2)

        with col1:
            st.image(
                st.session_state["cover"],
                caption="Cover Image",
                width="stretch",
            )

        with col2:
            st.image(
                st.session_state["stego"],
                caption="Stego Image",
                width="stretch",
            )

        st.download_button(
            label="Download Stego Image",
            data=st.session_state["stego_image"],
            file_name=st.session_state["stego_filename"],
            mime="image/png",
            key="download_stego",
        )

        st.subheader(f"PSNR: {st.session_state['psnr']:.2f} dB")

        st.subheader("Histogram Comparison")
        st.image(
            str(HISTOGRAM_PATH),
            caption="Histogram",
            width="stretch",
        )

        st.subheader("Bit-Plane Differences")

        if st.session_state["cover"].ndim == 2:
            bit_plane_path = (
                BIT_PLANE_PREFIX.parent
                / f"{BIT_PLANE_PREFIX.name}.png"
            )

            st.image(
                str(bit_plane_path),
                caption="Bit-Plane Differences",
                width="stretch",
            )

        elif st.session_state["cover"].ndim == 3:
            for channel in ("R", "G", "B"):
                bit_plane_path = (
                    BIT_PLANE_PREFIX.parent
                    / f"{BIT_PLANE_PREFIX.name}_{channel}.png"
                )

                st.image(
                    str(bit_plane_path),
                    caption=f"{channel} Channel",
                    width="stretch",
                )


# ============================================================
# DECODE
# ============================================================

elif mode == "Decode":
    # Upload stego image
    st.header("Step 1: Upload Stego Image")

    stego_file = st.file_uploader(
        "Choose a stego image",
        type=["png", "jpg", "jpeg", "bmp", "tiff"],
        key="stego_uploader",
    )

    if st.button("Decode Message", disabled=stego_file is None):
        # Clear the previous decoded payload before decoding again
        st.session_state.pop("decoded", None)
        st.session_state.pop("decoded_filename", None)

        try:
            with st.spinner("Decoding the hidden message..."):
                stego_extension = Path(stego_file.name).suffix
                stego_path = UPLOADED_PATH / f"uploaded_stego{stego_extension}"
                stego_path.write_bytes(stego_file.getvalue())

                stego = read_image(stego_path)
                decoded = extract_message(stego)
                decoded_path = write_payload(decoded, DECODED_PATH)

            st.session_state["decoded"] = decoded
            st.session_state["decoded_filename"] = decoded_path.name

            st.success("Message decoded successfully!")

        except ValueError as e:
            st.error(f"Decoding failed: {e}")

    # Display download button outside the Decode button block
    if (
        "decoded" in st.session_state
        and "decoded_filename" in st.session_state
    ):
        st.download_button(
            label="Download Decoded Payload",
            data=st.session_state["decoded"],
            file_name=st.session_state["decoded_filename"],
            mime="application/octet-stream",
            key="download_decoded",
        )
