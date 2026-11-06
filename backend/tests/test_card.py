import io

import pytest
from PIL import Image

from app.email.card import (
    MAX_SIDE,
    MAX_UPLOAD_BYTES,
    InvalidImage,
    normalize_image,
    render_card,
)


def picture(fmt="PNG", size=(800, 400), color=(200, 30, 30)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, format=fmt)
    return out.getvalue()


def open_png(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    assert image.format == "PNG"
    return image


class TestNormalize:
    @pytest.mark.parametrize("fmt", ["PNG", "JPEG", "WEBP"])
    def test_accepted_formats_come_out_as_png(self, fmt):
        assert open_png(normalize_image(picture(fmt))).size == (800, 400)

    def test_big_pictures_are_shrunk_keeping_the_ratio(self):
        image = open_png(normalize_image(picture(size=(3200, 1600))))
        assert image.size == (MAX_SIDE, MAX_SIDE // 2)

    def test_small_pictures_are_not_enlarged(self):
        assert open_png(normalize_image(picture(size=(100, 50)))).size == (100, 50)

    def test_transparency_is_flattened(self):
        out = io.BytesIO()
        Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(out, format="PNG")
        assert open_png(normalize_image(out.getvalue())).mode == "RGB"

    def test_metadata_does_not_survive(self):
        out = io.BytesIO()
        info = Image.Exif()
        info[0x010E] = "secret description"
        Image.new("RGB", (10, 10)).save(out, format="JPEG", exif=info)
        result = normalize_image(out.getvalue())
        assert b"secret description" not in result

    def test_exif_rotation_is_applied(self):
        out = io.BytesIO()
        info = Image.Exif()
        info[0x0112] = 6  # rotated 90 degrees
        Image.new("RGB", (40, 20)).save(out, format="JPEG", exif=info)
        assert open_png(normalize_image(out.getvalue())).size == (20, 40)

    @pytest.mark.parametrize(
        "data", [b"", b"hello", b"%PDF-1.4 not an image", b"GIF89a" + b"0" * 20]
    )
    def test_files_that_are_not_pictures_are_refused(self, data):
        with pytest.raises(InvalidImage) as error:
            normalize_image(data)
        assert error.value.reason in {"not_an_image", "wrong_format"}

    def test_a_gif_is_a_wrong_format(self):
        with pytest.raises(InvalidImage) as error:
            normalize_image(picture("GIF"))
        assert error.value.reason == "wrong_format"

    def test_too_big_a_file_is_refused(self):
        with pytest.raises(InvalidImage) as error:
            normalize_image(b"0" * (MAX_UPLOAD_BYTES + 1))
        assert error.value.reason == "too_big"

    def test_a_decompression_bomb_is_refused(self):
        out = io.BytesIO()
        Image.new("1", (9000, 9000)).save(out, format="PNG")
        with pytest.raises(InvalidImage) as error:
            normalize_image(out.getvalue())
        assert error.value.reason == "too_big"


class TestRender:
    def test_without_a_background_a_default_one_is_used(self):
        image = open_png(render_card(None, "Sono Ada Lovelace", "#ffffff", "bottom"))
        assert image.size == (1200, 630)

    def test_the_picture_keeps_the_size_of_the_background(self):
        background = normalize_image(picture(size=(900, 300)))
        assert open_png(render_card(background, "Ciao", "#ffffff", "top")).size == (900, 300)

    def _text_pixels(self, data: bytes, color=(255, 255, 255)) -> list[tuple[int, int]]:
        image = open_png(data).convert("RGB")
        return [
            (x, y)
            for y in range(image.height)
            for x in range(0, image.width, 2)
            if image.getpixel((x, y)) == color
        ]

    @pytest.mark.parametrize("position", ["top", "center", "bottom"])
    def test_the_text_sits_where_it_was_asked(self, position):
        background = normalize_image(picture(size=(600, 400), color=(20, 20, 20)))
        pixels = self._text_pixels(render_card(background, "Ada", "#ffffff", position))
        assert pixels, "no text was drawn"
        middle = sum(y for _, y in pixels) / len(pixels)
        expected = {"top": 100, "center": 200, "bottom": 300}[position]
        assert abs(middle - expected) < 70

    def test_the_text_has_the_chosen_color(self):
        background = normalize_image(picture(size=(600, 400), color=(20, 20, 20)))
        data = render_card(background, "Ada", "#ffbc42", "center")
        assert self._text_pixels(data, color=(255, 188, 66))

    def test_a_long_sentence_wraps_and_stays_inside_the_picture(self):
        text = (
            "I'm Ada Lovelace and I'll be at Cissonauti Summer Camp "
            "from 10 July 2027 to 16 July 2027"
        )
        background = normalize_image(picture(size=(1200, 630), color=(20, 20, 20)))
        pixels = self._text_pixels(render_card(background, text, "#ffffff", "bottom"))
        xs = [x for x, _ in pixels]
        assert min(xs) >= 1200 * 0.04 and max(xs) <= 1200 * 0.96

    def test_accents_and_very_long_names_do_not_break_it(self):
        text = "Sono Édouard Müller-Ñandú Supercalifragilistichespiralidoso e sarò a Camp"
        assert open_png(render_card(None, text, "#ffffff", "center")).size == (1200, 630)
        giant = "Pneumonoultramicroscopicsilicovolcanoconiosis" * 4
        assert open_png(render_card(None, giant, "#ffffff", "top")).size == (1200, 630)

    def test_newlines_in_the_text_make_new_lines(self):
        one = render_card(None, "AAA BBB", "#ffffff", "center")
        two = render_card(None, "AAA\nBBB", "#ffffff", "center")
        assert one != two
