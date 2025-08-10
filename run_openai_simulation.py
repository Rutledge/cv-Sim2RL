"""
This is a test script for the OpenAI help chat assistant.
It uses Scorecard to run a simulation of the chat assistant.

Install these dependencies (specific version of scorecard_ai):

$ pip install pytest-playwright
$ playwright install
$ pip install git+https://github.com/scorecard-ai/scorecard-python.git@multi-turn-simulation
$ # Run this script (the optional --headed flag shows the browser, otherwise it runs headless)
$ pytest run_geico_simulation.py --headed -s
"""

# pylint: disable=missing-function-docstring
import base64
import time
from typing import Any

from playwright.sync_api import Page
from scorecard_ai import Scorecard
from scorecard_ai.lib import ChatMessage, multi_turn_simulation, StopChecks


def open_chat_assistant_bubble(page: Page):
    # Wait for page to load and Intercom to initialize
    page.wait_for_timeout(3000)  # Wait for Intercom to load
    
    # Debug: Check what's on the page
    print(f"Number of iframes: {page.locator('iframe').count()}")
    print(f"Intercom container exists: {page.locator('#intercom-container').count() > 0}")
    
    # Try to click using JavaScript as a more reliable method
    try:
        # Method 1: Click the launcher icon element directly with JavaScript
        result = page.evaluate("""
            () => {
                // Look for the launcher icon element
                const launcher = document.querySelector('.launcher-default-open-icon');
                if (launcher) {
                    launcher.click();
                    return 'clicked launcher-default-open-icon';
                }
                
                // Try to find in Intercom container
                const intercomContainer = document.querySelector('#intercom-container');
                if (intercomContainer) {
                    // Find any clickable element within the Intercom container
                    const clickable = intercomContainer.querySelector('div[role="button"], button, .intercom-launcher-open-icon');
                    if (clickable) {
                        clickable.click();
                        return 'clicked element in intercom-container';
                    }
                }
                
                // Try to find the iframe and click inside it
                const iframe = document.querySelector('iframe#intercom-launcher-frame');
                if (iframe && iframe.contentWindow) {
                    // We can't directly access iframe content due to cross-origin, but we can try to click the iframe itself
                    iframe.click();
                    return 'clicked iframe';
                }
                
                // Look for any element with intercom and launcher in class
                const anyLauncher = document.querySelector('[class*="launcher"][class*="open"], [class*="intercom-launcher"]');
                if (anyLauncher) {
                    anyLauncher.click();
                    return 'clicked launcher element';
                }
                
                return 'no element found';
            }
        """)
        print(f"JavaScript click result: {result}")
        
        if result == 'no element found':
            # Fallback: Try using Playwright's force click on the container
            containers = page.locator("#intercom-container > div").all()
            if containers:
                containers[0].click(force=True)
                print("Force clicked first div in Intercom container")
    except Exception as e:
        print(f"Error clicking Intercom launcher: {e}")
        
        # Last resort: try to click by coordinates (bottom right corner)
        try:
            viewport = page.viewport_size
            if viewport:
                # Click in the bottom right corner where chat widgets usually are
                page.mouse.click(viewport['width'] - 50, viewport['height'] - 50)
                print("Clicked bottom right corner by coordinates")
        except Exception as e2:
            print(f"Could not click by coordinates: {e2}")


def click_messages_tab(page: Page):
    # Wait longer for the Intercom chat to fully open and settle
    page.wait_for_timeout(4000)
    
    # Click on the Messages tab using simple selectors first
    try:
        # Try the most direct approach - look for text "Messages"
        messages_tab = page.locator("text=Messages").first
        if messages_tab.count() > 0:
            # Add a small delay before clicking to appear more human-like
            page.wait_for_timeout(1500)
            messages_tab.click()
            print("Clicked Messages tab (text selector)")
            # Wait after clicking to let the interface respond
            page.wait_for_timeout(2000)
            return
    except:
        pass
        
    try:
        # Try in iframe with simple text selector
        iframe = page.frame_locator("iframe").first
        messages_tab = iframe.locator("text=Messages").first
        # Add delay before clicking
        page.wait_for_timeout(1500)
        messages_tab.click()
        print("Clicked Messages tab (iframe text selector)")
        # Wait after clicking
        page.wait_for_timeout(2000)
        return
    except:
        pass
        
    # Try JavaScript with simple text search
    try:
        result = page.evaluate("""
            () => {
                // Find all elements containing "Messages" text
                const allElements = document.querySelectorAll('*');
                for (let element of allElements) {
                    if (element.textContent && element.textContent.trim() === 'Messages') {
                        element.click();
                        return 'clicked element with Messages text';
                    }
                }
                return 'no Messages text found';
            }
        """)
        print(f"Messages tab JavaScript result: {result}")
    except Exception as e:
        print(f"Could not click Messages tab: {e}")


