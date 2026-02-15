"""Theme assignment engine — guarantees unique themes across concurrent sites."""

import asyncio
import hashlib
import json
import random
from pathlib import Path

from orchestrator.config import THEMES_FILE, INDUSTRY_DEFAULTS_FILE


class ThemeEngine:
    """
    Assigns unique themes to sites, ensuring no two concurrent sites share a theme.
    Uses industry affinity for best-fit matching with a lock for concurrency safety.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._in_use: set[str] = set()
        self._themes: list[dict] = []
        self._industry_map: dict[str, list[str]] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        with open(THEMES_FILE) as f:
            self._themes = json.load(f)
        with open(INDUSTRY_DEFAULTS_FILE) as f:
            self._industry_map = json.load(f)
        self._loaded = True

    async def assign(self, industry: str, business_name: str) -> dict:
        """
        Assign a unique theme for a business.

        Args:
            industry: Business industry (lowercase, underscores).
            business_name: Business name (for deterministic fallback).

        Returns:
            A theme dict from themes.json (possibly mutated for uniqueness).
        """
        async with self._lock:
            self._load()

            # Get preferred themes for this industry
            industry_key = industry.lower().replace(" ", "_")
            preferred_ids = self._industry_map.get(
                industry_key, self._industry_map.get("default", [])
            )

            # Try preferred themes first
            for theme_id in preferred_ids:
                if theme_id not in self._in_use:
                    theme = self._get_theme(theme_id)
                    if theme:
                        self._in_use.add(theme_id)
                        return theme

            # Fallback: any unused theme
            all_ids = [t["id"] for t in self._themes]
            random.shuffle(all_ids)
            for theme_id in all_ids:
                if theme_id not in self._in_use:
                    theme = self._get_theme(theme_id)
                    if theme:
                        self._in_use.add(theme_id)
                        return theme

            # All themes in use — mutate a random theme
            base_theme = random.choice(self._themes).copy()
            mutated = self._mutate_theme(base_theme, business_name)
            mutated_id = f"{base_theme['id']}-mutated-{business_name[:8]}"
            mutated["id"] = mutated_id
            self._in_use.add(mutated_id)
            return mutated

    async def release(self, theme_id: str) -> None:
        """Release a theme back to the pool after site deployment."""
        async with self._lock:
            self._in_use.discard(theme_id)

    def _get_theme(self, theme_id: str) -> dict | None:
        for t in self._themes:
            if t["id"] == theme_id:
                return t.copy()
        return None

    @staticmethod
    def _mutate_theme(theme: dict, seed: str) -> dict:
        """Apply deterministic color mutations to create a variant."""
        # Use business name as seed for consistent mutations
        h = int(hashlib.md5(seed.encode()).hexdigest()[:8], 16)
        hue_shift = (h % 30) - 15  # -15 to +15 degree shift

        colors = theme.get("colors", {})
        mutated_colors = {}
        for key, hex_color in colors.items():
            mutated_colors[key] = _shift_hue(hex_color, hue_shift)
        theme["colors"] = mutated_colors
        return theme


def _shift_hue(hex_color: str, degrees: int) -> str:
    """Shift the hue of a hex color by the given degrees."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"#{hex_color}"

    r, g, b = int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)

    # RGB to HSL (simplified)
    r_norm, g_norm, b_norm = r / 255, g / 255, b / 255
    max_c = max(r_norm, g_norm, b_norm)
    min_c = min(r_norm, g_norm, b_norm)
    diff = max_c - min_c

    # Lightness
    l = (max_c + min_c) / 2

    if diff == 0:
        h = 0
        s = 0
    else:
        s = diff / (1 - abs(2 * l - 1)) if (1 - abs(2 * l - 1)) != 0 else 0
        if max_c == r_norm:
            h = 60 * (((g_norm - b_norm) / diff) % 6)
        elif max_c == g_norm:
            h = 60 * ((b_norm - r_norm) / diff + 2)
        else:
            h = 60 * ((r_norm - g_norm) / diff + 4)

    # Shift hue
    h = (h + degrees) % 360

    # HSL back to RGB
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2

    if h < 60:
        r1, g1, b1 = c, x, 0
    elif h < 120:
        r1, g1, b1 = x, c, 0
    elif h < 180:
        r1, g1, b1 = 0, c, x
    elif h < 240:
        r1, g1, b1 = 0, x, c
    elif h < 300:
        r1, g1, b1 = x, 0, c
    else:
        r1, g1, b1 = c, 0, x

    r_out = int((r1 + m) * 255)
    g_out = int((g1 + m) * 255)
    b_out = int((b1 + m) * 255)

    r_out = max(0, min(255, r_out))
    g_out = max(0, min(255, g_out))
    b_out = max(0, min(255, b_out))

    return f"#{r_out:02x}{g_out:02x}{b_out:02x}"
