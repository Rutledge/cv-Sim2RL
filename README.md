# Alaska Airlines Chat Simulation System

An interactive system for testing customer service chatbots using automated persona-based simulations.

## Features

- **Interactive Persona Generation**: Uses OpenAI's Responses API with web search to generate realistic customer personas
- **Automated Sim Agent Creation**: Creates simulation agents in Scorecard AI with structured prompts
- **Dynamic Testcase Generation**: Generates relevant test scenarios for each persona
- **Screenshot Capture**: Takes screenshots during chat interactions for visual verification
- **Scorecard AI Integration**: Runs automated simulations and tracks results

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

3. **Set up environment variables:**
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your actual keys:
   ```
   SCORECARD_API_KEY=your_scorecard_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here  
   PROJECT_ID=your_scorecard_project_id_here
   ```

## Usage

Run the interactive simulation:

```bash
python interactive_alaska_simulation.py
```

The script will:
1. Ask you to describe a customer persona (e.g., "frustrated frequent flyer")
2. Research and generate realistic simulation scenarios
3. Create a new sim agent and testset in Scorecard
4. Run the simulation against Alaska Airlines' chat system
5. Provide a link to view results

## Files

- `interactive_alaska_simulation.py` - Main interactive simulation script
- `run_alaska_simulation.py` - Direct Alaska Airlines simulation script
- `get_sim_agent.py` - Utility to inspect existing sim agents
- `get_testset.py` - Utility to inspect existing testsets

## Architecture

The system uses:
- **OpenAI Responses API** with web search for persona research and content generation
- **Pydantic models** for structured output validation
- **Playwright** for browser automation and screenshot capture
- **Scorecard AI** for simulation management and result tracking

## Example Personas

- "frustrated frequent flyer"
- "confused elderly passenger" 
- "business traveler in a hurry"
- "family with young children"
- "price-conscious budget traveler"