"""Tests for image validation utility."""
import io

from PIL import Image
from app.utils.image_validation import validate_image_bytes


class TestImageValidation:
    def test_valid_jpeg(self):
        """Valid JPEG passes validation."""
        img = Image.new("RGB", (200, 200), "blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        assert validate_image_bytes(buf.getvalue()) is True

    def test_valid_png(self):
        """Valid PNG passes validation."""
        img = Image.new("RGB", (200, 200), "green")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        assert validate_image_bytes(buf.getvalue()) is True

    def test_corrupt_bytes(self):
        """Random bytes fail validation."""
        assert validate_image_bytes(b"not an image at all") is False

    def test_empty_bytes(self):
        """Empty bytes fail validation."""
        assert validate_image_bytes(b"") is False

    def test_too_small(self):
        """Images smaller than min dimensions fail validation."""
        img = Image.new("RGB", (10, 10), "red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        assert validate_image_bytes(buf.getvalue(), min_width=50, min_height=50) is False

    def test_svg_xml_fails(self):
        """SVG/XML content fails validation."""
        svg = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        assert validate_image_bytes(svg) is False

    def test_none_bytes(self):
        """None input fails validation."""
        assert validate_image_bytes(None) is False

    def test_short_bytes(self):
        """Very short bytes fail validation."""
        assert validate_image_bytes(b"\x89PNG") is False
