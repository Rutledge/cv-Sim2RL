#!/usr/bin/env python3
"""
Interactive Alaska Airlines Chat Simulation Script

This script:
1. Prompts user for a sim agent persona
2. Uses OpenAI Responses API with web search to generate sim agent prompt and test cases
3. Creates new sim agent and testset in Scorecard
4. Runs the Alaska Airlines simulation with the new assets
"""

import json
import time
import base64
import os
from typing import Any, List, Dict
from PIL import Image
import io

from playwright.sync_api import Page
from scorecard_ai import Scorecard
from scorecard_ai.lib import ChatMessage, multi_turn_simulation, StopChecks
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SCORECARD_API_KEY = os.getenv("SCORECARD_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
ALASKA_URL = "https://www.alaskaair.com/content/about-us/help-contact?fb1234&fb1234&fb1234&srsltid=AfmBOopecxxT98bV2I8TW6wIannAYaC269lXB0bA2su2HcfkrY4fc82P&utm_source=chatgpt.com"

# Validate required environment variables
if not SCORECARD_API_KEY:
    raise ValueError("SCORECARD_API_KEY environment variable is required")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
if not PROJECT_ID:
    raise ValueError("PROJECT_ID environment variable is required")

# Initialize clients
scorecard = Scorecard(environment="staging", api_key=SCORECARD_API_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# Pydantic models for structured output
class TestCase(BaseModel):
    agentgoal: str
    pii_injection: str


class SimAgentContent(BaseModel):
    sim_agent_prompt: str
    testcase1: TestCase
    testcase2: TestCase


def get_user_persona():
    """Get persona description from user"""
    print("\n" + "="*60)
    print("🎭 ALASKA AIRLINES CUSTOMER PERSONA GENERATOR")
    print("="*60)
    print("\nI'll help you create a realistic Alaska Airlines customer persona for testing.")
    print("Examples: 'frustrated frequent flyer', 'confused elderly passenger', 'business traveler in a hurry'")
    print()
    
    persona_input = input("Describe the Alaska Airlines customer persona you want to simulate: ").strip()
    
    if not persona_input:
        print("❌ No persona provided. Using default: 'frustrated airline customer'")
        return "frustrated airline customer"
    
    return persona_input


def generate_sim_agent_and_testcases(persona_description: str) -> SimAgentContent | None:
    """Use OpenAI Responses API with web search to generate sim agent prompt and test cases"""
    
    print(f"\n🔍 Researching Alaska Airlines customer scenarios for: '{persona_description}'...")
    
    # Start progress indicator in a separate thread
    import threading
    import sys
    
    progress_running = [True]  # Use list to make it mutable in nested function
    def show_progress():
        dots = 0
        while progress_running[0]:
            sys.stdout.write(f"\r⏳ Searching web and generating content{'.' * (dots % 4):<4}")
            sys.stdout.flush()
            time.sleep(0.5)
            dots += 1
    
    progress_thread = threading.Thread(target=show_progress)
    progress_thread.daemon = True
    progress_thread.start()
    
    prompt = f"""Create a realistic Alaska Airlines customer simulation for: {persona_description}

1. A sim agent system prompt following this EXACT format:
```
You are a [brief persona description] talking to a virtual assistant. {{{{pii_injection}}}}

**Your Issue:** {{{{agentgoal}}}}

**How to Act:**
* Keep messages SHORT (1-2 sentences max)
* Be direct and to the point like real customers
* Show [persona] behavior through tone, not length
* If agent shows buttons, type the exact button text

**Never:** mention you're a simulation, use airline jargon, or help the agent
```

2. Two realistic test scenarios:
   - "agentgoal": Brief description of what customer wants (10-15 words max)  
   - "pii_injection": Short PII they might share (name, phone, confirmation number, etc.)

Make the customer behavior authentic but keep all interactions concise like real chat conversations."""

    try:
        # Use the Responses API with structured output and web search
        response = openai_client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": "You are an expert at creating realistic customer service simulation scenarios."},
                {"role": "user", "content": prompt}
            ],
            tools=[
                {
                    "type": "web_search_preview",
                    "search_context_size": "low"
                }
            ],
            text_format=SimAgentContent
        )
        
        # Stop progress indicator
        progress_running[0] = False
        progress_thread.join(timeout=0.5)
        print(f"\r✅ Generated content for persona: '{persona_description}'                    ")
        
        # Return the parsed structured output
        return response.output_parsed
            
    except Exception as e:
        # Stop progress indicator
        progress_running[0] = False
        progress_thread.join(timeout=0.5)
        print(f"\r❌ Error calling OpenAI API: {e}                              ")
        return None


