# Sim2RL: AI-Powered Simulation Agents for Reinforcement Learning

*Generate realistic user personas for training conversational AI agents through advanced simulation and reinforcement learning*

## 🚀 Overview

Sim2RL bridges the gap between AI evaluation and reinforcement learning by automatically generating authentic user personas that act as dynamic training environments. Instead of static test scripts, we create intelligent simulation agents that research real-world behaviors and adapt their interactions based on actual user patterns.

## ⚡ Key Features

- **Autonomous Persona Research**: AI agents automatically discover and synthesize real user behaviors from web data
- **Dynamic Simulation Environments**: Personas evolve and adapt during conversations, creating realistic training scenarios
- **Multi-Modal RL Training Data**: Captures both conversational text and visual interface states for comprehensive agent training
- **Real-World Integration**: Test against live production systems while generating training data
- **Continuous Learning Pipeline**: Simulation results feed directly into RL training loops for autonomous improvement

## 🛠 Quick Start

```bash
# Setup environment
pip install -r requirements.txt
playwright install

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Launch interactive persona generator
python interactive_alaska_simulation.py
```

## 🎯 How It Works

1. **Persona Genesis**: Describe a user type → AI researches real behaviors → Creates authentic simulation agent
2. **Live Simulation**: Autonomous agents interact with target systems while capturing multi-modal training data
3. **RL Pipeline**: Conversation outcomes become reward signals for continuous policy improvement
4. **Performance Analytics**: Visual conversation analysis reveals agent strengths and failure modes

## 📊 Applications

- **Customer Service AI Training**: Generate diverse customer personas for chatbot improvement
- **Conversational AI Evaluation**: Test dialogue systems against realistic user behaviors  
- **Policy Optimization**: Use simulation data to train better RL policies
- **Risk Mitigation**: Discover edge cases before production deployment

## 🏗 Architecture

Built with cutting-edge AI infrastructure:
- OpenAI GPT-5 with web search for persona research
- Scorecard AI for simulation orchestration
- Playwright for real-world system integration
- Structured outputs via Pydantic for reliable data flows

## 📁 Project Structure

- `interactive_alaska_simulation.py` - Main persona generator and simulation runner
- `run_alaska_simulation.py` - Direct simulation execution framework
- `get_sim_agent.py` - Simulation agent introspection utilities
- `get_testset.py` - Training dataset analysis tools

## 🎭 Example Personas

Transform simple descriptions into intelligent simulation agents:
- "frustrated frequent flyer" → Research actual airline complaints → Generate realistic customer behavior
- "confused elderly passenger" → Study accessibility issues → Create authentic interaction patterns
- "business traveler in a hurry" → Analyze time-pressure scenarios → Simulate urgent conversation dynamics

Transform your AI training from static scripts to dynamic, intelligent simulation environments.