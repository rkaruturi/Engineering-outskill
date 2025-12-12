"""
Execution Engine Agent - Executes Playwright scripts and captures results.
Runs automation scripts with comprehensive logging and artifact capture.
"""

import asyncio
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import time

from config import Config
from models import GeneratedScript, ExecutionResult, TaskStatus
from utils import ScreenshotManager


class ExecutionEngineAgent:
    """Executes Playwright automation scripts"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshot_manager: Optional[ScreenshotManager] = None
    
    async def execute_script(
        self, 
        script: GeneratedScript,
        headless: Optional[bool] = None
    ) -> ExecutionResult:
        """Execute a generated Playwright script"""
        
        print(f"▶️  Executing script v{script.version} for task {script.task_id}")
        
        if headless is None:
            headless = Config.HEADLESS
        
        # SAFETY: Always force headless in cloud environments (no display available)
        if Config.IS_CLOUD_ENVIRONMENT:
            headless = True
        
        # Initialize screenshot manager
        self.screenshot_manager = ScreenshotManager(script.task_id)
        
        # Prepare result object
        result = ExecutionResult(
            task_id=script.task_id,
            script_version=script.version,
            success=False
        )
        
        start_time = time.time()
        
        try:
            # Initialize Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser
            browser_type = getattr(self.playwright, Config.BROWSER_TYPE)
            
            # Build browser args - add necessary flags for containerized/cloud environments
            browser_args = ['--start-maximized']
            if headless:
                # These args are required for running in containers without X server
                browser_args.extend([
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--disable-software-rasterizer',
                ])
            
            self.browser = await browser_type.launch(
                headless=headless,
                args=browser_args
            )
            
            # Create context with video recording
            video_path = self.screenshot_manager.get_video_path()
            self.context = await self.browser.new_context(
                viewport={'width': Config.VIEWPORT_WIDTH, 'height': Config.VIEWPORT_HEIGHT},
                record_video_dir=str(video_path.parent),
                record_video_size={'width': Config.VIEWPORT_WIDTH, 'height': Config.VIEWPORT_HEIGHT}
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set up console log capture
            console_logs = []
            self.page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
            
            # Set up network log capture
            network_logs = []
            def log_request(request):
                network_logs.append({
                    "type": "request",
                    "method": request.method,
                    "url": request.url,
                    "timestamp": datetime.now().isoformat()
                })
            
            def log_response(response):
                network_logs.append({
                    "type": "response",
                    "method": response.request.method,
                    "url": response.url,
                    "status": response.status,
                    "timestamp": datetime.now().isoformat()
                })
            
            self.page.on("request", log_request)
            self.page.on("response", log_response)
            
            # Execute the script
            execution_result = await self._execute_script_code(script.code)
            
            # Capture final screenshot
            final_screenshot = self.screenshot_manager.get_screenshot_path("final")
            await self.page.screenshot(path=str(final_screenshot))
            
            # Update result
            result.success = execution_result.get("success", True)
            result.error_message = execution_result.get("error")
            result.screenshots = [str(s) for s in self.screenshot_manager.get_all_screenshots()]
            result.console_logs = console_logs
            result.network_logs = network_logs
            result.execution_time = time.time() - start_time
            
            print(f"✓ Execution completed in {result.execution_time:.2f}s")
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"✗ Execution failed: {error_msg}")
            
            # Capture error screenshot if page exists
            if self.page:
                try:
                    error_screenshot = self.screenshot_manager.get_screenshot_path("error")
                    await self.page.screenshot(path=str(error_screenshot))
                    result.screenshots = [str(s) for s in self.screenshot_manager.get_all_screenshots()]
                except:
                    pass
            
            result.success = False
            result.error_message = error_msg
            result.execution_time = time.time() - start_time
            
            # Get traceback
            tb = traceback.format_exc()
            result.console_logs.append(f"[ERROR] {tb}")
        
        finally:
            # Cleanup
            await self._cleanup()
            
            # Get video path
            if self.screenshot_manager:
                video = self.screenshot_manager.get_video()
                if video:
                    result.video_path = str(video)
        
        return result
    
    async def _execute_script_code(self, code: str) -> Dict[str, Any]:
        """Execute the actual script code"""
        
        # Create namespace for script execution
        namespace = {
            'page': self.page,
            'context': self.context,
            'browser': self.browser,
            'asyncio': asyncio,
            'screenshot_manager': self.screenshot_manager
        }
        
        try:
            # Execute the script
            exec(code, namespace)
            
            # Check if there's a run_automation function
            if 'run_automation' in namespace:
                result = await namespace['run_automation'](self.page)
                return result if isinstance(result, dict) else {"success": True, "result": result}
            
            # Check if there's a main function
            elif 'main' in namespace:
                result = await namespace['main']()
                return result if isinstance(result, dict) else {"success": True, "result": result}
            
            else:
                return {"success": True, "message": "Script executed successfully"}
                
        except Exception as e:
            return {
                "success": False,
                "error": f"{type(e).__name__}: {str(e)}",
                "traceback": traceback.format_exc()
            }
    
    async def _cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")
    
    def get_execution_summary(self, result: ExecutionResult) -> str:
        """Get a formatted summary of the execution"""
        
        status_emoji = "✓" if result.success else "✗"
        status_text = "SUCCESS" if result.success else "FAILED"
        
        summary = f"""
{status_emoji} Execution {status_text}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task ID: {result.task_id}
Script Version: v{result.script_version}
Duration: {result.execution_time:.2f}s
Executed: {result.executed_at.strftime('%Y-%m-%d %I:%M:%S %p')}

Artifacts:
  Screenshots: {len(result.screenshots)}
  Video: {'Yes' if result.video_path else 'No'}
  Console Logs: {len(result.console_logs)}
  Network Events: {len(result.network_logs)}
"""
        
        if not result.success and result.error_message:
            summary += f"\nError: {result.error_message}\n"
        
        return summary


# Convenience function for quick execution
async def execute_automation_script(script: GeneratedScript) -> ExecutionResult:
    """Quick function to execute a script"""
    agent = ExecutionEngineAgent()
    return await agent.execute_script(script)


# Example usage
if __name__ == "__main__":
    from agents.script_generator import generate_automation_script
    
    async def main():
        # Generate a simple script
        print("Generating script...")
        script = await generate_automation_script(
            "Navigate to example.com and take a screenshot",
            url="https://example.com"
        )
        
        # Execute it
        print("\nExecuting script...")
        agent = ExecutionEngineAgent()
        result = await agent.execute_script(script)
        
        # Print summary
        print(agent.get_execution_summary(result))
    
    asyncio.run(main())
