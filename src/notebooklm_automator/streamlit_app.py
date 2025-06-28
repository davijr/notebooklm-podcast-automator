import streamlit as st
import sys
import time
from io import StringIO
from typing import List, Optional, Callable
from playwright.sync_api import Error as PlaywrightError

from notebooklm_automator.url_handler import get_urls
from notebooklm_automator.core import NotebookLMAutomator
from notebooklm_automator.spotify import SpotifyAutomator

def main():
    """
    Main function for the Streamlit app.
    """
    st.set_page_config(
        page_title="NotebookLM Podcast Automator",
        page_icon="🎙️",
        layout="wide"
    )

    # タブを作成
    tab1, tab2 = st.tabs(["NotebookLM オーディオ生成", "Spotify アップロード"])

    with tab1:
        st.title("NotebookLM Podcast Automator")
        st.markdown("""
        This tool automates the process of creating podcasts in Google NotebookLM by:
        1. Creating a new notebook
        2. Adding website and YouTube URLs as sources
        3. Generating an Audio Overview (podcast)

        **Note:** You must have Chrome running with remote debugging enabled.
        """)

        # メインコンテンツ
        st.header("Add URLs")
        urls_text = st.text_area(
            "Enter URLs (one per line)",
            height=200,
            help="Enter website or YouTube URLs, one per line.",
            placeholder="https://example.com\nhttps://www.youtube.com/watch?v=dQw4w9WgXcQ",
            key="notebooklm_urls"
        )

        # Run button for NotebookLM
        if st.button("Run Automation", type="primary", key="run_automation"):
            port = st.session_state.get('port', 9222)
            use_jina_reader = st.session_state.get('use_jina_reader', False)
            use_playwright_chromium = st.session_state.get('use_playwright_chromium', False)
            process_notebooklm_urls(urls_text, port, use_jina_reader, use_playwright_chromium)

    with tab2:
        st.title("Spotify for Podcasters アップロード")
        st.markdown("""
        This tool helps you upload your NotebookLM audio to Spotify for Podcasters.
        1. Enter the URLs of your NotebookLM projects (one per line)
        2. The audios will be downloaded and uploaded to Spotify for Podcasters
        """)
        
        # Spotify アップロード用のフォーム
        notebook_urls = st.text_area(
            "NotebookLM Project URLs (one per line)",
            height=200,
            help="Enter the URLs of your NotebookLM projects, one per line.",
            placeholder="https://notebooklm.google.com/...\nhttps://notebooklm.google.com/...",
            key="spotify_notebook_urls"
        )
        
        # Upload to Spotify button
        if st.button("Upload to Spotify", type="primary", key="upload_spotify"):
            urls = [url.strip() for url in notebook_urls.split('\n') if url.strip()]
            if not urls:
                st.error("Please enter at least one valid NotebookLM project URL.")
            else:
                port = st.session_state.get('port', 9222)
                use_playwright_chromium = st.session_state.get('use_playwright_chromium', False)
                results = []
                
                # Create columns for progress display
                progress_col, status_col = st.columns([1, 4])
                
                with progress_col:
                    st.write("Progress:")
                    progress_bar = st.progress(0)
                
                with status_col:
                    status_text = st.empty()
                
                for i, url in enumerate(urls, 1):
                    progress = i / len(urls)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {i}/{len(urls)}: {url[:50]}...")
                    
                    success, message = upload_to_spotify(url, port, use_playwright_chromium, show_status=False)
                    results.append((url, success, message))
                    
                    # Update status
                    status_text.text(f"Processed {i}/{len(urls)}: {url[:50]}...")
                
                # Show final results
                progress_bar.empty()
                status_text.empty()
                
                st.subheader("Upload Results")
                for url, success, message in results:
                    if success:
                        st.success(f"✅ {url[:50]}...: {message}")
                    else:
                        st.error(f"❌ {url[:50]}...: {message}")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # CDP port input
        port = st.number_input(
            "Chrome DevTools Protocol (CDP) Port",
            min_value=1,
            max_value=65535,
            value=9222,
            help="Port for Chrome DevTools Protocol connection. Only change if you started Chrome with a different remote debugging port.",
            key="port"
        )

        # Jina Reader option
        use_jina_reader = st.checkbox(
            "Use Jina Reader API",
            value=True,
            help="If checked, prepends 'https://r.jina.ai/' to URLs to use Jina Reader API for better content extraction.",
            key="use_jina_reader"
        )

        # Playwright Chromium option
        use_playwright_chromium = st.checkbox(
            "Use Playwright Chromium",
            value=False,
            help="If checked, uses Playwright's built-in Chromium instead of connecting to external Chrome. Useful if you have trouble launching Chrome with debugging.",
            key="use_playwright_chromium"
        )

        # Chrome launch instructions
        st.markdown("### How to Launch Chrome with Remote Debugging")
        st.code(f"/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=./chrome-user-data --window-size=1280,800", language="bash")
        st.markdown("**Note:** Adjust the path for your operating system. The `--user-data-dir` parameter creates a separate Chrome profile for this automation. The `--window-size` parameter ensures proper display of NotebookLM's 3-column layout.")

        # Add a separator
        st.divider()

        # About section
        st.markdown("### About")
        st.markdown("""
        This is a Streamlit interface for the NotebookLM Podcast Automator.

        For more information, visit the [GitHub repository](https://github.com/upamune/notebooklm-podcast-automator).
        """)

