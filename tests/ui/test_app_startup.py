"""
Smoke tests for Alexandria Streamlit application.

Tests verify that the app loads correctly and essential UI elements are present.
These tests require a running Streamlit server (automatically started by fixtures).
"""

import re
import pytest
from playwright.sync_api import Page, expect


class TestAppStartup:
    """Basic smoke tests to verify app loads correctly."""

    def test_app_loads_without_error(self, app_page: Page):
        """Test that the app loads and displays content without errors."""
        # App should load without Streamlit error messages
        error_elements = app_page.locator('[data-testid="stException"]')
        assert error_elements.count() == 0, "App displayed an error on startup"

    def test_page_title_contains_alexandria(self, app_page: Page):
        """Test that page title contains 'Alexandria'."""
        expect(app_page).to_have_title(re.compile("Alexandria", re.IGNORECASE))

    def test_main_content_visible(self, app_page: Page):
        """Test that main content container is visible."""
        main_container = app_page.locator('[data-testid="stAppViewContainer"]')
        expect(main_container).to_be_visible()


# NOTE: TestNavigationTabs removed (2026-01-30)
# GUI refactored to single-page interface without tabs.
# See ADR-0003: GUI is now secondary query-only interface.
# Old tabs (Calibre ingestion, Folder ingestion, etc.) no longer exist.


class TestSidebar:
    """Tests for sidebar elements."""

    def test_sidebar_exists(self, app_page: Page):
        """Test that sidebar container exists."""
        sidebar = app_page.locator('[data-testid="stSidebar"]')
        expect(sidebar).to_be_attached()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
