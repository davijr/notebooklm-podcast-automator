"""
Spotify integration for NotebookLM Podcast Automator.

This module provides functionality to upload podcast episodes to Spotify for Podcasters.
"""
import os
import tempfile
import time
from pathlib import Path
from typing import Optional, Callable, Tuple

from playwright.sync_api import Page, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

class SpotifyAutomator:
    """
    Class for automating podcast uploads to Spotify for Podcasters.
    """

    def __init__(self, page: Page):
        """
        Initialize the Spotify automator with a Playwright page.

        Args:
            page: Playwright page object connected to a browser instance.
        """
        self.page = page
        self.temp_dir = Path(tempfile.mkdtemp(prefix="notebooklm_spotify_"))

    def upload_episode(
        self,
        audio_file_path: str,
        title: str,
        description: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Tuple[bool, str]:
        """
        Upload an episode to Spotify for Podcasters.

        Args:
            audio_file_path: Path to the audio file to upload.
            title: Title of the episode.
            description: Description of the episode.
            progress_callback: Optional callback for progress updates.
                             Called with (message, progress_percentage).

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self._update_progress(progress_callback, "Starting Spotify upload process...", 0)
            
            # Navigate directly to the upload page
            self._navigate_to_upload_page()
            
            # Upload audio file
            self._upload_audio_file(audio_file_path)
            
            # Fill in episode details
            self._fill_episode_details(title, description)
            
            # Publish the episode
            self._publish_episode()
            
            self._update_progress(progress_callback, "Episode upload completed successfully!", 100)
            return True, "Successfully uploaded episode to Spotify"
            
        except PlaywrightError as e:
            error_msg = f"Playwright error during Spotify upload: {str(e)}"
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during Spotify upload: {str(e)}"
            return False, error_msg
        finally:
            # Clean up temporary files
            self._cleanup()

    def _navigate_to_upload_page(self):
        """Navigate directly to the episode upload page."""
        self.page.goto("https://creators.spotify.com/pod/dashboard/episode/wizard", timeout=60000)
        # Wait for the file upload button to appear
        self.page.wait_for_selector("button:has-text('ファイルを選択')", timeout=30000)
        
    def _start_new_episode(self):
        """Legacy method kept for backward compatibility."""
        self._navigate_to_upload_page()

    def _upload_audio_file(self, file_path: str):
        """
        Upload an audio file to Spotify.
        
        Args:
            file_path: Path to the audio file to upload.
        """
        # Make sure the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
            
        # Click the file selection button and handle the file chooser
        with self.page.expect_file_chooser() as fc_info:
            self.page.click("button:has-text('ファイルを選択')")
        file_chooser = fc_info.value
        file_chooser.set_files(file_path)
        
        # Wait for upload to complete
        # Note: The actual text might need adjustment based on the UI
        try:
            # Wait for either "Upload complete" or the next step to appear
            self.page.wait_for_selector(
                "button:has-text('次へ')", 
                timeout=300000  # 5 minute timeout for upload
            )
        except Exception as e:
            # If the upload seems stuck, check for any error messages
            error_elements = self.page.query_selector_all("[role='alert'], .error-message, .upload-error")
            if error_elements:
                error_text = "\n".join([el.inner_text() for el in error_elements if el.inner_text().strip()])
                if error_text:
                    raise Exception(f"Upload failed with error: {error_text}")
            raise  # Re-raise the original exception if no specific error message found

    def _fill_episode_details(self, title: str, description: str):
        """
        Fill in the episode details form.
        
        Args:
            title: Episode title.
            description: Episode description.
        """
        # Wait for the title input to be visible and fill it
        title_field = self.page.wait_for_selector("input#title-input", timeout=30000)
        title_field.fill(title)
        
        # Fill in the description (contenteditable div)
        description_div = self.page.wait_for_selector("div[role='textbox'][name='description']", timeout=30000)
        description_div.click()  # Focus the description field
        description_div.fill(description)
        
        # Wait for the form to be considered valid (Next button becomes clickable)
        next_button = self.page.wait_for_selector(
            "button[type='submit'][form='details-form']:not([disabled])", 
            timeout=30000
        )
        next_button.click()
        
        # Wait for the next step to load (publish button)
        self.page.wait_for_selector("button:has-text('公開する')", timeout=30000)

    def _publish_episode(self):
        """Click the publish button to submit the episode."""
        # Wait for and click the publish button
        publish_button = self.page.wait_for_selector(
            "button:has-text('公開する'):not([disabled])", 
            timeout=30000
        )
        publish_button.click()
        
    def _update_progress(
        self,
        progress_callback: Optional[Callable[[str, int], None]],
        message: str,
        progress: int
    ) -> None:
        """
        Update progress if a callback is provided.
        
        Args:
            progress_callback: Callback function to update progress.
            message: Progress message.
            progress: Progress percentage (0-100).
        """
        if progress_callback:
            progress_callback(message, progress)

    def _cleanup(self):
        """Clean up temporary files and directories."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            # Remove all files in the temp directory
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            # Remove the directory itself
            self.temp_dir.rmdir()