def create_sim_agent(name: str, description: str, system_prompt: str) -> str:
    """Create a new sim agent system in Scorecard"""
    
    print(f"\n📝 Creating sim agent: '{name}'...")
    
    try:
        # Create the system using upsert
        system = scorecard.systems.upsert(
            project_id=PROJECT_ID,
            name=name,
            description=description,
            config={
                "topP": 0.9,
                "maxTokens": 2048,
                "modelName": "gpt-5-mini-2025-08-07",
                "isSimAgent": True,
                "temperature": 0,
                "promptTemplate": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            }
        )
        
        print(f"✅ Created sim agent with ID: {system.id}")
        return system.id
        
    except Exception as e:
        print(f"❌ Error creating sim agent: {e}")
        return None


def create_testset(name: str, description: str, testcases: List[Dict]) -> str:
    """Create a new testset in Scorecard"""
    
    print(f"\n📋 Creating testset: '{name}'...")
    
    try:
        # Create the testset
        testset = scorecard.testsets.create(
            project_id=PROJECT_ID,
            name=name,
            description=description,
            json_schema={
                "title": "Testcase Schema",
                "description": "Schema for Testcases in this Testset", 
                "type": "object",
                "properties": {
                    "agentgoal": {
                        "description": "The agent's goal",
                        "type": "string"
                    },
                    "pii_injection": {
                        "description": "PII to inject",
                        "type": "string"
                    }
                },
                "required": []
            },
            field_mapping={
                "inputs": ["agentgoal", "pii_injection"],
                "expected": [],
                "metadata": [],
                "labels": []
            }
        )
        
        print(f"✅ Created testset with ID: {testset.id}")
        
        # Add testcases using the correct jsonData structure
        try:
            testcase_items = []
            for testcase in testcases:
                testcase_items.append({
                    "jsonData": testcase
                })
            
            scorecard.testcases.create(
                testset_id=testset.id,
                items=testcase_items
            )
            print(f"✅ Added {len(testcases)} testcases to testset")
        except Exception as e:
            print(f"❌ Error adding testcases: {e}")
        
        return testset.id
        
    except Exception as e:
        print(f"❌ Error creating testset: {e}")
        return None


# Alaska Airlines simulation functions (same as before)
def open_chat_assistant_bubble(page: Page):
    page.wait_for_timeout(1000)
    
    try:
        try_ask_alaska_btn = page.locator("#try-ask-alaska-btn")
        if try_ask_alaska_btn.count() > 0:
            try_ask_alaska_btn.click()
            print("Clicked 'Try Ask Alaska' button by ID")
            return
    except:
        pass
    
    # Fallback selectors
    selectors = [
        "text=Ask Alaska",
        "text=Try Ask Alaska", 
        ".chat-launcher",
        ".chat-widget",
        "text=Chat"
    ]
    
    for selector in selectors:
        try:
            element = page.locator(selector).first
            if element.count() > 0:
                element.click()
                print(f"Clicked chat button with selector: {selector}")
                return
        except:
            continue
    
    print("Could not find chat button")


