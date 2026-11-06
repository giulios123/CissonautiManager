"""The picture in the registration email: a background chosen by the organizers with a sentence
on top («I'm Ada Lovelace and I'll be at ... from ... to ...»).

The uploaded file is never kept as it came: it is checked, resized and re-encoded as PNG, which
also drops metadata and anything hidden in the file.
"""

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SIDE = 1600
# A decompression bomb (a small file that expands to gigabytes) is refused by Pillow above this.
MAX_PIXELS = 40_000_000
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
DEFAULT_SIZE = (1200, 630)
DEFAULT_BACKGROUND = (51, 92, 103)  # the petrol of the site

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Montserrat-ExtraBold.ttf"


class InvalidImage(Exception):
    """The file is not a usable image. `reason` is a short code for the error message."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def normalize_image(data: bytes) -> bytes:
    """Checks an uploaded picture and returns it as a PNG of at most MAX_SIDE pixels."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise InvalidImage("too_big")
    try:
        probe = Image.open(io.BytesIO(data))
        if probe.format not in ALLOWED_FORMATS:
            raise InvalidImage("wrong_format")
        if probe.width * probe.height > MAX_PIXELS:
            raise InvalidImage("too_big")
        probe.verify()
        picture = Image.open(io.BytesIO(data))
        picture = ImageOps.exif_transpose(picture).convert("RGB")
    except InvalidImage:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise InvalidImage("not_an_image") from None
    picture.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    picture.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int):
    """Greedy word wrap; a word longer than the line is broken."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=font) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            while draw.textlength(word, font=font) > width and len(word) > 1:
                cut = len(word) - 1
                while cut > 1 and draw.textlength(word[:cut], font=font) > width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        lines.append(line)
    return lines


def render_card(
    background: bytes | None, text: str, color: str = "#ffffff", position: str = "bottom"
) -> bytes:
    """The background with `text` on a translucent band, as PNG bytes."""
    if background:
        base = Image.open(io.BytesIO(background)).convert("RGBA")
    else:
        base = Image.new("RGBA", DEFAULT_SIZE, DEFAULT_BACKGROUND + (255,))
    width, height = base.size
    margin = round(width * 0.06)
    max_text_width = width - 2 * margin
    max_block_height = round(height * 0.32)

    probe = ImageDraw.Draw(base)
    size = max(round(height / 12), 12)
    while True:
        font = ImageFont.truetype(str(FONT_PATH), size)
        lines = _wrap(probe, text, font, max_text_width)
        line_height = round(size * 1.3)
        block_height = line_height * len(lines)
        if block_height <= max_block_height or size <= 12:
            break
        size -= 2

    padding = round(size * 0.6)
    band_height = block_height + 2 * padding
    if position == "top":
        top = 0
    elif position == "center":
        top = (height - band_height) // 2
    else:
        top = height - band_height
    band = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(band).rectangle([0, top, width, top + band_height], fill=(0, 0, 0, 120))
    base = Image.alpha_composite(base, band)

    draw = ImageDraw.Draw(base)
    y = top + padding
    for line in lines:
        draw.text((margin, y), line, font=font, fill=_hex_to_rgb(color) + (255,))
        y += line_height
    out = io.BytesIO()
    base.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
