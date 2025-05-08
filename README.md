# NotebookLM Automator

<img src="https://i.gyazo.com/0a9678c0bd80ac9577cbd2289885267d.png" width="500"/>

A Python tool that automates Google NotebookLM operations using Playwright and Chrome DevTools Protocol (CDP).

## Project Purpose and Features

NotebookLM Automator is designed to automate the following operations in Google NotebookLM:

- Creating new notebooks
- Adding website and YouTube URLs as sources to notebooks
- Starting Audio Overview (podcast) generation

This tool uses Playwright for browser automation and connects to an existing Chrome browser via Chrome DevTools Protocol (CDP). It is based on [DataNath/notebooklm_source_automation](https://github.com/DataNath/notebooklm_source_automation) with enhancements including improved authentication method, Audio Overview generation capability, and modernized project structure.

## Setup Instructions

### Requirements

- uv
- Python 3.9 or higher
- Chrome or Chromium browser

### Installation

1. **Install `uv`**

   Follow the official installation instructions at [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv) or install with pip:

   ```bash
   pip install uv
   ```

2. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd notebooklm-automator
   ```

3. **Create and activate a virtual environment**

   ```bash
   uv venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate    # Windows
   ```

4. **Install dependencies and the project in editable mode**

   ```bash
   uv pip install -e .
   ```

### Launching Chrome with Remote Debugging

**IMPORTANT**: Before running the script, you must launch Chrome/Chromium with remote debugging enabled.

**macOS**:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**Windows**:
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

**Linux**:
```bash
google-chrome --remote-debugging-port=9222
```

The default port is `9222`, but you can use a different port and specify it with the `-p` flag when running the automator.

## Execution Instructions

Ensure your virtual environment is activated and Chrome is running with remote debugging enabled.

### Using the Streamlit Interface (Recommended)

**The Streamlit interface is the recommended way to use this tool** as it provides a user-friendly experience with visual feedback on the automation progress.

```bash
streamlit run src/notebooklm_automator/streamlit_app.py
```

This will launch a web interface at http://localhost:8501 where you can:
- Enter URLs directly in a text area
- Upload a file containing URLs
- Configure the CDP port
- Monitor the automation progress with a visual interface and real-time logs
- See clear success/error messages with troubleshooting guidance

### Command-Line Usage

While the Streamlit interface is recommended for most users, the following command-line options are available for advanced users or automation scenarios.

#### With URL flag

```bash
run-automator -u "https://example.com,https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### With URLs from a file

```bash
run-automator urls.txt
```

The file should contain one URL per line.

#### With URLs from standard input (interactive mode)

```bash
run-automator
```

The script will prompt you to enter URLs one per line. After entering your URLs, press:
- **Ctrl+D** on Linux/macOS
- **Ctrl+Z followed by Enter** on Windows

You'll see confirmation of each URL as you enter it, making it easier to verify your input.

#### With URLs from Unix pipe

```bash
cat urls.txt | run-automator
echo -e "https://example.com\nhttps://example.org" | run-automator
```

#### Specifying a different CDP port

```bash
run-automator -p 9223 -u "https://example.com"
run-automator -p 9223 urls.txt
```

### Command-Line Arguments

- `file`: Optional file containing URLs (one per line).
- `-u, --urls URLS`: Comma-separated list of website or YouTube URLs.
- `-p, --port PORT`: CDP port for Chrome connection (default: 9222). Only change this if you started Chrome with a different remote debugging port.

If no file or URLs are provided, the script will read from standard input (either from a pipe or interactively).

## Notes and Caveats

- NotebookLM's UI is subject to change, which could break the Playwright selectors. Regular maintenance might be needed.
- The script initiates Audio Overview generation but does not wait for its completion.
