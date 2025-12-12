"""
Error Diagnosis Agent - Analyzes execution failures and classifies errors.
Provides detailed diagnostic information for script repair.
"""

import json
import re
from typing import Dict, List, Optional
from openai import OpenAI

from config import Config
from models import ExecutionResult, ErrorDiagnosis, ErrorType
from utils import PromptTemplates, get_cost_tracker


class ErrorDiagnosisAgent:
    """Diagnoses automation script failures"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=Config.OPENROUTER_BASE_URL,
            api_key=Config.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://github.com/self-healing-automation",
                "X-Title": "Self-Healing Browser Automation"
            },
            timeout=60.0
        )
        self.cost_tracker = get_cost_tracker()
        self.model = Config.DEFAULT_MODEL
    
    async def diagnose_error(self, result: ExecutionResult) -> ErrorDiagnosis:
        """Analyze an execution failure and provide diagnosis"""
        
        if result.success:
            raise ValueError("Cannot diagnose a successful execution")
        
        print(f"🔍 Diagnosing error for task {result.task_id}")
        
        # Try rule-based diagnosis first (cheaper)
        rule_based = self._rule_based_diagnosis(result)
        
        # Use LLM for complex cases or low confidence
        if rule_based.confidence < 0.7:
            print("  Using LLM for detailed analysis...")
            llm_diagnosis = await self._llm_diagnosis(result)
            return llm_diagnosis
        else:
            print(f"  Rule-based diagnosis (confidence: {rule_based.confidence:.2f})")
            return rule_based
    
    def _rule_based_diagnosis(self, result: ExecutionResult) -> ErrorDiagnosis:
        """Fast rule-based error classification"""
        
        error_msg = result.error_message or ""
        error_msg_lower = error_msg.lower()
        
        # Initialize diagnosis
        error_type = ErrorType.UNKNOWN
        root_cause = error_msg
        suggested_fixes = []
        confidence = 0.5
        
        # Selector errors
        if any(keyword in error_msg_lower for keyword in [
            "element not found", "no element", "selector", "locator", 
            "could not find", "elementhandle"
        ]):
            error_type = ErrorType.SELECTOR_NOT_FOUND
            root_cause = "Element selector could not locate the target element"
            suggested_fixes = [
                "Try alternative selectors (CSS, XPath, text content)",
                "Add explicit wait: await page.wait_for_selector()",
                "Check if element is in iframe or shadow DOM",
                "Verify element is visible and not hidden by CSS"
            ]
            confidence = 0.8
        
        # Timeout errors
        elif any(keyword in error_msg_lower for keyword in [
            "timeout", "timed out", "exceeded"
        ]):
            error_type = ErrorType.TIMEOUT
            root_cause = "Operation exceeded time limit"
            suggested_fixes = [
                "Increase timeout: timeout=60000",
                "Wait for network idle: wait_until='networkidle'",
                "Add retry logic with exponential backoff",
                "Check if page is loading too slowly"
            ]
            confidence = 0.85
        
        # Network errors
        elif any(keyword in error_msg_lower for keyword in [
            "network", "connection", "dns", "refused", "unreachable", "net::"
        ]):
            error_type = ErrorType.NETWORK_ERROR
            root_cause = "Network connectivity or DNS resolution failure"
            suggested_fixes = [
                "Verify URL is correct and accessible",
                "Check internet connection",
                "Add retry logic for failed requests",
                "Handle offline scenarios gracefully"
            ]
            confidence = 0.9
        
        # JavaScript errors
        elif any(keyword in error_msg_lower for keyword in [
            "javascript", "uncaught", "reference error", "type error"
        ]):
            error_type = ErrorType.JAVASCRIPT_ERROR
            root_cause = "JavaScript runtime error on the page"
            suggested_fixes = [
                "Check browser console for detailed errors",
                "Wait for page JavaScript to load completely",
                "Try different browser or version",
                "Disable problematic scripts if possible"
            ]
            confidence = 0.75
        
        # Crash errors
        elif any(keyword in error_msg_lower for keyword in [
            "crash", "terminated", "killed", "segmentation fault"
        ]):
            error_type = ErrorType.CRASH
            root_cause = "Browser or process crashed unexpectedly"
            suggested_fixes = [
                "Increase memory limits",
                "Try headless mode",
                "Update Playwright/browser version",
                "Check system resources"
            ]
            confidence = 0.7
        
        # Build error context
        error_context = {
            "error_message": result.error_message,
            "execution_time": result.execution_time,
            "screenshots_available": len(result.screenshots),
            "console_errors": [log for log in result.console_logs if "[error]" in log.lower()][:5],
            "failed_requests": [log for log in result.network_logs if log.get("status", 200) >= 400][:5]
        }
        
        return ErrorDiagnosis(
            task_id=result.task_id,
            error_type=error_type,
            error_message=root_cause,
            error_context=error_context,
            suggested_fixes=suggested_fixes,
            confidence=confidence
        )
    
    async def _llm_diagnosis(self, result: ExecutionResult) -> ErrorDiagnosis:
        """Use LLM for detailed error analysis"""
        
        # Build diagnosis prompt
        prompt = PromptTemplates.error_diagnosis_prompt(
            error_message=result.error_message or "Unknown error",
            console_logs=result.console_logs,
            network_logs=result.network_logs,
            screenshot_available=len(result.screenshots) > 0
        )
        
        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PromptTemplates.get_system_message("diagnostician")},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            # Track costs
            usage = response.usage
            cost_info = self.cost_tracker.track_request(
                model=self.model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens
            )
            
            # Parse JSON response
            diagnosis_json = self._extract_json(response.choices[0].message.content)
            
            # Map string error_type to ErrorType enum
            error_type_str = diagnosis_json.get("error_type", "unknown")
            try:
                error_type = ErrorType[error_type_str.upper()]
            except KeyError:
                error_type = ErrorType.UNKNOWN
            
            return ErrorDiagnosis(
                task_id=result.task_id,
                error_type=error_type,
                error_message=diagnosis_json.get("root_cause", result.error_message),
                error_context={
                    "llm_cost": cost_info['cost'],
                    "original_error": result.error_message
                },
                suggested_fixes=diagnosis_json.get("suggested_fixes", []),
                confidence=diagnosis_json.get("confidence", 0.5)
            )
            
        except Exception as e:
            print(f"  LLM diagnosis failed: {e}, falling back to rule-based")
            return self._rule_based_diagnosis(result)
    
    def _extract_json(self, response: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try to find JSON in the response
        try:
            # First try direct parsing
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            pattern = r"```(?:json)?\n(.*?)```"
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return json.loads(matches[0])
            raise ValueError("Could not extract valid JSON from response")
    
    def get_diagnosis_summary(self, diagnosis: ErrorDiagnosis) -> str:
        """Format diagnosis as human-readable summary"""
        
        return f"""
🔍 ERROR DIAGNOSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Error Type: {diagnosis.error_type.value.upper()}
Confidence: {diagnosis.confidence * 100:.0f}%

Root Cause:
{diagnosis.error_message}

Suggested Fixes:
{chr(10).join(f"  {i+1}. {fix}" for i, fix in enumerate(diagnosis.suggested_fixes))}

Additional Context:
{chr(10).join(f"  • {k}: {v}" for k, v in diagnosis.error_context.items() if k != 'llm_cost')}
"""


# Convenience function
async def diagnose_execution_error(result: ExecutionResult) -> ErrorDiagnosis:
    """Quick function to diagnose an error"""
    agent = ErrorDiagnosisAgent()
    return await agent.diagnose_error(result)
