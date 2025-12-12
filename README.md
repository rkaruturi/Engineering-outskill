# 🤖 Self-Healing Browser Automation System

An intelligent multi-agent system that uses LLMs to generate, execute, and automatically repair browser automation scripts with adaptive error recovery.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-green)](https://playwright.dev)
[![OpenRouter](https://img.shields.io/badge/LLM-OpenRouter-orange)](https://openrouter.ai)

## ✨ Features

- **🧠 AI Script Generation**: Convert natural language to Playwright code using Claude/GPT
- **▶️ Automated Execution**: Run scripts with comprehensive logging and artifact capture
- **🔍 Intelligent Diagnosis**: Classify errors and identify root causes  
- **🔧 Self-Healing**: Automatically repair failed scripts and retry
- **📊 Visual Dashboard**: Streamlit UI for monitoring, results, and cost tracking
- **💰 Cost-Optimized**: Uses Claude 3.5 Haiku (~$0.01-0.05 per script)
- **📸 Complete Artifacts**: Screenshots, videos, logs for every execution

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Dashboard                     │
│          (Task Input, Results, Scripts, Costs)              │
└────────────────────┬────────────────────────────────────────┘
                     │
              ┌──────▼──────┐
              │ Orchestrator │
              └──────┬───────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼──────┐  ┌───▼────┐  ┌──────▼─────┐
│  Script    │  │Execute │  │   Error    │
│ Generator  │→ │ Engine │→ │ Diagnosis  │
└────────────┘  └────────┘  └──────┬─────┘
                                   │
                            ┌──────▼──────┐
                            │  Adaptive   │
                            │   Repair    │
                            └─────────────┘
```

### Agents

1. **Script Generator**: LLM-powered Playwright code generation
2. **Execution Engine**: Browser automation with logging
3. **Error Diagnosis**: Failure analysis and classification
4. **Adaptive Repair**: Self-healing script regeneration

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- OpenRouter API key ([Get one here](https://openrouter.ai))

### Installation

1. **Clone/Navigate to the project directory**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

4. **Configure environment**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env and add your OpenRouter API key
   # OPENROUTER_API_KEY=your_actual_key_here
   ```

### Running the Dashboard

```bash
streamlit run dashboard.py
```

Visit `http://localhost:8501` in your browser.

## 📖 Usage

### Via Dashboard

1. Open the Streamlit dashboard
2. Enter a natural language task description:
   - "Navigate to example.com and take a screenshot"
   - "Search for 'AI automation' on google.com"
   - "Fill out the contact form at example.com/contact"
3. Click "Generate & Execute"
4. View results, screenshots, and videos

### Via Python API

```python
import asyncio
from orchestrator import automate

async def main():
    result = await automate(
        description="Navigate to example.com and click the login button",
        url="https://example.com",
        auto_heal=True  # Enable self-healing
    )
    
    print(f"Status: {result.final_status}")
    print(f"Cost: ${result.total_cost:.4f}")

asyncio.run(main())
```

### Direct Agent Usage

```python
from agents import ScriptGeneratorAgent, ExecutionEngineAgent

async def generate_and_run():
    # Generate script
    generator = ScriptGeneratorAgent()
    script = await generator.generate_script(task)
    
    # Execute script
    engine = ExecutionEngineAgent()
    result = await engine.execute_script(script)
```

## 💰 Cost Management

The system is designed to be cost-efficient:

- **Primary Model**: Claude 3.5 Haiku (~$0.25 input / $1.25 output per 1M tokens)
- **Typical Costs**:
  - Script generation: $0.01-0.03
  - Error diagnosis: $0.005-0.01
  - Script repair: $0.01-0.03
  - **Total per automation**: ~$0.02-0.10

### Budget Controls

Configure in `.env`:
```env
MAX_COST_PER_RUN=0.50    # Max spend per automation
DAILY_BUDGET=5.00         # Daily spending limit
```

Monitor costs in the dashboard's "Costs" page.

## 🎯 Example Tasks

### Simple Navigation
```
Navigate to example.com and take a screenshot of the homepage
```

### Form Interaction
```
Go to example.com/contact, fill in the name field with 'John Doe', 
email with 'john@example.com', and submit the form
```

### Multi-Step Flow
```
Navigate to example.com, click the login button, enter username 'test@example.com'
and password 'password123', click submit, wait for dashboard to load, 
and take a screenshot
```

### Search & Extract
```
Search for 'Playwright automation' on google.com and capture the search results page
```

## 🔧 Configuration

Edit `.env` for customization:

```env
# API Configuration
OPENROUTER_API_KEY=your_key_here
DEFAULT_MODEL=anthropic/claude-3.5-haiku
FALLBACK_MODEL=openai/gpt-4o-mini

# Browser Settings
HEADLESS=false              # Run browser visibly
BROWSER_TYPE=chromium       # chromium, firefox, webkit
DEFAULT_TIMEOUT=30000       # 30 seconds

# Self-Healing
MAX_REPAIR_ATTEMPTS=3       # Max auto-repair attempts
AUTO_HEAL=true              # Enable auto-repair

# Budget
MAX_COST_PER_RUN=0.50
DAILY_BUDGET=5.00
```

## 📁 Project Structure

```
Browser Automation/
├── agents/
│   ├── script_generator.py      # LLM → Playwright code
│   ├── execution_engine.py      # Run automation scripts
│   ├── error_diagnosis.py       # Analyze failures
│   └── adaptive_repair.py       # Fix scripts
├── utils/
│   ├── prompts.py               # LLM prompt templates
│   ├── cost_tracker.py          # API cost monitoring
│   └── screenshot_manager.py    # Artifact management
├── config.py                    # Configuration
├── models.py                    # Data models
├── orchestrator.py              # Main workflow coordinator
├── dashboard.py                 # Streamlit UI
├── requirements.txt             # Dependencies
└── .env.example                 # Environment template
```

## 🔄 Workflow

1. **Generate**: LLM converts task description to Playwright script
2. **Execute**: Run script in browser, capture artifacts
3. **Check**: Success? → Done. Failure? → Continue
4. **Diagnose**: Analyze error (selector issue, timeout, etc.)
5. **Repair**: LLM regenerates script with fixes
6. **Retry**: Execute repaired script (max 3 attempts)

## 📊 Dashboard Pages

- **🏠 Home**: Create and run automation tasks
- **📊 Results**: View execution history and artifacts
- **🔧 Scripts**: Export generated scripts for CI/CD
- **💰 Costs**: Monitor API usage and budgets

## 🛠️ Troubleshooting

### "OpenRouter API key not found"
- Copy `.env.example` to `.env`
- Add your API key: `OPENROUTER_API_KEY=sk-or-...`

### Browser doesn't launch
```bash
# Reinstall Playwright browsers
playwright install chromium
```

### Import errors
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

### High costs
- Use Claude 3.5 Haiku (default, cheapest)
- Reduce `MAX_REPAIR_ATTEMPTS`
- Set strict budget limits in `.env`

## 🎓 Advanced Usage

### Custom Prompt Templates

Edit `utils/prompts.py` to customize LLM prompts:

```python
class PromptTemplates:
    @staticmethod
    def script_generation_prompt(task_description, url):
        # Customize your prompt here
        return f"Generate Playwright code for: {task_description}"
```

### CI/CD Integration

Export generated scripts from the dashboard and integrate into your CI pipeline:

```yaml
# .github/workflows/automation.yml
- name: Run automation test
  run: python exported_script.py
```

### Add Custom Agents

Create new agents in `agents/` directory:

```python
class CustomAgent:
    async def process(self, data):
        # Your logic here
        pass
```

## 📝 License

MIT License - feel free to use in your projects!

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional LLM providers
- Visual regression testing (Pixelmatch integration)
- Flow discovery agent
- More sophisticated error recovery strategies

## 🙏 Acknowledgments

- **Playwright**: Browser automation framework
- **OpenRouter**: Unified LLM API access
- **Anthropic/OpenAI**: Claude and GPT models
- **Streamlit**: Rapid dashboard development

---

**Built with** ❤️ **for intelligent browser automation**
