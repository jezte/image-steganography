from pathlib import Path
import streamlit as st
from stego.analysis import calculate_psnr, generate_bit_plane_diff, generate_histogram
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

# Create output directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOADED_PATH.mkdir(parents=True, exist_ok=True)
(STEGO_PATH.parent).mkdir(parents=True, exist_ok=True)
(DECODED_PATH.parent).mkdir(parents=True, exist_ok=True)

st.title("Steganography App")

# User selects mode: Encode or Decode
mode = st.radio("Choose Mode", ["Encode", "Decode"])

if mode == "Encode":
    # Upload cover image
    st.header("Step 1: Upload Cover Image")
    cover_file = st.file_uploader("Choose a cover image", type=["png", "jpg", "jpeg", "bmp", "tiff"])
    encode_button_disabled = True

    if cover_file:
        cover_extension = Path(cover_file.name).suffix
        cover_path = UPLOADED_PATH / f"uploaded_cover{cover_extension}"
        with open(cover_path, "wb") as f:
            f.write(cover_file.read())
        cover = read_image(cover_path)

    # Upload payload file
    st.header("Step 2: Upload Payload File")
    payload_file = st.file_uploader("Choose a payload file", type=None)
    if payload_file:
        payload_extension = Path(payload_file.name).suffix
        payload_path = UPLOADED_PATH / f"uploaded_payload{payload_extension}"
        with open(payload_path, "wb") as f:
            f.write(payload_file.read())
        payload = read_bytes(payload_path)
        encode_button_disabled = False

    # Embed message and display results
    if st.button("Embed Message", disabled=encode_button_disabled):
        if cover_file and payload_file:
            with st.spinner("Embedding message into the cover image..."):
                stego = embed_message(cover, payload)
                write_image(stego, STEGO_PATH)

            # Display cover and stego images side-by-side
            st.header("Cover and Stego Images")
            col1, col2 = st.columns(2)
            with col1:
                st.image(cover, caption="Cover Image", width="stretch")
            with col2:
                st.image(stego, caption="Stego Image", width="stretch")

            # Calculate and display PSNR
            with st.spinner("Calculating PSNR..."):
                psnr = calculate_psnr(cover, stego)
            st.subheader(f"PSNR: {psnr:.2f} dB")

            # Generate and display histogram
            with st.spinner("Generating histogram..."):
                generate_histogram(cover, stego, HISTOGRAM_PATH)
            st.subheader("Histogram Comparison")
            st.image(HISTOGRAM_PATH, caption="Histogram", width="stretch")

            # Generate and display bit-plane differences
            with st.spinner("Generating bit-plane differences..."):
                generate_bit_plane_diff(cover, stego, BIT_PLANE_PREFIX)
            st.subheader("Bit-Plane Differences")

            if cover.ndim == 2:
                bit_plane_path = BIT_PLANE_PREFIX.parent / f"{BIT_PLANE_PREFIX.name}.png"
                st.image(bit_plane_path, caption="Bit-Plane Differences", width="stretch")
            elif cover.ndim == 3:
                for channel in ("R", "G", "B"):
                    bit_plane_path = (
                        BIT_PLANE_PREFIX.parent
                        / f"{BIT_PLANE_PREFIX.name}_{channel}.png"
                    )
                    st.image(bit_plane_path, caption=f"{channel} Channel", width="stretch")

elif mode == "Decode":
    # Upload stego image
    st.header("Step 1: Upload Stego Image")
    stego_file = st.file_uploader("Choose a stego image", type=["png", "jpg", "jpeg", "bmp", "tiff"])
    decode_button_disabled = True

    if stego_file:
        stego_extension = Path(stego_file.name).suffix
        stego_path = UPLOADED_PATH / f"uploaded_stego{stego_extension}"
        with open(stego_path, "wb") as f:
            f.write(stego_file.read())
        stego = read_image(stego_path)
        decode_button_disabled = False

    # Decode the message
    if st.button("Decode Message", disabled=decode_button_disabled):
        with st.spinner("Decoding the hidden message..."):
            try:
                decoded = extract_message(stego)
                decoded_path = write_payload(decoded, DECODED_PATH)
                # Save the decoded data to session state
                st.session_state["decoded"] = decoded
                st.session_state["decoded_filename"] = decoded_path.name
                st.success("Message decoded successfully!")
            except ValueError as e:
                st.session_state.pop("decoded", None)
                st.session_state.pop("decoded_filename", None)
                st.error(f"Decoding failed: {e}")

    # Display the download button if decoded data exists in session state
    # (because before this the button would disappear after it's clicked on)
    if "decoded" in st.session_state and "decoded_filename" in st.session_state:
        st.download_button(
            label="Download Decoded Payload",
            data=st.session_state["decoded"],
            file_name=st.session_state["decoded_filename"],
            mime="application/octet-stream",
            disabled=not stego_file
        )
