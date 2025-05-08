from playwright.sync_api import Page, expect
import time

def detect_ui_language(page: Page) -> str:
    """
    Detect the UI language of NotebookLM (English or Japanese).

    Args:
        page: Playwright page object representing the NotebookLM page.

    Returns:
        Language code: "ja" for Japanese or "en" for English (default).
    """
    # Get the lang attribute of the <html> tag
    lang = page.evaluate("document.documentElement.lang") or "en"

    # Determine the language based on the lang attribute (default is English)
    if lang.startswith("ja"):
        return "ja"
    return "en"  # Return English as default

def get_ui_text_map() -> dict:
    """
    Return a mapping of UI text in different languages.

    Returns:
        Dictionary containing UI text mappings for English and Japanese.
    """
    return {
        "create_notebook": {
            "en": "Create new notebook",
            "ja": "新規作成"
        },
        "add_source": {
            "en": "Add source",
            "ja": "ソースを追加"
        },
        "website": {
            "en": "Website",
            "ja": "ウェブサイト"
        },
        "youtube": {
            "en": "YouTube",
            "ja": "YouTube"
        },
        "insert": {
            "en": "Insert",
            "ja": "挿入"
        },
        "generate": {
            "en": "Generate",
            "ja": "生成"
        },
    }

def add_link_sources(urls: list, page: Page, progress_callback=None) -> None:
    """
    Add multiple URL sources to a NotebookLM notebook.

    Args:
        urls: List of URLs to add as sources.
        page: Playwright page object representing the NotebookLM page.
        progress_callback: Optional callback function to report progress.
                          Called with (current_index, total_count, current_url).
    """
    # Detect UI language and get text mappings
    lang = detect_ui_language(page)
    ui_text = get_ui_text_map()

    # Process each URL in the list
    for index, url in enumerate(urls):
        try:
            # Report progress if callback is provided
            if progress_callback:
                progress_callback(index, len(urls), url)

            # Different behavior for first URL vs subsequent URLs
            if index == 0:
                # For the first URL, create a new notebook
                create_notebook_text = ui_text["create_notebook"][lang]
                create_button = page.get_by_role("button", name=create_notebook_text)
                create_button.wait_for(state="attached")
                expect(create_button).to_be_enabled()
                create_button.click()
            else:
                # For subsequent URLs, add a source
                add_source_text = ui_text["add_source"][lang]
                add_source_button = page.get_by_role("button", name=add_source_text)
                add_source_button.wait_for(state="attached")
                expect(add_source_button).to_be_enabled()
                add_source_button.click()

            # Wait for source selection dialog to appear
            time.sleep(1)  # Brief wait for UI to update

            # Determine source type based on URL
            if "youtube.com" in url or "youtu.be" in url:
                source_type_text = ui_text["youtube"][lang]
            else:
                source_type_text = ui_text["website"][lang]

            # Click on the appropriate source type chip
            source_type_chip = page.locator("span.mdc-evolution-chip__text-label", has_text=source_type_text)
            source_type_chip.wait_for(state="attached")
            source_type_chip.click()

            # Fill in the URL
            url_input = page.locator("[formcontrolname='newUrl']")
            url_input.wait_for(state="attached")
            expect(url_input).to_be_enabled()
            url_input.fill(url)

            # Click the Insert button
            insert_text = ui_text["insert"][lang]
            insert_button = page.get_by_role("button", name=insert_text)
            insert_button.wait_for(state="attached")
            expect(insert_button).to_be_enabled()
            insert_button.click()

            time.sleep(2)

            # Wait for loading to complete (spinner to disappear)
            spinner = page.locator(".mat-progress-spinner")
            if spinner.count() > 0:
                spinner.wait_for(state="detached", timeout=30000)

            # Brief wait before proceeding to next URL
            time.sleep(2)

        except Exception as e:
            print(f"Error adding source {url}: {str(e)}")

def generate_audio_overview(page: Page) -> None:
    """
    Initiate Audio Overview generation for the current notebook.

    Args:
        page: Playwright page object representing the NotebookLM page.
    """
    try:
        # Detect UI language and get text mappings
        lang = detect_ui_language(page)
        ui_text = get_ui_text_map()

        # Get language-specific text for Audio Overview and Generate button
        generate_text = ui_text["generate"][lang]

        # Find and click the Generate button within the Audio Overview section
        generate_button = page.get_by_role("button", name=generate_text)
        expect(generate_button).to_be_enabled()
        generate_button.click()

        # Optional: Confirm UI changes indicating generation has started
        # For example, button might be disabled after clicking
        try:
            expect(generate_button).to_be_disabled(timeout=2000)
            print("Audio Overview generation started: Generate button is now disabled.")
        except:
            # If we can't confirm the button is disabled, just continue
            print("Audio Overview generation started.")

    except Exception as e:
        print(f"Error generating Audio Overview: {str(e)}")
        print("Continuing with the rest of the process...")