import math
from typing import Iterator
import numpy as np

END_MARKER = "~end~"
_BLOCK_MASK = np.array([[True, True, True], [True, False, False]])


def _message_to_bits(message: bytes, marker: str = END_MARKER) -> str:
    """ Convert a byte payload and end marker to a binary string. """
    payload_bits = "".join(f"{byte:08b}" for byte in message)
    marker_bits = "".join(f"{ord(char):08b}" for char in marker)
    return payload_bits + marker_bits


def _iter_blocks(image: np.ndarray) -> Iterator[tuple[tuple[int, ...], np.ndarray]]:
    """ Yield (center-index, neighborhood) pairs for 2D or 3D images. """
    if image.ndim == 2:
        for row in range(image.shape[0] - 1):
            for col in range(image.shape[1] - 2):
                yield (row+1, col+1), image[row:row+2, col:col+3]

    elif image.ndim == 3:
        for channel in range(image.shape[2]):
            for row in range(image.shape[0] - 1):
                for col in range(image.shape[1] - 2):
                    yield (
                        (row+1, col+1, channel),
                        image[row:row+2, col:col+3, channel],
                    )
    else:
        raise ValueError("Image must be a 2D grayscale or 3D multi-channel array.")


def _capacity_bits(neighborhood: np.ndarray) -> int:
    """ Return the number of payload bits available in one neighborhood. """
    values = neighborhood[_BLOCK_MASK]
    # difference is labeled with 'd' in paper
    # d = g_max - g_min
    difference = int(values.max()) - int(values.min())
    # return value is labeled with 'n' in paper
    return math.floor(math.log2(difference)) - 1 if difference > 3 else 1


def _embedding_capacity(image: np.ndarray) -> int:
    """ Return total capacity in bits for an image. """
    return sum(_capacity_bits(block) for _, block in _iter_blocks(image))


def _embedding_offset(value: int, payload_value: int, n_bits: int) -> int:
    """ Calculate the minimum wrapped modification for an n-bit value. """
    modulus = 2**n_bits
    target = payload_value
    current = value % modulus
    delta = target - current

    lower = -math.floor((modulus - 1) / 2)
    upper = math.ceil((modulus - 1) / 2)

    if lower <= delta <= upper:
        return delta
    if -modulus + 1 <= delta < lower:
        return delta + modulus
    if upper < delta < modulus:
        return delta - modulus

    raise RuntimeError("Unable to calculate a valid embedding offset.")


def _apply_modification(value: int, offset: int, n_bits: int) -> int:
    """ Apply an offset while keeping the pixel in the valid 8-bit range. """
    result = value + offset
    modulus = 2**n_bits

    if result < 0:
        result += modulus
    elif result > 255:
        result -= modulus

    return result


def embed_message(
    cover: np.ndarray,
    message: bytes,
    *,
    marker: str = END_MARKER,
) -> np.ndarray:
    """ Embed "message" into a uint8 grayscale or multi-channel image.

    Raises:
        ValueError: if the image type/shape is invalid or the payload is too large.
    """
    if cover.dtype != np.uint8:
        raise ValueError("Cover image must have dtype uint8.")

    if cover.ndim not in (2, 3):
        raise ValueError("Cover image must be grayscale (2D) or multi-channel (3D).")

    bits = _message_to_bits(message, marker)
    capacity = _embedding_capacity(cover)

    if len(bits) > capacity:
        available_payload_bits = max(0, capacity - len(marker.encode("utf-8")) * 8)
        raise ValueError(
            f"Message is too large: {len(bits)} bits required, "
            f"but only {capacity} bits are available "
            f"(about {available_payload_bits // 8} payload bytes)."
        )

    stego = cover.astype(np.int16, copy=True)
    bit_index = 0

    for center, neighborhood in _iter_blocks(stego):
        n_bits = _capacity_bits(neighborhood)

        if bit_index >= len(bits):
            break

        chunk = bits[bit_index:bit_index+n_bits]

        chunk = chunk.ljust(n_bits, "0")
        payload_value = int(chunk, 2)

        current_value = int(stego[center])
        offset = _embedding_offset(current_value, payload_value, n_bits)
        stego[center] = _apply_modification(current_value, offset, n_bits)

        bit_index += n_bits

    if bit_index < len(bits):
        raise RuntimeError("Embedding stopped before the complete payload was written.")

    return stego.astype(np.uint8)


def extract_message(
    stego: np.ndarray,
    *,
    marker: str = END_MARKER,
) -> bytes:
    """ Extract the payload from a stego image.

    Raises:
        ValueError: if the marker cannot be found.
    """
    if stego.dtype != np.uint8:
        raise ValueError("Stego image must have dtype uint8.")

    if stego.ndim not in (2, 3):
        raise ValueError("Stego image must be grayscale (2D) or multi-channel (3D).")

    bits: list[str] = []

    for center, neighborhood in _iter_blocks(stego):
        n_bits = _capacity_bits(neighborhood)
        value = int(stego[center]) % (2**n_bits)
        bits.append(format(value, f"0{n_bits}b"))

    bit_stream = "".join(bits)
    marker_bits = "".join(f"{ord(char):08b}" for char in marker)

    marker_position = bit_stream.find(marker_bits)
    if marker_position == -1:
        raise ValueError("End-of-message marker was not found.")

    payload_bits = bit_stream[:marker_position]

    # The original algorithm stores bytes, so the payload must be byte-aligned.
    if len(payload_bits) % 8 != 0:
        raise ValueError("Extracted payload is not byte-aligned.")

    return bytes(
        int(payload_bits[index:index+8], 2)
        for index in range(0, len(payload_bits), 8)
    )
