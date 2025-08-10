"""
This is a test script for the Alaska Airlines chat assistant.
It uses Scorecard to run a simulation of the chat assistant.

Install these dependencies (specific version of scorecard_ai):

$ pip install pytest-playwright
$ playwright install
$ pip install git+https://github.com/scorecard-ai/scorecard-python.git@multi-turn-simulation
$ # Run this script (the optional --headed flag shows the browser, otherwise it runs headless)
$ pytest run_alaska_simulation.py --headed -s
"""

# pylint: disable=missing-function-docstring
import base64
import os
import time
from typing import Any

from playwright.sync_api import Page
from scorecard_ai import Scorecard
from scorecard_ai.lib import ChatMessage, multi_turn_simulation, StopChecks
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def open_chat_assistant_bubble(page: Page):
    # Wait for page to load and potentially for chat to initialize
    page.wait_for_timeout(1000)

    # Look for "Try Ask Alaska" button by ID first
    try:
        try_ask_alaska_btn = page.locator("#try-ask-alaska-btn")
        if try_ask_alaska_btn.count() > 0:
            try_ask_alaska_btn.click()
            print("Clicked 'Try Ask Alaska' button by ID")
            return
    except:
        pass
    
    # Fallback to text-based selectors
    try:
        ask_alaska_btn = page.locator("text=Ask Alaska").first
        if ask_alaska_btn.count() > 0:
            ask_alaska_btn.click()
            print("Clicked 'Ask Alaska' button")
            return
    except:
        pass
    
    # Try "Try Ask Alaska" button by text
    try:
        try_ask_alaska_btn = page.locator("text=Try Ask Alaska").first
        if try_ask_alaska_btn.count() > 0:
            try_ask_alaska_btn.click()
            print("Clicked 'Try Ask Alaska' button by text")
            return
    except:
        pass
    
    # Look for other Alaska Airlines chat bubble or button
    # Try common chat selectors
    selectors = [
        ".chat-launcher",
        ".chat-widget", 
        ".chat-button",
        ".support-chat",
        "#chat-widget",
        "[data-testid*='chat']",
        ".live-chat",
        ".help-chat"
    ]
    
    for selector in selectors:
        bubble_count = page.locator(selector).count()
        if bubble_count > 0:
            try:
                page.locator(selector).click(force=True)
                print(f"Clicked chat button with selector: {selector}")
                return
            except:
                continue
    
    # If no specific chat button found, try clicking any visible chat-related text
    try:
        chat_text = page.locator("text=Chat").first
        if chat_text.count() > 0:
            chat_text.click()
            print("Clicked 'Chat' text")
    except:
        print("Could not find chat button")


def fill_in_info_form(page: Page):
    # Wait for any form to appear
    page.wait_for_timeout(1000)
    
    # Fill in common form fields if they exist
    try:
        if page.locator("input[name='firstName'], input[name='first_name'], input.FirstName").count() > 0:
            page.locator("input[name='firstName'], input[name='first_name'], input.FirstName").first.fill("John")
        
        if page.locator("input[name='lastName'], input[name='last_name'], input.LastName").count() > 0:
            page.locator("input[name='lastName'], input[name='last_name'], input.LastName").first.fill("Doe")
        
        if page.locator("input[type='email'], input[name='email'], input.Email").count() > 0:
            page.locator("input[type='email'], input[name='email'], input.Email").first.fill("john.doe@example.com")
        
        # Look for submit button
        submit_selectors = [
            "button[type='submit']",
            ".submit-button",
            "button:has-text('Submit')",
            "button:has-text('Start')",
            "button:has-text('Continue')"
        ]
        
        for selector in submit_selectors:
            if page.locator(selector).count() > 0:
                page.locator(selector).first.click()
                break
                
    except Exception as e:
        print(f"Form filling error: {e}")


def wait_for_chat_assistant_to_load(page: Page):
    # Wait for chat interface to load
    page.wait_for_timeout(500)
    
    # Look for chat input or message area
    chat_selectors = [
        "textarea",
        "input[type='text']",
        ".chat-input",
        "[contenteditable='true']",
        ".message-input"
    ]
    
    for selector in chat_selectors:
        try:
            page.wait_for_selector(selector, timeout=3000)
            print(f"Chat loaded, found input: {selector}")
            return
        except:
            continue
    
    print("Chat interface may not have loaded properly")


