import io

import PIL.Image

from adt_press.utils.image import _has_visible_alpha


def _palette_png(transparency_index=None, pixel_data=None) -> PIL.Image.Image:
    image = PIL.Image.new("P", (2, 2))
    palette = [255, 0, 0, 0, 255, 0] + [0, 0, 0] * 254
    image.putpalette(palette)
    image.putdata(pixel_data or [0, 0, 0, 0])

    if transparency_index is not None:
        image.info["transparency"] = transparency_index

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return PIL.Image.open(buffer)


def test_palette_png_with_transparent_pixels_detects_alpha():
    palette_image = _palette_png(transparency_index=1, pixel_data=[0, 1, 0, 0])

    assert _has_visible_alpha(palette_image) is True


def test_palette_png_without_transparency_reports_false():
    palette_image = _palette_png()

    assert _has_visible_alpha(palette_image) is False
