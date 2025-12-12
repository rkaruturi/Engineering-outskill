"""
Cost tracking utilities for monitoring OpenRouter API usage.
Tracks tokens, calculates costs, and enforces budget limits.
"""

from typing import Dict, Optional
from datetime import datetime, date
from pathlib import Path
import json

from config import Config
from models import CostSummary


class CostTracker:
    """Track and manage API costs"""
    
    def __init__(self):
        self.summary = CostSummary()
        self.daily_costs: Dict[str, float] = {}
        self.session_start = datetime.now()
        self._load_daily_costs()
    
    def _load_daily_costs(self):
        """Load daily costs from file"""
        costs_file = Config.LOGS_DIR / "daily_costs.json"
        if costs_file.exists():
            try:
                with open(costs_file, 'r') as f:
                    self.daily_costs = json.load(f)
            except Exception:
                self.daily_costs = {}
    
    def _save_daily_costs(self):
        """Save daily costs to file"""
        costs_file = Config.LOGS_DIR / "daily_costs.json"
        try:
            with open(costs_file, 'w') as f:
                json.dump(self.daily_costs, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save daily costs: {e}")
    
    def calculate_cost(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """Calculate cost for a request"""
        
        pricing = Config.MODEL_PRICING.get(model)
        if not pricing:
            print(f"Warning: No pricing data for model {model}, using fallback")
            pricing = Config.MODEL_PRICING[Config.FALLBACK_MODEL]
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def track_request(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, float]:
        """Track a request and return cost information"""
        
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        # Update summary
        self.summary.total_requests += 1
        self.summary.total_input_tokens += input_tokens
        self.summary.total_output_tokens += output_tokens
        self.summary.total_cost += cost
        
        # Track by model
        if model not in self.summary.cost_by_model:
            self.summary.cost_by_model[model] = 0.0
        self.summary.cost_by_model[model] += cost
        
        # Track daily costs
        today = str(date.today())
        if today not in self.daily_costs:
            self.daily_costs[today] = 0.0
        self.daily_costs[today] += cost
        
        self._save_daily_costs()
        
        return {
            "cost": cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_session_cost": self.summary.total_cost,
            "total_daily_cost": self.daily_costs[today]
        }
    
    def check_budget(self, estimated_cost: float = 0.0) -> tuple[bool, str]:
        """Check if request would exceed budget limits"""
        
        today = str(date.today())
        daily_total = self.daily_costs.get(today, 0.0) + estimated_cost
        
        # Check daily budget
        if daily_total > Config.DAILY_BUDGET:
            return False, f"Would exceed daily budget: ${daily_total:.4f} / ${Config.DAILY_BUDGET:.2f}"
        
        # Check per-run budget
        if estimated_cost > Config.MAX_COST_PER_RUN:
            return False, f"Estimated cost ${estimated_cost:.4f} exceeds max per run ${Config.MAX_COST_PER_RUN:.2f}"
        
        return True, "Within budget"
    
    def get_summary(self) -> Dict:
        """Get cost summary as dictionary"""
        return {
            "session_start": self.session_start.isoformat(),
            "total_requests": self.summary.total_requests,
            "total_input_tokens": self.summary.total_input_tokens,
            "total_output_tokens": self.summary.total_output_tokens,
            "total_cost": round(self.summary.total_cost, 4),
            "daily_cost": round(self.daily_costs.get(str(date.today()), 0.0), 4),
            "cost_by_model": {k: round(v, 4) for k, v in self.summary.cost_by_model.items()},
            "average_cost_per_request": round(
                self.summary.total_cost / max(self.summary.total_requests, 1), 4
            )
        }
    
    def format_cost_report(self) -> str:
        """Format a human-readable cost report"""
        summary = self.get_summary()
        
        report = f"""
╔══════════════════════════════════════════╗
║         API COST SUMMARY                 ║
╚══════════════════════════════════════════╝

Session Duration: {(datetime.now() - self.session_start).seconds // 60} minutes
Total Requests: {summary['total_requests']}

Tokens:
  Input:  {summary['total_input_tokens']:,}
  Output: {summary['total_output_tokens']:,}

Costs:
  This Session: ${summary['total_cost']:.4f}
  Today:        ${summary['daily_cost']:.4f}
  Avg/Request:  ${summary['average_cost_per_request']:.4f}

Budget Status:
  Daily Limit:  ${Config.DAILY_BUDGET:.2f}
  Remaining:    ${Config.DAILY_BUDGET - summary['daily_cost']:.2f}
"""
        
        if summary['cost_by_model']:
            report += "\nCost by Model:\n"
            for model, cost in summary['cost_by_model'].items():
                model_name = model.split('/')[-1]
                report += f"  {model_name}: ${cost:.4f}\n"
        
        return report


# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get or create the global cost tracker"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