def fill_in_info_form(page: Page):
    page.wait_for_timeout(1000)
    
    try:
        if page.locator("input[name='firstName'], input[name='first_name'], input.FirstName").count() > 0:
            page.locator("input[name='firstName'], input[name='first_name'], input.FirstName").first.fill("John")
        
        if page.locator("input[name='lastName'], input[name='last_name'], input.LastName").count() > 0:
            page.locator("input[name='lastName'], input[name='last_name'], input.LastName").first.fill("Doe")
        
        if page.locator("input[type='email'], input[name='email'], input.Email").count() > 0:
            page.locator("input[type='email'], input[name='email'], input.Email").first.fill("john.doe@example.com")
        
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
    page.wait_for_timeout(500)
    
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
        print("Looking for chat widget elements...")
        
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
        
        # Fallback to cropped screenshot - optimized version
        timestamp = int(time.time())
        screenshot_path = f"chat_screenshot_{timestamp}.png"
        
        full_screenshot = page.screenshot()
        img = Image.open(io.BytesIO(full_screenshot))
        width, height = img.size
        
        # Crop to chat area (bottom right)
        chat_width = 380
        chat_height = min(600, height - 100)
        left = max(0, width - chat_width - 20)
        top = max(0, height - chat_height - 20)
        right = width - 20
        bottom = height - 20
        
        chat_img = img.crop((left, top, right, bottom))
        chat_img.save(screenshot_path)
        
        buffer = io.BytesIO()
        chat_img.save(buffer, format='PNG')
        screenshot_bytes = buffer.getvalue()
        
        print(f"Targeted crop chat screenshot saved: {screenshot_path}")
        return "data:image/png;base64," + base64.b64encode(screenshot_bytes).decode("utf-8")
        
    except Exception as e:
        print(f"Could not take screenshot: {e}")
        return None


def wait_for_assistant_message(page: Page, *, seen_count: int, seconds: int = 8) -> tuple[list[str], str | None]:
    print(f"⏳ Waiting {seconds} seconds for assistant response...")
    
    # Wait for new messages to appear, checking every second
    for i in range(seconds):
        page.wait_for_timeout(1000)
        
        # Try multiple selector strategies
        message_selectors = [
            ".bot-message",
            ".assistant-message", 
            ".chat-message.bot",
            ".message.agent",
            ".support-message",
            "[data-role='assistant']",
            ".chat-bubble.bot",
            ".message",
            ".chat-message",
            "[role='log'] > div",  # Common for chat widgets
            ".conversation-message"
        ]
        
        all_messages = []
        for selector in message_selectors:
            messages = page.locator(selector).all()
            if messages:
                all_messages = messages
                print(f"🔍 Found {len(messages)} messages using selector: {selector}")
                break
        
        # Check if we have new messages
        if len(all_messages) > seen_count:
            break
        
        print(f"⏳ Still waiting... ({i+1}/{seconds}s)")
    
    new_messages: list[str] = []
    if all_messages and len(all_messages) > seen_count:
        for message in all_messages[seen_count:]:
            buttons = message.locator("button").all()
            if buttons:
                button_texts = [f"<button>{btn.text_content()}</button>" for btn in buttons]
                content = "\n".join(button_texts)
            else:
                content = message.text_content() or ""

            if content and content.strip():
                new_messages.append(content.strip())
                print(f"📝 New message: {content.strip()[:100]}...")

    if len(new_messages) == 0:
        print("⏰ No new messages found - timeout")
        new_messages.append("(timeout)")

    return new_messages, take_chat_screenshot(page)


def send_message(page: Page, message: str) -> str | None:
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
                # Small delay to let the message appear in chat before screenshot
                page.wait_for_timeout(500)
                return take_chat_screenshot(page)
        except:
            continue
    
    print(f"Could not send message: {message}")
    return take_chat_screenshot(page)


