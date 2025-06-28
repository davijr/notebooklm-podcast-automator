import streamlit as st
import threading
from queue import Queue
from typing import Callable

from notebooklm_automator.core import NotebookLMAutomator
from notebooklm_automator.spotify import SpotifyAutomator

def main():
    """
    Main function for the Spotify Upload Streamlit app.
    """
    st.set_page_config(
        page_title="Spotify for Podcasters アップロード",
        page_icon="🎵",
        layout="wide"
    )

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
                
                success, message = upload_to_spotify(url, port, show_status=False)
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

        # Chrome launch instructions
        st.markdown("### How to Launch Chrome with Remote Debugging")
        st.code(f"/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=C:\\dev\\workspace_mygithub\\notebooklm-podcast-automator\\chrome-user-data --window-size=1280,800", language="bash")
        st.markdown("**Note:** Adjust the path for your operating system. The `--user-data-dir` parameter creates a separate Chrome profile for this automation. The `--window-size` parameter ensures proper display of NotebookLM's 3-column layout.")

        # Add a separator
        st.divider()

        # About section
        st.markdown("### About")
        st.markdown("""
        This is a Streamlit interface for uploading NotebookLM audio to Spotify for Podcasters.

        For more information, visit the [GitHub repository](https://github.com/upamune/notebooklm-podcast-automator).
        """)

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

def upload_to_spotify(notebook_url: str, port: int, show_status: bool = True) -> tuple[bool, str]:
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
        success, result = run_in_thread(_download_audio, notebook_url, port, log)
        if not success:
            return False, result
        
        success, (file_path, title, description) = result
        if not success:
            return False, f"Failed to download audio: {file_path}"
        
        # Spotifyへのアップロードを実行
        log("Uploading to Spotify for Podcasters...")
        success, result = run_in_thread(_upload_to_spotify, port, file_path, title, description)
        
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

def _download_audio(notebook_url: str, port: int, log: Callable[[str], None]) -> tuple[bool, tuple]:
    """Download audio from NotebookLM (runs in a separate thread)."""
    try:
        with NotebookLMAutomator(port) as automator:
            log("Downloading audio from NotebookLM...")
            success, file_path, title, description = automator.download_audio(notebook_url)
            if success:
                return True, (file_path, title, description)
            return False, (file_path, "", "")  # file_path contains error message
    except Exception as e:
        return False, (str(e), "", "")

def _upload_to_spotify(port: int, file_path: str, title: str, description: str) -> tuple[bool, str]:
    """Upload episode to Spotify (runs in a separate thread)."""
    try:
        with NotebookLMAutomator(port) as automator:
            spotify = SpotifyAutomator(automator.page)
            return spotify.upload_episode(file_path, title, description)
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    main()