def process_notebooklm_urls(urls_text: str, port: int, use_jina_reader: bool, use_playwright_chromium: bool = False) -> None:
    """Process URLs with NotebookLM and generate audio."""
    # Process URLs from text area
    raw_urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
    if not raw_urls:
        st.error("No valid URLs provided in the text area.")
        return

    # Apply Jina Reader if enabled
    urls_list = get_urls(url_flag=",".join(raw_urls), use_jina_reader=use_jina_reader)
    
    # Display the URLs that will be processed
    st.success(f"Processing {len(urls_list)} URLs:")
    for i, url in enumerate(urls_list, 1):
        st.markdown(f"{i}. `{url}`")

    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Create a placeholder for logs
    log_container = st.container()
    with log_container:
        log_output = st.empty()

    # Capture logs
    log_capture = StringIO()

    # Redirect stdout to capture logs
    original_stdout = sys.stdout
    sys.stdout = log_capture

    try:
        status_text.write("Connecting to Chrome...")

        # Define a progress callback function for Streamlit
        def streamlit_progress_callback(current_index: int, total_count: int, current_url: str) -> None:
            current_url_status = f"Processing URL {current_index+1}/{total_count}: {current_url}"
            status_text.write(current_url_status)
            print(current_url_status)
            log_output.text(log_capture.getvalue())

            # Update progress bar
            progress = (current_index + 1) / total_count
            progress_bar.progress(progress)
            log_output.text(log_capture.getvalue())

        print(f"Connecting to Chrome on CDP port: {port}...")
        status_text.write("Connecting to Chrome...")
        log_output.text(log_capture.getvalue())

        # Use the core automator class
        with NotebookLMAutomator(port, use_playwright_chromium) as automator:
            try:
                # Connection happens automatically in __enter__
                print("Successfully connected to Chrome and navigated to NotebookLM.")
                status_text.write("Successfully connected to NotebookLM...")
                log_output.text(log_capture.getvalue())

                # Process URLs
                print(f"Adding {len(urls_list)} URLs as sources...")
                status_text.write(f"Adding {len(urls_list)} URLs as sources...")
                log_output.text(log_capture.getvalue())

                automator.process_urls(urls_list, streamlit_progress_callback)

                print("Finished adding sources.")
                log_output.text(log_capture.getvalue())

                # Generate audio overview
                print("Generating Audio Overview...")
                status_text.write("Generating Audio Overview...")
                log_output.text(log_capture.getvalue())

                automator.generate_audio()

                print("Audio Overview generation completed.")
                log_output.text(log_capture.getvalue())
                
                # Complete the progress bar
                progress_bar.progress(1.0)
                status_text.write("✅ Automation completed successfully!")
                log_output.text(log_capture.getvalue())

            except PlaywrightError as e:
                error_msg = f"A Playwright error occurred: {e}"
                print(error_msg)
                print("Please ensure Google Chrome is running with remote debugging enabled on the specified port.")
                print(f"Example command to launch Chrome: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=./chrome-user-data --window-size=1280,800")
                log_output.text(log_capture.getvalue())
                status_text.write(f"❌ {error_msg}")
            except Exception as e:
                error_msg = f"An unexpected error occurred: {e}"
                print(error_msg)
                log_output.text(log_capture.getvalue())
                status_text.write(f"❌ {error_msg}")

    except Exception as e:
        error_msg = f"Error: {e}"
        print(error_msg)
        log_output.text(log_capture.getvalue())
        status_text.write(f"❌ {error_msg}")

    finally:
        # Restore stdout
        sys.stdout = original_stdout