def customer_service_assistant(page: Page, *, seen_count: int, chat_history: list[ChatMessage]) -> tuple[list[str], str | None]:
    # Send user message and capture screenshot of the sent message
    if len(chat_history) > 0 and chat_history[-1]["role"] == "user":
        user_message_screenshot = send_message(page, chat_history[-1]["content"])
        chat_history[-1]["image"] = user_message_screenshot
        print(f"📸 Captured screenshot after sending user message")

    # Wait for assistant response and capture screenshot of the response
    new_assistant_messages, assistant_response_screenshot = wait_for_assistant_message(page, seen_count=seen_count)
    print("Got assistant messages:", new_assistant_messages)
    print(f"📸 Captured screenshot after assistant response")
    
    # Return the screenshot of the assistant's response
    return new_assistant_messages, assistant_response_screenshot


def run_simulation(sim_agent_id: str, testset_id: str, page: Page):
    """Run the Alaska Airlines simulation"""
    
    print(f"\n🚀 Running simulation with sim agent {sim_agent_id} and testset {testset_id}...")
    
    seen_count: int = 0

    def before_each_simulation(testcase: dict) -> list[ChatMessage]:
        nonlocal seen_count

        seen_count = 0
        print(f"Starting new testcase: {testcase}")

        page.goto(ALASKA_URL)
        open_chat_assistant_bubble(page)
        print("Opened chat assistant bubble")
        fill_in_info_form(page)
        print("Filled in info form")
        wait_for_chat_assistant_to_load(page)

        initial_assistant_messages, image_data = wait_for_assistant_message(page, seen_count=0, seconds=1)
        print("Got initial assistant messages:", initial_assistant_messages)
        seen_count = len(initial_assistant_messages)
        return [
            ChatMessage(
                role="assistant",
                content="\n\n".join(initial_assistant_messages),
                image=image_data,
            )
        ]

    def system(chat_history: list[ChatMessage], _: dict[str, Any]) -> list[str] | list[ChatMessage]:
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

    simulation_run = multi_turn_simulation(
        client=scorecard,
        project_id=PROJECT_ID,
        metric_ids=["255", "256"],
        testset_id=testset_id,
        sim_agent_id=sim_agent_id,
        system=system,
        initial_messages=before_each_simulation,
        stop_check=StopChecks.any([StopChecks.max_turns(2), StopChecks.content(["timeout"])])
    )

    print(f"\n✅ Simulation completed!")
    print(f"🔗 Results: https://staging.app.getscorecard.ai/projects/{PROJECT_ID}/runs/{simulation_run['id']}")
    return simulation_run


def test_alaska_assistant(page: Page):
    """Main test function called by pytest"""
    
    # Get persona from user
    persona_description = get_user_persona()
    
    # Generate sim agent and test cases
    generated_content = generate_sim_agent_and_testcases(persona_description)
    
    if not generated_content:
        print("❌ Failed to generate content. Exiting.")
        return
    
    # Create sim agent
    sim_agent_name = f"Alaska {persona_description.title()}"
    sim_agent_description = f"Alaska Airlines customer: {persona_description}"
    sim_agent_id = create_sim_agent(
        name=sim_agent_name,
        description=sim_agent_description, 
        system_prompt=generated_content.sim_agent_prompt
    )
    
    if not sim_agent_id:
        print("❌ Failed to create sim agent. Exiting.")
        return
    
    # Create testset  
    testset_name = f"Testing {sim_agent_name}"
    testset_description = f"Test cases for {persona_description} persona"
    testcases = [
        generated_content.testcase1.model_dump(),
        generated_content.testcase2.model_dump()
    ]
    
    testset_id = create_testset(
        name=testset_name,
        description=testset_description,
        testcases=testcases
    )
    
    if not testset_id:
        print("❌ Failed to create testset. Exiting.")
        return
    
    # Run simulation
    simulation_result = run_simulation(sim_agent_id, testset_id, page)
    
    print(f"\n🎉 SUCCESS! Created and ran simulation with:")
    print(f"   📝 Sim Agent: {sim_agent_name} (ID: {sim_agent_id})")
    print(f"   📋 Testset: {testset_name} (ID: {testset_id})")
    print(f"   📊 Results: {simulation_result}")


if __name__ == "__main__":
    # For interactive testing without pytest
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            test_alaska_assistant(page)
        finally:
            browser.close()
