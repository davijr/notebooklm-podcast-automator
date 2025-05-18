import sys
import os

def get_urls(url_flag: str = None, file_path: str = None, use_jina_reader: bool = False) -> list:
    """
    Get a list of URLs from a comma-separated string, a file, or standard input.
    Optionally prepends Jina Reader API prefix to URLs.

    Args:
        url_flag: Optional comma-separated string of URLs.
        file_path: Optional path to a file containing URLs (one per line).
        use_jina_reader: If True, prepends "https://r.jina.ai/" to each URL.

    Returns:
        A list of URLs, potentially with Jina Reader API prefix.

    Raises:
        ValueError: If no valid URLs are provided.
        FileNotFoundError: If the specified file does not exist.
    """
    urls = []

    # Priority: 1. URL flag, 2. File path, 3. Standard input
    if url_flag:
        # Split comma-separated URLs and trim whitespace
        urls = [url.strip() for url in url_flag.split(',')]
    elif file_path:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read URLs from file (one per line)
        with open(file_path, 'r') as file:
            for line in file:
                url = line.strip()
                if url:  # Only add non-empty URLs
                    urls.append(url)

        print(f"Read {len(urls)} URLs from file: {file_path}")
    else:
        # Check if stdin has data (piped input) or is connected to a terminal (interactive mode)
        is_interactive = sys.stdin.isatty()

        if is_interactive:
            print("\n=== URL Input Mode ===")
            print("Enter URLs (one per line):")
            print("Press Ctrl+D (Linux/macOS) or Ctrl+Z followed by Enter (Windows) when finished")
            print("---------------------------")

        # Read URLs from standard input (one per line)
        url_count = 0
        for line in sys.stdin:
            url = line.strip()
            if url:  # Only add non-empty URLs
                urls.append(url)
                url_count += 1
                if is_interactive:
                    print(f"Added URL #{url_count}: {url}")

        if is_interactive and url_count > 0:
            print("---------------------------")
            print(f"Total URLs entered: {url_count}")

    # Remove empty URLs after trimming
    urls = [url for url in urls if url]

    # Raise error if no valid URLs are provided
    if not urls:
        raise ValueError("No URLs provided. Please provide at least one valid URL.")

    # Apply Jina Reader API prefix if enabled
    if use_jina_reader:
        jina_prefix = "https://r.jina.ai/"
        urls = [f"{jina_prefix}{url}" if not url.startswith(jina_prefix) else url for url in urls]
        print("Using Jina Reader API for URLs")

    return urls