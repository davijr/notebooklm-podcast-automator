import argparse
import sys
import time
from playwright.sync_api import Error as PlaywrightError

from notebooklm_automator.url_handler import get_urls
from notebooklm_automator.core import run_automation_with_urls

def run_automation():
    """
    Main function to automate NotebookLM operations.

    This function:
    1. Parses command-line arguments
    2. Connects to Chrome via CDP
    3. Gets URLs from command-line, file, or stdin
    4. Navigates to NotebookLM
    5. Adds link sources
    6. Generates audio overview
    7. Measures and prints execution time
    """
    start_time = time.perf_counter()

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Automate NotebookLM operations.")
    parser.add_argument(
        "file",
        nargs="?",
        help="Optional file containing URLs (one per line). If not provided, URLs will be read from standard input or the --urls flag."
    )
    parser.add_argument(
        "-u", "--urls",
        help="Comma-separated URLs to add as sources."
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=9222,
        help="Port for Chrome DevTools Protocol (CDP) connection (default: 9222)."
    )
    parser.add_argument(
        "-j", "--jina-reader",
        action="store_true",
        help="Use Jina Reader API by prepending 'https://r.jina.ai/' to URLs."
    )
    args = parser.parse_args()

    # Get URLs from command-line, file, or stdin
    try:
        # Determine input source and provide appropriate message
        if args.urls:
            input_source = "command line"
        elif args.file:
            input_source = f"file: {args.file}"
        else:
            input_source = "standard input"
            print("No URLs provided via command line or file. Waiting for input...")
            print("You can provide URLs by typing or pasting them below.")

        # Get URLs from the appropriate source
        urls_list = get_urls(args.urls, args.file, args.jina_reader)
        print(f"Processing {len(urls_list)} URLs from {input_source}")

    except ValueError as e:
        print(f"Error: {e}")
        print("Usage examples:")
        print("  uv run run-automator -u \"https://example.com,https://example.org\"")
        print("  uv run run-automator urls.txt")
        print("  cat urls.txt | uv run run-automator")
        print("  echo -e \"https://example.com\\nhttps://example.org\" | uv run run-automator")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Define a progress callback function
    def progress_callback(current_index, total_count, current_url):
        print(f"Processing URL {current_index+1}/{total_count}: {current_url}")

    # Run the automation with the collected URLs
    try:
        print(f"Connecting to Chrome on CDP port: {args.port}...")
        print("Navigating to NotebookLM...")

        # Use the core automation function
        run_automation_with_urls(urls_list, args.port, progress_callback)

        print("Finished adding sources.")
        print("Audio Overview generation completed.")

    except PlaywrightError as e:
        print(f"A Playwright error occurred: {e}")
        print("Please ensure Google Chrome is running with remote debugging enabled on the specified port.")
        print(f"Example command to launch Chrome: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={args.port} --user-data-dir=C:\\dev\\workspace_mygithub\\notebooklm-podcast-automator\\chrome-user-data --window-size=1280,800")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

    # Calculate and print execution time
    end_time = time.perf_counter()
    print(f"Script finished in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    run_automation()