def take_chat_screenshot(page: Page) -> str | None:
    """Take a screenshot of just the chat widget."""
    try:
        # First, try to find the actual chat widget element by inspecting what's visible
        print("Looking for chat widget elements...")
        
        # Try to find elements that look like chat widgets
        chat_selectors = [
            "[id*='chat']",
            "[class*='chat']",
            "[data-testid*='chat']",
            "iframe[src*='chat']",
            "div[role='dialog']",
            ".modal",
            "[aria-label*='chat']"
        ]
        
        for selector in chat_selectors:
            elements = page.locator(selector).all()
            for element in elements:
                if element.is_visible():
                    try:
                        timestamp = int(time.time())
                        screenshot_path = f"chat_screenshot_{timestamp}.png"
                        screenshot_bytes = element.screenshot(path=screenshot_path)
                        print(f"Chat element screenshot saved: {screenshot_path} using selector: {selector}")
                        return "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode("utf-8")
                    except:
                        continue
        
        # If no specific chat widget found, take a more targeted crop
        timestamp = int(time.time())
        screenshot_path = f"chat_screenshot_{timestamp}.png"
        
        # Take full page screenshot
        full_screenshot = page.screenshot()
        
        from PIL import Image
        import io
        
        # Load the full screenshot
        img = Image.open(io.BytesIO(full_screenshot))
        width, height = img.size
        
        # Based on typical chat widget placement, crop a more specific area
        # Usually chat widgets are in the bottom right, taking about 350-400px width
        chat_width = 380
        chat_height = min(600, height - 100)  # Leave some margin at top
        
        # Position: bottom right corner with some padding
        left = width - chat_width - 20  # 20px padding from right edge
        top = height - chat_height - 20   # 20px padding from bottom
        right = width - 20
        bottom = height - 20
        
        # Ensure bounds are valid
        left = max(0, left)
        top = max(0, top)
        
        # Crop the image to the chat area
        chat_img = img.crop((left, top, right, bottom))
        
        # Save the cropped image
        chat_img.save(screenshot_path)
        
        # Convert to base64
        buffer = io.BytesIO()
        chat_img.save(buffer, format='PNG')
        screenshot_bytes = buffer.getvalue()
        
        print(f"Targeted crop chat screenshot saved: {screenshot_path}")
        return "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode("utf-8")
        
    except Exception as e:
        print(f"Could not take screenshot: {e}")
        # Final fallback: full page screenshot
        try:
            timestamp = int(time.time())
            screenshot_path = f"chat_screenshot_{timestamp}.png"
            screenshot_bytes = page.screenshot(path=screenshot_path)
            return "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode("utf-8")
        except:
            pass
    return None


def wait_for_assistant_message(
    page: Page, *, seen_count: int, seconds: int = 4
) -> tuple[list[str], str | None]:
    page.wait_for_timeout(seconds * 1000)

    # Look for assistant/bot messages with various selectors
    message_selectors = [
        ".bot-message",
        ".assistant-message", 
        ".chat-message.bot",
        ".message.agent",
        ".support-message",
        "[data-role='assistant']",
        ".chat-bubble.bot"
    ]
    
    all_assistant_messages = []
    for selector in message_selectors:
        messages = page.locator(selector).all()
        if messages:
            all_assistant_messages = messages
            break
    
    # If no specific bot messages found, try generic message selectors
    if not all_assistant_messages:
        all_assistant_messages = page.locator(".message, .chat-message").all()
    
    # Only messages that are new (after seen_count index)
    new_messages: list[str] = []
    for message in all_assistant_messages[seen_count:]:
        # Check if this message contains buttons
        buttons = message.locator("button").all()
        if buttons:
            # Format buttons as HTML-like strings
            button_texts = [f"<button>{btn.text_content()}</button>" for btn in buttons]
            content = "\n".join(button_texts)
        else:
            # Regular text message
            content = message.text_content() or ""

        if content and content.strip():
            new_messages.append(content.strip())

    if len(new_messages) == 0:
        new_messages.append("(timeout)")

    # Take a screenshot
    return new_messages, take_chat_screenshot(page)


def send_message(page: Page, message: str) -> str | None:
    # Find chat input with various selectors
    input_selectors = [
        "textarea",
        "input[type='text']",
        ".chat-input",
        "[contenteditable='true']",
        ".message-input",
        "#message-input"
    ]
    
    for selector in input_selectors:
        try:
            chat_input = page.locator(selector).first
            if chat_input.count() > 0:
                chat_input.fill(message)
                chat_input.press("Enter")
                print(f"Sent message: {message}")
                return take_chat_screenshot(page)
        except:
            continue
    
    print(f"Could not send message: {message}")
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

    # Navigate to the Alaska Airlines page
    page.goto("https://www.alaskaair.com/content/about-us/help-contact?fb1234&fb1234&fb1234&srsltid=AfmBOopecxxT98bV2I8TW6wIannAYaC269lXB0bA2su2HcfkrY4fc82P&utm_source=chatgpt.com", wait_until="networkidle")

    # Clear any storage that might have been set on load
    try:
        page.evaluate("localStorage.clear()")
        page.evaluate("sessionStorage.clear()")
    except (TimeoutError, ValueError):
        pass  # Storage might not be accessible

    # Delete all cookies again after page load
    page.context.clear_cookies()


def test_alaska_assistant(page: Page):
    seen_count: int = 0

    def before_each_simulation(testcase: dict) -> list[ChatMessage]:
        nonlocal seen_count

        seen_count = 0
        print(f"Starting new testcase: {testcase}")

        # Use the existing page instead of creating a new context
        page.goto("https://www.alaskaair.com/content/about-us/help-contact?fb1234&fb1234&fb1234&srsltid=AfmBOopecxxT98bV2I8TW6wIannAYaC269lXB0bA2su2HcfkrY4fc82P&utm_source=chatgpt.com")
        open_chat_assistant_bubble(page)
        print("Opened chat assistant bubble")
        fill_in_info_form(page)
        print("Filled in info form")
        wait_for_chat_assistant_to_load(page)

        initial_assistant_messages, image_data = wait_for_assistant_message(
            page, seen_count=0, seconds=1
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
        nonlocal seen_count
        new_assistant_messages, image_data = customer_service_assistant(
            page, seen_count=seen_count, chat_history=chat_history
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
    scorecard = Scorecard(
        environment="staging", 
        api_key=os.getenv("SCORECARD_API_KEY")
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
        project_id="206",
        metric_ids=["255", "256"],
        testset_id="17858",
        sim_agent_id="97d50674-a8d8-471c-baa6-42f44281a655",
        #
        system=system,
        initial_messages=before_each_simulation,
        stop_check=StopChecks.any(
            [StopChecks.max_turns(2), StopChecks.content(["timeout"])]
        ),
    )

    print(simulation_run)