def run_in_thread(func, *args, **kwargs):
    """
    Run a function in a separate thread and return its result.
    
    Args:
        func: The function to run
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        tuple: (success: bool, result: Any or error_message: str)
    """
    import threading
    from queue import Queue
    
    def wrapper(q, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            q.put((True, result))
        except Exception as e:
            q.put((False, str(e)))
    
    q = Queue()
    thread = threading.Thread(target=wrapper, args=(q,) + args, kwargs=kwargs)
    thread.daemon = True  # メインプロセス終了時にスレッドも終了するようにする
    thread.start()
    thread.join(timeout=300)  # 5分のタイムアウト
    
    if thread.is_alive():
        return False, "Operation timed out after 5 minutes"
    
    if q.empty():
        return False, "Operation failed with no error message"
    
    return q.get()

def upload_to_spotify(notebook_url: str, port: int, use_playwright_chromium: bool = False, show_status: bool = True) -> tuple[bool, str]:
    """
    Upload audio from a single NotebookLM project to Spotify for Podcasters.
    
    Args:
        notebook_url: URL of the NotebookLM project
        port: Chrome DevTools Protocol port
        show_status: Whether to show status updates in the UI
        
    Returns:
        tuple: (success: bool, message: str)
    """
    def log(message: str) -> None:
        """Log a message to the console and optionally to the UI."""
        print(message)
        if show_status:
            st.write(message)
    
    try:
        log(f"Processing: {notebook_url}")
        log("Connecting to Chrome...")
        
        # NotebookLMからのオーディオダウンロードを実行
        success, result = run_in_thread(_download_audio, notebook_url, port, use_playwright_chromium, log)
        if not success:
            return False, result
        
        success, (file_path, title, description) = result
        if not success:
            return False, f"Failed to download audio: {file_path}"
        
        # Spotifyへのアップロードを実行
        log("Uploading to Spotify for Podcasters...")
        success, result = run_in_thread(_upload_to_spotify, port, use_playwright_chromium, file_path, title, description)
        
        if not success:
            return False, f"Failed to upload to Spotify: {result}"
            
        success, message = result
        if success:
            log(f"Successfully uploaded: {title}")
            if show_status:
                st.balloons()
            return True, message
        else:
            error_msg = f"Failed to upload {title} to Spotify: {message}"
            log(error_msg)
            return False, error_msg
    
    except Exception as e:
        error_msg = f"An error occurred while processing {notebook_url}: {str(e)}"
        log(error_msg)
        return False, error_msg

def _download_audio(notebook_url: str, port: int, use_playwright_chromium: bool, log) -> tuple[bool, tuple]:
    """Download audio from NotebookLM (runs in a separate thread)."""
    try:
        with NotebookLMAutomator(port, use_playwright_chromium) as automator:
            log("Downloading audio from NotebookLM...")
            success, file_path, title, description = automator.download_audio(notebook_url)
            if success:
                return True, (file_path, title, description)
            return False, (file_path, "", "")  # file_path contains error message
    except Exception as e:
        return False, (str(e), "", "")

def _upload_to_spotify(port: int, use_playwright_chromium: bool, file_path: str, title: str, description: str) -> tuple[bool, str]:
    """Upload episode to Spotify (runs in a separate thread)."""
    try:
        with NotebookLMAutomator(port, use_playwright_chromium) as automator:
            spotify = SpotifyAutomator(automator.page)
            return spotify.upload_episode(file_path, title, description)
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    main()
