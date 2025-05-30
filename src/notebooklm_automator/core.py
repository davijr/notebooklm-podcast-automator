"""
Core functionality for NotebookLM Podcast Automator.

This module contains the common functionality shared between the CLI and Streamlit versions.
"""
import os
import string
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Callable, Tuple, Dict, Any
from ulid import ULID

import os
# Force sync API to avoid asyncio conflicts
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

from playwright.sync_api import Page, sync_playwright, Error as PlaywrightError

from notebooklm_automator.links import add_link_sources, generate_audio_overview
from notebooklm_automator.spotify import SpotifyAutomator

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
        self.connect()
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

            # Set viewport size to ensure proper layout (minimum width 1261px for 3-column layout)
            self.page.set_viewport_size({"width": 1280, "height": 800})

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
                
    def download_audio(self, project_url: str, output_dir: Optional[str] = None) -> Tuple[bool, str, str, str]:
        """
        Download the audio file from a NotebookLM project.
        
        Args:
            project_url: URL of the NotebookLM project.
            output_dir: Directory to save the audio file. If None, uses a temporary directory.
            
        Returns:
            Tuple of (success: bool, file_path: str or error message: str, title: str, description: str)
        """
        if not self.page:
            return False, "Not connected to NotebookLM. Call connect() first.", "", ""
            
        try:
            # Navigate to the project
            self.page.goto(project_url, timeout=60000)
            
            # Get notebook title and description before any interactions
            title = self.get_notebook_title()
            description = self.get_notebook_summary()
            
            # Check if we need to load the audio first
            load_button = self.page.locator("button:has-text('読み込み')")
            if load_button.is_visible():
                load_button.click()
                # Wait for the play button to become visible after loading
                self.page.wait_for_selector("button[aria-label='音声を再生']", timeout=120000)  # Wait up to 2 minutes for audio to load
            
            # Wait for the audio player to be ready
            self.page.wait_for_selector("button[aria-label='音声を再生']", timeout=30000)
            
            # Click the options button to show the download menu
            options_button = self.page.locator("button[aria-label='オーディオ プレーヤーに関するその他のオプションを表示']")
            if not options_button.is_visible():
                return False, "Could not find audio options button", "", ""
                
            options_button.click()
            
            # Wait for the menu to appear and click the download link
            download_link = self.page.locator("a[mat-menu-item]:has-text('ダウンロード')")
            if not download_link.is_visible():
                return False, "Could not find download link in the menu", "", ""
                
            # Get the download URL from the href attribute
            download_url = download_link.get_attribute("href")
            if not download_url:
                return False, "Download link has no href attribute", "", ""
                
            # Create output directory if it doesn't exist
            if output_dir is None:
                output_dir = Path(tempfile.mkdtemp(prefix="notebooklm_audio_"))
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate a ULID-based filename
            filename = f"{ULID()}.mp3"
            
            file_path = output_dir / filename
            
            # Get the download URL and use requests to download manually
            print("Starting audio download...")
            
            # Get cookies from the browser context
            context = self.page.context
            cookies = context.cookies()
            
            # Convert cookies to requests format
            import requests
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            
            # Set headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'audio/mpeg,audio/*,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': self.page.url
            }
            
            # Download the file using requests
            response = session.get(download_url, headers=headers, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Audio downloaded successfully to: {file_path}")
                
            return True, str(file_path), title, description
            
        except Exception as e:
            return False, f"Error downloading audio: {str(e)}", "", ""
    
    def get_notebook_title(self) -> str:
        """
        Get the title of the current notebook.
        
        Returns:
            str: The notebook title.
        """
        title_element = self.page.wait_for_selector("h1.notebook-title", timeout=10000)
        return title_element.inner_text().strip()
    
    def get_notebook_summary(self) -> str:
        """
        Get the summary/description of the current notebook.
        
        Returns:
            str: The notebook summary/description.
        """
        summary_element = self.page.wait_for_selector("div.summary-content", timeout=10000)
        return summary_element.inner_text().strip()

    def upload_to_spotify(
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
        if not self.page:
            return False, "Not connected to browser. Call connect() first."
            
        spotify = SpotifyAutomator(self.page)
        return spotify.upload_episode(audio_file_path, title, description, progress_callback)
    
    def process_notebooklm_project(
        self,
        project_url: str,
        spotify_upload: bool = True,
        output_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """
        Process a single NotebookLM project: download audio and optionally upload to Spotify.
        
        Args:
            project_url: URL of the NotebookLM project.
            spotify_upload: Whether to upload to Spotify after downloading.
            output_dir: Directory to save the audio file. If None, uses a temporary directory.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Dict containing the results of the operation.
        """
        result = {
            "project_url": project_url,
            "success": False,
            "audio_file": None,
            "spotify_uploaded": False,
            "error": None
        }
        
        try:
            # Download the audio file
            self._update_progress(progress_callback, f"Downloading audio from {project_url}...", 10)
            success, audio_result = self.download_audio(project_url, output_dir)
            
            if not success:
                result["error"] = audio_result
                return result
                
            result["audio_file"] = audio_result
            self._update_progress(progress_callback, f"Downloaded audio to {audio_result}", 50)
            
            # Upload to Spotify if requested
            if spotify_upload:
                self._update_progress(progress_callback, "Uploading to Spotify...", 60)
                
                # Get project title for the episode
                title = Path(audio_result).stem.replace("_", " ").title()
                
                upload_success, upload_message = self.upload_to_spotify(
                    audio_file_path=audio_result,
                    title=title,
                    description=f"Automatically uploaded from NotebookLM: {project_url}",
                    progress_callback=lambda msg, pct: self._update_progress(
                        progress_callback, f"Spotify: {msg}", 60 + int(pct * 0.4)
                    )
                )
                
                if upload_success:
                    result["spotify_uploaded"] = True
                    self._update_progress(progress_callback, "Successfully uploaded to Spotify", 100)
                else:
                    result["error"] = f"Spotify upload failed: {upload_message}"
                    return result
            
            result["success"] = True
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
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
            progress_callback(message, min(max(progress, 0), 100))

def run_automation_with_urls(
    urls_list: List[str],
    port: int = 9222,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    output_dir: Optional[str] = None,
    upload_to_spotify: bool = True
) -> List[Dict[str, Any]]:
    """
    Run the automation process with the provided NotebookLM project URLs.

    This is a convenience function that handles the common workflow:
    1. Connect to Chrome via CDP
    2. For each project URL:
       - Download the audio file
       - Optionally upload to Spotify for Podcasters
    
    Args:
        urls_list: List of NotebookLM project URLs.
        port: Port for Chrome DevTools Protocol (CDP) connection.
        progress_callback: Optional callback function for progress updates.
        output_dir: Directory to save audio files. If None, uses a 'downloads' directory.
        upload_to_spotify: Whether to upload the audio to Spotify for Podcasters.
        
    Returns:
        List of result dictionaries with 'url', 'success', 'audio_file', and 'spotify_upload' keys.
    """
    results = []
    total = len(urls_list)
    
    with NotebookLMAutomator(port) as automator:
        for i, url in enumerate(urls_list, 1):
            progress = int((i - 1) * 100 / total)
            result = {"url": url, "success": False, "error": None}
            
            try:
                automator._update_progress(
                    progress_callback,
                    f"Processing project {i}/{total}: {url}",
                    progress
                )
                
                # Download the audio file and get notebook info
                success, msg, title, description = automator.download_audio(url, output_dir)
                if not success:
                    result["error"] = f"Failed to download audio: {msg}"
                    results.append(result)
                    continue
                    
                result["audio_file"] = msg
                result["success"] = True
                
                # If no title/description was retrieved, use defaults
                if not title:
                    title = f"NotebookLM Episode {i}"
                if not description:
                    description = f"Automatically generated episode from NotebookLM: {url}"
                
                # Upload to Spotify if requested
                if upload_to_spotify and success:
                    automator._update_progress(
                        progress_callback,
                        f"Uploading to Spotify: {title}",
                        progress + 50
                    )
                    
                    # Use the notebook's title and description for the podcast episode
                    spotify_success, spotify_msg = automator.upload_to_spotify(
                        audio_file_path=msg,
                        title=title,
                        description=description,
                        progress_callback=lambda m, p: automator._update_progress(
                            progress_callback, f"Spotify: {m}", progress + 50 + int(p * 0.5)
                        )
                    )
                    
                    result["spotify_upload"] = {"success": spotify_success, "message": spotify_msg}
                    result["spotify_title"] = title
                    result["spotify_description"] = description
                    
                    if not spotify_success:
                        result["error"] = f"Spotify upload failed: {spotify_msg}"
            
            except Exception as e:
                result["error"] = str(e)
                
            results.append(result)
    
    return results
