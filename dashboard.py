"""
Streamlit Dashboard - Web interface for the automation system.
Provides task input, execution monitoring, results visualization, and cost tracking.
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
from PIL import Image

# Fix for Windows asyncio event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from config import Config
from models import TaskStatus
from orchestrator import AutomationOrchestrator
from utils import get_cost_tracker, ScreenshotManager


# Page configuration
st.set_page_config(
    page_title="Self-Healing Browser Automation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'test_runs' not in st.session_state:
    st.session_state.test_runs = []
if 'current_run' not in st.session_state:
    st.session_state.current_run = None


def run_async(coro):
    """Helper to run async functions in Streamlit"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def sidebar():
    """Render sidebar navigation"""
    st.sidebar.title("🤖 Browser Automation")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "📊 Results", "🔧 Scripts", "💰 Costs"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Settings")
    
    headless = st.sidebar.checkbox("Headless Mode", value=Config.HEADLESS)
    auto_heal = st.sidebar.checkbox("Auto-Heal", value=Config.AUTO_HEAL)
    
    st.sidebar.markdown(f"""
    **Budget Limits**
    - Per Run: ${Config.MAX_COST_PER_RUN:.2f}
    - Daily: ${Config.DAILY_BUDGET:.2f}
    """)
    
    return page, headless, auto_heal


def home_page(headless, auto_heal):
    """Main page for creating automation tasks"""
    st.title("🏠 Self-Healing Browser Automation")
    st.markdown("Generate and execute browser automation scripts using AI")
    
    # Task input section
    st.markdown("### 📝 Create Automation Task")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        description = st.text_area(
            "Task Description",
            placeholder="Example: Navigate to example.com, click the login button, enter username 'test@example.com' and password 'password123', then submit",
            height=100,
            help="Describe what you want the browser to do in natural language"
        )
    
    with col2:
        url = st.text_input(
            "Starting URL (optional)",
            placeholder="https://example.com",
            help="The URL where the automation should start"
        )
        
        st.markdown("**Quick Examples:**")
        examples = {
            "Simple Navigation": "Navigate to example.com and take a screenshot",
            "Google Search": "Search for 'Playwright automation' on google.com",
            "Form Fill": "Go to example.com/contact and fill out the contact form with test data"
        }
        
        example = st.selectbox("Load Example", [""] + list(examples.keys()))
        if example and st.button("Load"):
            st.session_state.example_description = examples[example]
            st.rerun()
    
    # Use example if loaded
    if 'example_description' in st.session_state:
        description = st.session_state.example_description
        del st.session_state.example_description
    
    # Run button
    if st.button("🚀 Generate & Execute", type="primary", use_container_width=True):
        if not description:
            st.error("Please enter a task description")
            return
        
        if not Config.OPENROUTER_API_KEY:
            st.error("⚠️ OpenRouter API key not configured. Please set OPENROUTER_API_KEY in .env file")
            return
        
        # Run automation
        with st.spinner("🤖 Running automation workflow..."):
            orchestrator = AutomationOrchestrator()
            
            # Create progress container
            progress_container = st.container()
            
            with progress_container:
                st.info("⏳ Generating script...")
                
                try:
                    # Run automation
                    test_run = run_async(
                        orchestrator.run_automation(
                            description=description,
                            url=url if url else None,
                            headless=headless,
                            auto_heal=auto_heal
                        )
                    )
                    
                    # Store in session
                    st.session_state.test_runs.append(test_run)
                    st.session_state.current_run = test_run
                    
                    # Show results
                    st.success("✅ Automation completed!")
                    st.balloons()
                    
                    # Display results
                    display_test_run(test_run)
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Show recent runs
    if st.session_state.test_runs:
        st.markdown("---")
        st.markdown("### 📋 Recent Runs")
        
        for i, run in enumerate(reversed(st.session_state.test_runs[-5:])):
            with st.expander(f"Run #{len(st.session_state.test_runs) - i}: {run.task.description[:50]}..."):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Status", run.final_status.value)
                with col2:
                    st.metric("Attempts", len(run.executions))
                with col3:
                    st.metric("Cost", f"${run.total_cost:.4f}")


