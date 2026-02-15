"""Tests for session_manager module."""

from orchestrator.session_manager import build_pm_prompt


class TestBuildPmPrompt:
    def test_includes_business_name(self):
        biz = {"business_name": "Acme Corp", "industry": "tech", "description": "A tech company", "services": "Web dev"}
        theme = {"name": "Modern Minimal", "id": "modern-minimal"}
        prompt = build_pm_prompt(biz, theme)
        assert "Acme Corp" in prompt

    def test_includes_industry(self):
        biz = {"business_name": "Test", "industry": "restaurant", "description": "", "services": ""}
        theme = {"name": "Warm Rustic", "id": "warm-rustic"}
        prompt = build_pm_prompt(biz, theme)
        assert "restaurant" in prompt

    def test_includes_theme(self):
        biz = {"business_name": "Test", "industry": "tech", "description": "", "services": ""}
        theme = {"name": "Dark Tech", "id": "dark-tech"}
        prompt = build_pm_prompt(biz, theme)
        assert "Dark Tech" in prompt

    def test_includes_key_instructions(self):
        biz = {"business_name": "Test", "industry": "tech", "description": "", "services": ""}
        theme = {"name": "Test", "id": "test"}
        prompt = build_pm_prompt(biz, theme)
        assert "brief.json" in prompt
        assert "sub-agents" in prompt
        assert "status.json" in prompt