def fill_in_info_form(page: Page):
    # Wait for the Intercom form to appear
    page.wait_for_timeout(2000)
    
    # Fill in any required fields in Intercom if they appear
    try:
        iframe = page.frame_locator("iframe[title*='Intercom'], iframe[name*='intercom']")
        if iframe.locator("input[type='email']").count() > 0:
            iframe.locator("input[type='email']").fill("john.doe@example.com")
        if iframe.locator("input[name='name']").count() > 0:
            iframe.locator("input[name='name']").fill("John Doe")
    except:
        pass  # Form might not be required


def wait_for_chat_assistant_to_load(page: Page):
    # Wait for the Intercom chat interface to load
    page.wait_for_timeout(3000)
    # Look for Intercom's chat input field
    try:
        # Intercom chat is usually in an iframe
        iframe = page.frame_locator("iframe[title*='Intercom'], iframe[name*='intercom']")
        iframe.locator("textarea, [contenteditable='true']").wait_for(timeout=5000)
    except:
        page.wait_for_timeout(2000)


def take_chat_screenshot(page: Page) -> str | None:
    """Take a screenshot of the chat container."""
    try:
        # Try to find the Intercom chat container
        chat_container = page.locator("iframe[title*='Intercom'], iframe[name*='intercom'], #intercom-container").first
        if chat_container.count() > 0:
            # Create a timestamp-based filename
            timestamp = int(time.time())
            screenshot_path = f"chat_screenshot_{timestamp}.png"

            # Take screenshot and save to file
            screenshot_bytes = chat_container.screenshot(path=screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")

            return "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode(
                "utf-8"
            )
    except (TimeoutError, ValueError, OSError) as e:
        print(f"Could not take screenshot: {e}")
    return None


def wait_for_assistant_message(
    page: Page, *, seen_count: int, seconds: int = 8
) -> tuple[list[str], str | None]:
    page.wait_for_timeout(seconds * 1000)

    # Try to find Intercom assistant messages
    try:
        # Intercom messages are usually in an iframe
        iframe = page.frame_locator("iframe[title*='Intercom'], iframe[name*='intercom']")
        all_assistant_messages = iframe.locator(".intercom-comment, [data-testid*='message']").all()
    except:
        all_assistant_messages = page.locator(".intercom-comment, [data-testid*='message']").all()
    # Only messages that are new (after seen_count index)
    new_messages: list[str] = []
    for message in all_assistant_messages[seen_count:]:
        # Check if this message contains rich menu buttons
        buttons = message.locator(".rich-menu button").all()
        if buttons:
            # Format buttons as HTML-like strings
            button_texts = [f"<button>{btn.text_content()}</button>" for btn in buttons]
            content = "\n".join(button_texts)
        else:
            # Regular text message
            content = message.text_content() or ""

        if content:
            new_messages.append(content)

    if len(new_messages) == 0:
        new_messages.append("(timeout)")

    # Take a screenshot
    return new_messages, take_chat_screenshot(page)


def send_message(page: Page, message: str) -> str | None:
    # Find the Intercom chat input field
    try:
        # Intercom chat is usually in an iframe
        iframe = page.frame_locator("iframe[title*='Intercom'], iframe[name*='intercom']")
        chat_input = iframe.locator("textarea, [contenteditable='true']").first
        chat_input.fill(message)
        chat_input.press("Enter")
    except:
        # Fallback to direct selector if not in iframe
        chat_input = page.locator("textarea, [contenteditable='true']").first
        chat_input.fill(message)
        chat_input.press("Enter")
    
    print(f"Sent message: {message}")
    return take_chat_screenshot(page)


