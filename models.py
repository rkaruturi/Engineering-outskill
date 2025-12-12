"""
Data models for the self-healing browser automation system.
Uses Pydantic for validation and serialization.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of an automation task"""
    PENDING = "pending"
    GENERATING = "generating"
    EXECUTING = "executing"
    DIAGNOSING = "diagnosing"
    REPAIRING = "repairing"
    SUCCESS = "success"
    FAILED = "failed"


class ErrorType(str, Enum):
    """Types of errors that can occur during execution"""
    SELECTOR_NOT_FOUND = "selector_not_found"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    JAVASCRIPT_ERROR = "javascript_error"
    CRASH = "crash"
    UNEXPECTED_STATE = "unexpected_state"
    UNKNOWN = "unknown"


class AutomationTask(BaseModel):
    """Natural language automation task"""
    id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    description: str
    url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GeneratedScript(BaseModel):
    """LLM-generated Playwright script"""
    task_id: str
    code: str
    language: str = "python"
    model_used: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1  # Increments with each repair


class ExecutionResult(BaseModel):
    """Result of script execution"""
    task_id: str
    script_version: int
    success: bool
    error_message: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    video_path: Optional[str] = None
    console_logs: List[str] = Field(default_factory=list)
    network_logs: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time: float = 0.0  # seconds
    executed_at: datetime = Field(default_factory=datetime.now)


class ErrorDiagnosis(BaseModel):
    """Analysis of execution failure"""
    task_id: str
    error_type: ErrorType
    error_message: str
    error_context: Dict[str, Any] = Field(default_factory=dict)
    suggested_fixes: List[str] = Field(default_factory=list)
    confidence: float = 0.0  # 0.0 to 1.0
    diagnosed_at: datetime = Field(default_factory=datetime.now)


class RepairAttempt(BaseModel):
    """Attempt to fix a failed script"""
    task_id: str
    original_version: int
    repaired_script: GeneratedScript
    repair_strategy: str
    diagnosis_used: ErrorDiagnosis
    success: bool = False
    attempt_number: int = 1


class TestRun(BaseModel):
    """Complete test run with all stages"""
    task: AutomationTask
    scripts: List[GeneratedScript] = Field(default_factory=list)
    executions: List[ExecutionResult] = Field(default_factory=list)
    diagnoses: List[ErrorDiagnosis] = Field(default_factory=list)
    repairs: List[RepairAttempt] = Field(default_factory=list)
    final_status: TaskStatus = TaskStatus.PENDING
    total_cost: float = 0.0
    completed_at: Optional[datetime] = None
    
    def add_cost(self, cost: float):
        """Add to total cost"""
        self.total_cost += cost
    
    def mark_complete(self, status: TaskStatus):
        """Mark test run as complete"""
        self.final_status = status
        self.completed_at = datetime.now()


class CostSummary(BaseModel):
    """Summary of API costs"""
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    cost_by_model: Dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