def display_test_run(test_run):
    """Display detailed test run results"""
    st.markdown("---")
    st.markdown("### 📊 Execution Results")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_icon = "✅" if test_run.final_status == TaskStatus.SUCCESS else "❌"
        st.metric("Status", f"{status_icon} {test_run.final_status.value}")
    
    with col2:
        st.metric("Execution Attempts", len(test_run.executions))
    
    with col3:
        st.metric("Repairs Made", len(test_run.repairs))
    
    with col4:
        st.metric("Total Cost", f"${test_run.total_cost:.4f}")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📸 Screenshots", "📜 Logs", "💻 Code"])
    
    with tab1:
        if test_run.executions and test_run.executions[-1].screenshots:
            last_exec = test_run.executions[-1]
            st.markdown("**Captured Screenshots:**")
            
            cols = st.columns(3)
            for i, screenshot_path in enumerate(last_exec.screenshots):
                with cols[i % 3]:
                    try:
                        img = Image.open(screenshot_path)
                        st.image(img, caption=Path(screenshot_path).stem, use_column_width=True)
                    except Exception as e:
                        st.error(f"Could not load {screenshot_path}: {e}")
            
            # Video
            if last_exec.video_path and Path(last_exec.video_path).exists():
                st.markdown("**Recorded Video:**")
                st.video(last_exec.video_path)
        else:
            st.info("No screenshots available")
    
    with tab2:
        # Execution logs
        for i, execution in enumerate(test_run.executions):
            with st.expander(f"Attempt {i+1} - {'✅ Success' if execution.success else '❌ Failed'}", expanded=(not execution.success)):
                # Always show error message if failed
                if not execution.success and execution.error_message:
                    st.error(f"**Error:** {execution.error_message}")
                
                # Show execution details
                st.markdown(f"**Execution Time:** {execution.execution_time:.2f}s")
                st.markdown(f"**Script Version:** v{execution.script_version}")
                
                # Console logs
                if execution.console_logs:
                    st.markdown("**Console Logs:**")
                    st.code("\n".join(execution.console_logs[-20:]), language="text")
                else:
                    st.info("No console logs available")
                
                # Network logs (if any errors)
                if execution.network_logs:
                    failed_requests = [log for log in execution.network_logs if log.get("status", 200) >= 400]
                    if failed_requests:
                        st.markdown("**Failed Network Requests:**")
                        for req in failed_requests[:5]:
                            st.text(f"{req.get('method', 'GET')} {req.get('url', 'N/A')} → {req.get('status', 'N/A')}")

        
        # Diagnoses
        if test_run.diagnoses:
            st.markdown("**Error Diagnoses:**")
            for i, diagnosis in enumerate(test_run.diagnoses):
                with st.expander(f"Diagnosis {i+1}: {diagnosis.error_type.value}"):
                    st.markdown(f"**Confidence:** {diagnosis.confidence * 100:.0f}%")
                    st.markdown(f"**Root Cause:** {diagnosis.error_message}")
                    if diagnosis.suggested_fixes:
                        st.markdown("**Suggested Fixes:**")
                        for fix in diagnosis.suggested_fixes:
                            st.markdown(f"- {fix}")
    
    with tab3:
        # Show all script versions
        for i, script in enumerate(test_run.scripts):
            version_label = f"v{script.version} - {'Initial' if i == 0 else f'Repair {i}'}"
            with st.expander(f"Script {version_label}"):
                st.code(script.code, language="python")
                st.caption(f"Model: {script.model_used} | Cost: ${script.cost:.4f}")
                
                # Download button
                st.download_button(
                    label=f"📥 Download {version_label}",
                    data=script.code,
                    file_name=f"automation_v{script.version}.py",
                    mime="text/x-python"
                )


def results_page():
    """Page showing all test results"""
    st.title("📊 Test Results History")
    
    # Load all saved test runs
    if Config.LOGS_DIR.exists():
        task_dirs = [d for d in Config.LOGS_DIR.iterdir() if d.is_dir()]
        
        if task_dirs:
            for task_dir in sorted(task_dirs, reverse=True)[:20]:  # Show last 20
                run_file = task_dir / "test_run.json"
                if run_file.exists():
                    try:
                        with open(run_file, 'r') as f:
                            data = json.load(f)
                        
                        with st.expander(f"{task_dir.name}: {data['task']['description'][:60]}..."):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Status", data['final_status'])
                            with col2:
                                st.metric("Attempts", len(data['executions']))
                            with col3:
                                st.metric("Cost", f"${data['total_cost']:.4f}")
                            
                            # View artifacts
                            artifacts = ScreenshotManager.get_task_artifacts(task_dir.name)
                            if artifacts['screenshots']:
                                st.markdown(f"**Screenshots:** {artifacts['total_screenshots']}")
                    except Exception as e:
                        st.error(f"Error loading {task_dir.name}: {e}")
        else:
            st.info("No test results yet. Run an automation task to see results here.")
    else:
        st.info("No test results yet.")


