""" Steganography quality and visualization helpers. """

from pathlib import Path
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def calculate_psnr(cover: np.ndarray, stego: np.ndarray) -> float:
    """ Calculate PSNR in dB for two equal-sized uint8 images. """
    if cover.shape != stego.shape:
        raise ValueError("Cover and stego images must have the same shape.")

    mse = np.mean(
        (cover.astype(np.float64) - stego.astype(np.float64)) ** 2
    )

    if mse == 0:
        return float("inf")

    return float(10 * np.log10((255.0**2) / mse))


def show_images(cover: np.ndarray, stego: np.ndarray) -> None:
    """ Display cover and stego images. """

    for image, title in ((cover, "Cover"), (stego, "Stego")):
        if image.ndim == 2:
            fig = px.imshow(image, zmin=0, zmax=255, color_continuous_scale="gray", title=title)
        else:
            fig = px.imshow(image, zmin=0, zmax=255, title=title)

        fig.show()


def generate_histogram(cover: np.ndarray, stego: np.ndarray, output_path: Path) -> go.Figure:
    """ Compare first-order pixel differences of cover and stego images. """
    def adjacent_differences(image: np.ndarray) -> np.ndarray:
        flattened = image.astype(np.int16).ravel()
        return flattened[:-1] - flattened[1:]

    cover_diff = adjacent_differences(cover)
    stego_diff = adjacent_differences(stego)

    bins = np.arange(-100, 102)

    cover_hist = np.histogram(cover_diff, bins=bins)[0]
    stego_hist = np.histogram(stego_diff, bins=bins)[0]
    x = bins[:-1]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Cover", "Stego"),
    )
    fig.add_trace(go.Bar(x=x, y=cover_hist, name="Cover", marker_color="blue"), row=1, col=1)
    fig.add_trace(go.Bar(x=x, y=stego_hist, name="Stego", marker_color="red"), row=1, col=2)
    fig.update_layout(title="Adjacent Pixel Difference Histogram")
    fig.write_image(output_path, width=1800, height=700, scale=2)

    return fig


def bit_plane(image: np.ndarray, bit: int) -> np.ndarray:
    """ Extract one bit plane as a 0/1 uint8 image. """
    if not 0 <= bit <= 7:
        raise ValueError("bit must be between 0 and 7.")

    return ((image.astype(np.uint8) >> bit) & 1).astype(np.uint8)


def generate_bit_plane_diff(
    cover: np.ndarray,
    stego: np.ndarray,
    output_prefix: str | Path,
) -> go.Figure | tuple[go.Figure, go.Figure, go.Figure]:
    """ Save and display differences between cover and stego bit planes. """

    if cover.shape != stego.shape:
        raise ValueError("Cover and stego images must have the same shape.")

    output_prefix = Path(output_prefix)
    output_prefix.parent.mkdir(parents=True, exist_ok=True)

    if cover.ndim == 2:
        fig = make_subplots(
            rows=2,
            cols=4,
            horizontal_spacing=0.02,
            vertical_spacing=0.05,
        )

        for bit in range(8):
            diff = bit_plane(cover, bit) ^ bit_plane(stego, bit)
            diff_image = (diff * 255).astype(np.uint8)

            fig.add_trace(
                go.Image(
                    z=np.stack([diff_image] * 3, axis=2),
                ),
                row=bit // 4 + 1,
                col=bit % 4 + 1,
            )

        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        fig.update_layout(
            title="Bit Plane Differences",
            margin=dict(t=50, b=20, l=20, r=20),
        )

        output = output_prefix.parent / f"{output_prefix.name}.png"
        fig.write_image(output, width=1800, height=700, scale=2)

        return fig

    if cover.ndim == 3:
        channels = cover.shape[2]

        if channels != 3:
            raise ValueError("3D images must have exactly 3 channels (RGB).")

        figures = []

        for channel, channel_name in enumerate(("R", "G", "B")):
            fig = make_subplots(
                rows=2,
                cols=4,
                horizontal_spacing=0.02,
                vertical_spacing=0.05,
            )

            for bit in range(8):
                diff = (
                    bit_plane(cover[:, :, channel], bit)
                    ^ bit_plane(stego[:, :, channel], bit)
                )

                diff_image = (diff * 255).astype(np.uint8)

                fig.add_trace(
                    go.Image(
                        z=np.stack([diff_image] * 3, axis=2),
                    ),
                    row=bit // 4 + 1,
                    col=bit % 4 + 1,
                )

            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)

            fig.update_layout(
                title=f"{channel_name} Channel Bit Plane Differences",
                margin=dict(t=50, b=20, l=20, r=20),
            )

            output = (
                output_prefix.parent
                / f"{output_prefix.name}_{channel_name}.png"
            )

            fig.write_image(output, width=1800, height=700, scale=2)

            figures.append(fig)

        return tuple(figures)

    raise ValueError("Image must be 2D or 3D.")
