import streamlit as st
import sys
from io import StringIO
from playwright.sync_api import Error as PlaywrightError

from notebooklm_automator.url_handler import get_urls
from notebooklm_automator.core import NotebookLMAutomator

def main():
    """
    Main function for the NotebookLM Streamlit app.
    """
    st.set_page_config(
        page_title="NotebookLM Podcast Automator",
        page_icon="🎙️",
        layout="wide"
    )

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
        process_notebooklm_urls(urls_text, port, use_jina_reader)

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

        # Chrome launch instructions
        st.markdown("### How to Launch Chrome with Remote Debugging")
        st.code(f"/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=C:\\dev\\workspace_mygithub\\notebooklm-podcast-automator\\chrome-user-data --window-size=1280,800", language="bash")
        st.markdown("**Note:** Adjust the path for your operating system. The `--user-data-dir` parameter creates a separate Chrome profile for this automation. The `--window-size` parameter ensures proper display of NotebookLM's 3-column layout.")

        # Add a separator
        st.divider()

        # About section
        st.markdown("### About")
        st.markdown("""
        This is a Streamlit interface for the NotebookLM Podcast Automator.

        For more information, visit the [GitHub repository](https://github.com/upamune/notebooklm-podcast-automator).
        """)

def process_notebooklm_urls(urls_text: str, port: int, use_jina_reader: bool) -> None:
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
        with NotebookLMAutomator(port) as automator:
            try:
                # Connect to Chrome and navigate to NotebookLM
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
                print(f"Example command to launch Chrome: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=C:\\dev\\workspace_mygithub\\notebooklm-podcast-automator\\chrome-user-data --window-size=1280,800")
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


if __name__ == "__main__":
    main()