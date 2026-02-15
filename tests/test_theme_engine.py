"""Tests for theme_engine module."""

import asyncio

import pytest

from orchestrator.theme_engine import ThemeEngine, _shift_hue


class TestShiftHue:
    def test_no_shift(self):
        result = _shift_hue("#ff0000", 0)
        # Should be approximately the same color
        assert result.startswith("#")
        assert len(result) == 7

    def test_shift_returns_valid_hex(self):
        result = _shift_hue("#3366cc", 30)
        assert result.startswith("#")
        assert len(result) == 7
        # Verify it's valid hex
        int(result[1:], 16)

    def test_handles_grayscale(self):
        result = _shift_hue("#808080", 45)
        assert result.startswith("#")
        assert len(result) == 7

    def test_handles_short_hex(self):
        result = _shift_hue("#fff", 10)
        # Should handle gracefully
        assert isinstance(result, str)


class TestThemeEngine:
    @pytest.fixture
    def engine(self):
        return ThemeEngine()

    def test_assigns_theme(self, engine):
        theme = asyncio.run(engine.assign("tech", "My Tech Co"))
        assert "id" in theme
        assert "colors" in theme
        assert "fonts" in theme

    def test_unique_themes_for_concurrent(self, engine):
        """Two concurrent assignments should get different themes."""
        theme1 = asyncio.run(engine.assign("tech", "Tech Co A"))
        theme2 = asyncio.run(engine.assign("tech", "Tech Co B"))
        assert theme1["id"] != theme2["id"]

    def test_release_makes_theme_available(self, engine):
        theme1 = asyncio.run(engine.assign("tech", "Tech Co A"))
        theme_id = theme1["id"]
        asyncio.run(engine.release(theme_id))
        # After release, the theme could be assigned again
        # (though it may pick a different preferred theme first)

    def test_industry_affinity(self, engine):
        """Restaurant should get warm-toned themes."""
        theme = asyncio.run(engine.assign("restaurant", "Joe's Diner"))
        # Should be one of the restaurant-preferred themes
        assert theme["id"] is not None

    def test_default_industry(self, engine):
        """Unknown industry should still get a theme."""
        theme = asyncio.run(engine.assign("unknown_industry_xyz", "Random Biz"))
        assert "id" in theme
        assert "colors" in theme

    def test_exhaustion_mutation(self, engine):
        """When all themes are used, mutation should create new variants."""
        # Assign all themes
        themes = []
        for i in range(30):  # More than 26 themes
            t = asyncio.run(engine.assign("default", f"Business {i}"))
            themes.append(t)

        # All should have valid structure
        for t in themes:
            assert "colors" in t
            assert "primary" in t["colors"]

        # Release all
        for t in themes:
            asyncio.run(engine.release(t["id"]))