def scripts_page():
    """Page for managing and exporting scripts"""
    st.title("🔧 Generated Scripts")
    
    if Config.SCRIPTS_DIR.exists():
        task_dirs = [d for d in Config.SCRIPTS_DIR.iterdir() if d.is_dir()]
        
        if task_dirs:
            for task_dir in sorted(task_dirs, reverse=True):
                scripts = sorted(task_dir.glob("*.py"))
                if scripts:
                    with st.expander(f"Task: {task_dir.name} ({len(scripts)} versions)"):
                        for script_path in scripts:
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.code(script_path.read_text(), language="python", line_numbers=True)
                            
                            with col2:
                                st.download_button(
                                    label=f"📥 Download",
                                    data=script_path.read_text(),
                                    file_name=script_path.name,
                                    mime="text/x-python",
                                    key=str(script_path)
                                )
        else:
            st.info("No scripts generated yet.")
    else:
        st.info("No scripts generated yet.")


def costs_page():
    """Page showing cost analytics"""
    st.title("💰 API Cost Analytics")
    
    cost_tracker = get_cost_tracker()
    summary = cost_tracker.get_summary()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", summary['total_requests'])
    
    with col2:
        st.metric("Total Cost", f"${summary['total_cost']:.4f}")
    
    with col3:
        st.metric("Today's Cost", f"${summary['daily_cost']:.4f}")
    
    with col4:
        remaining = Config.DAILY_BUDGET - summary['daily_cost']
        st.metric("Budget Remaining", f"${remaining:.2f}")
    
    # Details
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Token Usage")
        st.metric("Input Tokens", f"{summary['total_input_tokens']:,}")
        st.metric("Output Tokens", f"{summary['total_output_tokens']:,}")
        st.metric("Avg Cost/Request", f"${summary['average_cost_per_request']:.4f}")
    
    with col2:
        st.markdown("### Cost by Model")
        if summary['cost_by_model']:
            for model, cost in summary['cost_by_model'].items():
                st.metric(model.split('/')[-1], f"${cost:.4f}")
        else:
            st.info("No API calls made yet")
    
    # Budget settings
    st.markdown("---")
    st.markdown("### 💳 Budget Settings")
    st.info(f"""
    - **Max Cost Per Run:** ${Config.MAX_COST_PER_RUN:.2f}
    - **Daily Budget:** ${Config.DAILY_BUDGET:.2f}
    - **Primary Model:** {Config.DEFAULT_MODEL}
    - **Fallback Model:** {Config.FALLBACK_MODEL}
    
    Edit these settings in the `.env` file.
    """)

    # OpenRouter Live Status
    st.markdown("---")
    st.subheader("🔑 OpenRouter API Status")
    
    if st.button("Check API Key Details"):
        with st.spinner("Querying OpenRouter API..."):
            try:
                import urllib.request
                import json
                
                api_key = Config.OPENROUTER_API_KEY
                if not api_key:
                    st.error("No API key configured.")
                else:
                    req = urllib.request.Request("https://openrouter.ai/api/v1/auth/key")
                    req.add_header("Authorization", f"Bearer {api_key}")
                    
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            data = json.loads(response.read()).get('data', {})
                            st.success("✅ Connected to OpenRouter")
                            
                            col_a, col_b, col_c = st.columns(3)
                            
                            limit = data.get('limit')
                            usage = data.get('usage')
                            
                            col_a.metric("Credit Limit", f"${limit}" if limit else "Unknown")
                            col_b.metric("Used So Far", f"${usage:.4f}" if usage is not None else "Unknown")
                            
                            if limit and usage is not None:
                                remaining = float(limit) - float(usage)
                                col_c.metric("Actual Remaining", f"${remaining:.4f}")
                            else:
                                col_c.metric("Actual Remaining", "Unlimited")
                        else:
                            st.error(f"Failed to check key: {response.status}")
                            
            except Exception as e:
                st.error(f"Error checking API: {e}")


# Main app
def main():
    page, headless, auto_heal = sidebar()
    
    if page == "🏠 Home":
        home_page(headless, auto_heal)
    elif page == "📊 Results":
        results_page()
    elif page == "🔧 Scripts":
        scripts_page()
    elif page == "💰 Costs":
        costs_page()


if __name__ == "__main__":
    main()
