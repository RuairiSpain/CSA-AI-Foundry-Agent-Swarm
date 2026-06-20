"""Performance benchmarking"""

from typing import Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import statistics

@dataclass
class PerformanceMetric:
    name: str
    duration_ms: float

class PerformanceBenchmark:
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    async def measure(self, name: str, func: Callable, *args, **kwargs) -> float:
        start = datetime.now()
        try:
            result = func(*args, **kwargs)
        except:
            result = None
        elapsed = (datetime.now() - start).total_seconds() * 1000
        
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append(elapsed)
        return elapsed
    
    async def get_stats(self, name: str) -> Dict[str, float]:
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        times = self.metrics[name]
        return {
            "min_ms": min(times),
            "max_ms": max(times),
            "avg_ms": statistics.mean(times),
            "count": len(times),
        }

