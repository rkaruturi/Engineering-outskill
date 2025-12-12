"""
Centralized prompt templates for LLM interactions.
Structured prompts for script generation, error repair, and diagnostics.
"""

from typing import Dict, List, Optional


class PromptTemplates:
    """Reusable prompt templates for the automation system"""
    
    @staticmethod
    def script_generation_prompt(task_description: str, url: Optional[str] = None) -> str:
        """Generate a prompt for creating a Playwright automation script"""
        
        url_context = f"\nTarget URL: {url}" if url else ""
        
        return f"""You are an expert in browser automation using Playwright (Python).
Generate a robust, production-ready Playwright script for the following task:

Task: {task_description}{url_context}

REQUIREMENTS:
1. Use async/await with Playwright Python API
2. Include proper error handling and timeouts
3. Use robust selector strategies (PRIORITY ORDER):
   - Accessibility roles: `page.get_by_role("button", name="Log in")`
   - Data attributes: `page.locator('[data-testid="submit"]')`
   - Text content: `page.get_by_text("Submit")`
   - CSS selectors (avoid dynamic IDs like #input-123)
4. HANDLE SPAs/DYNAMIC CONTENT:
   - Always `await page.wait_for_selector()` before interaction
   - Use `wait_until='domcontentloaded'` for heavy sites (YouTube, etc.) instead of 'networkidle'
   - Add small delays if needed for interactions to register
5. Capture screenshots at key steps
6. Include descriptive comments
7. Handle common edge cases (popups, cookies, modals)

SCRIPT STRUCTURE:
```python
from playwright.async_api import async_playwright
import asyncio

async def run_automation(page):
    '''Generated automation script'''
    try:
        # Step 1: Navigate
        await page.goto('URL_HERE', wait_until='networkidle')
        await page.screenshot(path='step1_navigate.png')
        
        # Add more steps here...
        
        return {{'success': True, 'message': 'Automation completed successfully'}}
    except Exception as e:
        return {{'success': False, 'error': str(e)}}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={{'width': 1920, 'height': 1080}}
        )
        page = await context.new_page()
        
        result = await run_automation(page)
        
        await browser.close()
        return result

if __name__ == '__main__':
    result = asyncio.run(main())
    print(result)
```

Generate ONLY the Python code, no explanations. Make it executable as-is."""

    @staticmethod
    def error_repair_prompt(
        original_script: str, 
        error_type: str, 
        error_message: str, 
        error_context: Dict
    ) -> str:
        """Generate a prompt for repairing a failed script"""
        
        context_str = "\n".join([f"- {k}: {v}" for k, v in error_context.items()])
        
        return f"""You are an expert at debugging and fixing Playwright automation scripts.

ORIGINAL SCRIPT:
```python
{original_script}
```

ERROR DETAILS:
- Error Type: {error_type}
- Error Message: {error_message}

ERROR CONTEXT:
{context_str}

TASK:
Analyze the error and generate a FIXED version of the script that addresses the issue.

COMMON FIXES BY ERROR TYPE:
1. **selector_not_found**: 
   - Try accessibility selectors: `get_by_role()`, `get_by_label()` (MORE ROBUST)
   - Add explicit waits: await page.wait_for_selector(state='visible')
   - Check for iframes or shadow DOM
   - For dynamic sites (YouTube), use `wait_until='domcontentloaded'` instead of networkidle

2. **timeout**: 
   - Increase timeout: timeout=60000
   - Use network idle: wait_until='networkidle'
   - Add retry logic with exponential backoff

3. **network_error**: 
   - Add retry logic for failed requests
   - Check for DNS/connection issues
   - Handle offline scenarios

4. **unexpected_state**: 
   - Add conditional checks before interactions
   - Handle multiple possible states
   - Use page.wait_for_load_state()

Generate ONLY the fixed Python code, no explanations. Ensure it's executable."""

    @staticmethod
    def error_diagnosis_prompt(
        error_message: str,
        console_logs: List[str],
        network_logs: List[Dict],
        screenshot_available: bool
    ) -> str:
        """Generate a prompt for diagnosing an error"""
        
        console_str = "\n".join(console_logs[-10:]) if console_logs else "No console logs"
        network_str = "\n".join([
            f"- {log.get('method', 'GET')} {log.get('url', 'N/A')} -> {log.get('status', 'N/A')}"
            for log in network_logs[-5:]
        ]) if network_logs else "No network logs"
        
        return f"""Analyze this browser automation failure and provide a detailed diagnosis.

ERROR MESSAGE:
{error_message}

CONSOLE LOGS (last 10):
{console_str}

NETWORK ACTIVITY (last 5):
{network_str}

Screenshot Available: {screenshot_available}

Provide a JSON response with:
{{
    "error_type": "selector_not_found|timeout|network_error|javascript_error|crash|unexpected_state|unknown",
    "root_cause": "Brief explanation of what went wrong",
    "suggested_fixes": ["Fix 1", "Fix 2", "Fix 3"],
    "confidence": 0.0-1.0
}}

Respond ONLY with valid JSON."""

    @staticmethod
    def flow_discovery_prompt(url: str, page_html: str) -> str:
        """Generate a prompt for discovering automatable flows"""
        
        # Truncate HTML if too long
        html_preview = page_html[:3000] + "..." if len(page_html) > 3000 else page_html
        
        return f"""Analyze this webpage and identify automatable user flows.

URL: {url}

HTML STRUCTURE:
{html_preview}

TASK:
Identify common automation scenarios on this page, such as:
- Login forms
- Registration flows
- Search functionality
- Checkout processes
- Form submissions
- Navigation patterns

Provide a JSON response:
{{
    "flows": [
        {{
            "name": "Login Flow",
            "description": "User authentication",
            "steps": ["Navigate to login", "Enter credentials", "Submit"],
            "selectors": {{"email": "#email", "password": "#password", "submit": "button[type=submit]"}},
            "complexity": "low|medium|high"
        }}
    ]
}}

Respond ONLY with valid JSON."""

    @staticmethod
    def get_system_message(role: str = "script_generator") -> str:
        """Get system message for LLM"""
        
        messages = {
            "script_generator": "You are an expert Playwright automation engineer. Generate clean, robust, production-ready code.",
            "error_repair": "You are a debugging expert specializing in fixing browser automation failures.",
            "diagnostician": "You are an expert at analyzing browser automation errors and providing actionable solutions."
        }
        
        return messages.get(role, "You are a helpful AI assistant.")


# Example usage templates
EXAMPLE_TASKS = {
    "simple_navigation": "Navigate to example.com and take a screenshot",
    "login": "Go to example.com/login, enter email 'test@example.com' and password 'password123', then click login",
    "form_fill": "Fill out the contact form at example.com/contact with name 'John Doe', email 'john@example.com', and message 'Hello'",
    "search": "Search for 'Playwright automation' on google.com and capture the first page of results"
}
