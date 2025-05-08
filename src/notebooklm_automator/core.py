"""
Core functionality for NotebookLM Podcast Automator.

This module contains the common functionality shared between the CLI and Streamlit versions.
"""
import time
from playwright.sync_api import Page, sync_playwright, Error as PlaywrightError

from notebooklm_automator.links import add_link_sources, generate_audio_overview

class NotebookLMAutomator:
    """
    Core class for automating NotebookLM operations.

    This class handles the common functionality for both CLI and Streamlit versions:
    1. Connecting to Chrome via CDP
    2. Navigating to NotebookLM
    3. Adding URLs as sources
    4. Generating audio overview
    """

    def __init__(self, port=9222):
        """
        Initialize the automator with the specified CDP port.

        Args:
            port: Port for Chrome DevTools Protocol (CDP) connection (default: 9222).
        """
        self.port = port
        self.playwright = None
        self.browser = None
        self.page = None

    def __enter__(self):
        """
        Context manager entry point.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        self.close()

    def connect(self):
        """
        Connect to Chrome via CDP and navigate to NotebookLM.

        Returns:
            self: For method chaining.

        Raises:
            PlaywrightError: If connection to Chrome fails.
            Exception: For other unexpected errors.
        """
        self.playwright = sync_playwright().start()

        try:
            # Connect to Chrome via CDP
            self.browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{self.port}")

            # Check if there are any browser contexts
            if not self.browser.contexts:
                raise PlaywrightError("No browser contexts found. Make sure Chrome is running with an open window.")

            # Use the first available context
            context = self.browser.contexts[0]
            self.page = context.new_page()

            # Navigate to NotebookLM
            self.page.goto("https://notebooklm.google.com/", timeout=60000)

            return self

        except Exception as e:
            # Clean up resources in case of error
            self.close()
            raise e

    def process_urls(self, urls_list, progress_callback=None):
        """
        Process a list of URLs by adding them as sources to NotebookLM.

        Args:
            urls_list: List of URLs to add as sources.
            progress_callback: Optional callback function to report progress.
                               Called with (current_index, total_count, current_url).

        Returns:
            self: For method chaining.
        """
        if not self.page:
            raise ValueError("Not connected to NotebookLM. Call connect() first.")

        # Process each URL and pass the progress callback
        add_link_sources(urls_list, self.page, progress_callback)

        return self

    def generate_audio(self):
        """
        Generate audio overview in NotebookLM.

        Returns:
            self: For method chaining.
        """
        if not self.page:
            raise ValueError("Not connected to NotebookLM. Call connect() first.")

        generate_audio_overview(self.page)
        return self

    def close(self):
        """
        Close the page and clean up resources.
        """
        try:
            if self.page and not self.page.is_closed():
                self.page = None
        finally:
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                self.browser = None

def run_automation_with_urls(urls_list, port=9222, progress_callback=None):
    """
    Run the automation process with the provided URLs.

    This is a convenience function that handles the common workflow:
    1. Connect to Chrome via CDP
    2. Navigate to NotebookLM
    3. Add URLs as sources
    4. Generate audio overview

    Args:
        urls_list: List of URLs to add as sources.
        port: Port for Chrome DevTools Protocol (CDP) connection (default: 9222).
        progress_callback: Optional callback function to report progress.
                           Called with (current_index, total_count, current_url).

    Raises:
        PlaywrightError: If connection to Chrome fails.
        Exception: For other unexpected errors.
    """
    with NotebookLMAutomator(port) as automator:
        automator.connect()
        automator.process_urls(urls_list, progress_callback)
        automator.generate_audio()