def customer_service_assistant(
    page: Page, *, seen_count: int, chat_history: list[ChatMessage]
) -> tuple[list[str], str | None]:
    # Get any simulated user messages from chat history
    # Then send them as user messages to the real assistant
    if len(chat_history) > 0 and chat_history[-1]["role"] == "user":
        image_data = send_message(page, chat_history[-1]["content"])
        chat_history[-1]["image"] = image_data

    new_assistant_messages, image_data = wait_for_assistant_message(
        page, seen_count=seen_count
    )
    print("Got assistant messages:", new_assistant_messages)
    return new_assistant_messages, image_data


def reset_page(page: Page):
    # Clear all cookies first
    page.context.clear_cookies()

    # Navigate to about:blank to completely leave the page
    page.goto("about:blank")
    page.wait_for_timeout(500)

    # Navigate to the page with cache disabled
    page.goto("https://help.openai.com/en/collections/3742473-chatgpt", wait_until="networkidle")

    # Clear any storage that might have been set on load
    try:
        page.evaluate("localStorage.clear()")
        page.evaluate("sessionStorage.clear()")
    except (TimeoutError, ValueError):
        pass  # Storage might not be accessible

    # Delete all cookies again after page load
    page.context.clear_cookies()


def test_openai_assistant(page: Page):
    current_context = None
    current_page: Page | None = None
    seen_count: int = 0

    def before_each_simulation(testcase: dict) -> list[ChatMessage]:
        nonlocal seen_count, current_context, current_page

        # Close previous context if it exists
        if current_context:
            if current_page:
                current_page.close()
            current_context.close()

        # Create a new browser context and page for complete isolation
        browser = page.context.browser
        if browser is None:
            raise RuntimeError("Browser is not available")
        current_context = browser.new_context()
        current_page = current_context.new_page()

        seen_count = 0
        print(f"Starting new testcase with fresh browser context: {testcase}")

        # Start the test with the new isolated page
        current_page.goto("https://help.openai.com/en/collections/3742473-chatgpt")
        open_chat_assistant_bubble(current_page)
        print("Opened chat assistant bubble")
        # Wait longer to avoid bot detection that triggers a few seconds after opening
        current_page.wait_for_timeout(8000)
        click_messages_tab(current_page)
        print("Clicked Messages tab")
        fill_in_info_form(current_page)
        print("Filled in info form (if needed)")
        wait_for_chat_assistant_to_load(current_page)

        initial_assistant_messages, image_data = wait_for_assistant_message(
            current_page, seen_count=0
        )
        print("Got initial assistant messages:", initial_assistant_messages)
        seen_count = len(initial_assistant_messages)
        return [
            ChatMessage(
                role="assistant",
                content="\n\n".join(initial_assistant_messages),
                image=image_data,
            )
        ]

    def system(
        chat_history: list[ChatMessage], _: dict[str, Any]
    ) -> list[str] | list[ChatMessage]:
        nonlocal seen_count, current_page
        if current_page is None:
            raise RuntimeError("Page is not initialized")
        new_assistant_messages, image_data = customer_service_assistant(
            current_page, seen_count=seen_count, chat_history=chat_history
        )
        seen_count += len(new_assistant_messages)
        return [
            ChatMessage(
                role="assistant",
                content="\n\n".join(new_assistant_messages),
                image=image_data,
            )
        ]

    # scorecard = Scorecard(
    #     environment="local", api_key="ak_TS5WN8EKKW3DF3HWKX638P1XMN7S39B9"
    # )
    scorecard = Scorecard(
        environment="staging", api_key="ak_PSZNFJ0X2DXX095JA52SRDV8MMCQFDGN"
    )

    simulation_run = multi_turn_simulation(
        client=scorecard,
        # Production:
        # project_id="421",
        # # metric_ids=["1207", "1208", "1209"],
        # metric_ids=[],
        # testset_id="13431",
        # sim_agent_id="678a73e2-0ae3-4a48-8dc9-7a24ba823ed3",
        # Staging:
        project_id="203",
        metric_ids=[],
        testset_id="17856",
        sim_agent_id="7db3e1e5-729c-4a76-a024-6203fdd6209a",
        #
        system=system,
        initial_messages=before_each_simulation,
        stop_check=StopChecks.any(
            [StopChecks.max_turns(3), StopChecks.content(["timeout"])]
        ),
    )

    print(simulation_run)