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


class TestNavigationTabs:
    """Tests for main navigation tabs."""

    def test_calibre_ingestion_tab_visible(self, app_page: Page):
        """Test that Calibre ingestion tab is visible."""
        tab = app_page.locator('button[role="tab"]').filter(has_text="Calibre ingestion")
        expect(tab).to_be_visible()

    def test_folder_ingestion_tab_visible(self, app_page: Page):
        """Test that Folder ingestion tab is visible."""
        tab = app_page.locator('button[role="tab"]').filter(has_text="Folder ingestion")
        expect(tab).to_be_visible()

    def test_qdrant_collections_tab_visible(self, app_page: Page):
        """Test that Qdrant collections tab is visible."""
        tab = app_page.locator('button[role="tab"]').filter(has_text="Qdrant collections")
        expect(tab).to_be_visible()

    def test_speakers_corner_tab_visible(self, app_page: Page):
        """Test that Speaker's corner tab is visible."""
        tab = app_page.locator('button[role="tab"]').filter(has_text="Speaker's corner")
        expect(tab).to_be_visible()

    def test_can_navigate_between_tabs(self, app_page: Page):
        """Test that clicking tabs changes the active tab."""
        # Find and click the Speaker's corner tab
        speaker_tab = app_page.locator('button[role="tab"]').filter(has_text="Speaker's corner")
        speaker_tab.click()

        # Verify it's now selected
        expect(speaker_tab).to_have_attribute("aria-selected", "true")

        # Navigate back to first tab
        calibre_tab = app_page.locator('button[role="tab"]').filter(has_text="Calibre ingestion")
        calibre_tab.click()
        expect(calibre_tab).to_have_attribute("aria-selected", "true")


class TestSidebar:
    """Tests for sidebar elements."""

    def test_sidebar_exists(self, app_page: Page):
        """Test that sidebar container exists."""
        sidebar = app_page.locator('[data-testid="stSidebar"]')
        expect(sidebar).to_be_attached()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
