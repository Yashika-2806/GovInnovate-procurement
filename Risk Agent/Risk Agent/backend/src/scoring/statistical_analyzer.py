from typing import List, Dict, Any
from collections import Counter
from src.models.research_data import FailedStartup, SuccessfulStartup

class StatisticalAnalyzer:
    def analyze(self, failures: List[FailedStartup], successes: List[SuccessfulStartup]) -> Dict[str, Any]:
        failure_causes = []
        for failure in failures:
            if failure.failure_causes:
                failure_causes.extend([cause.value for cause in failure.failure_causes])
                
        success_factors = []
        for success in successes:
            if success.success_factors:
                success_factors.extend(success.success_factors)
                
        failure_cause_freq = dict(Counter(failure_causes))
        success_factor_freq = dict(Counter(success_factors))
        
        return {
            'failure_cause_frequency': failure_cause_freq,
            'success_factor_frequency': success_factor_freq,
            'sample_size': {
                'failures': len(failures),
                'successes': len(successes)
            },
            'data_quality_notes': 'Insufficient sample size for strong statistical significance.' if len(failures) < 5 or len(successes) < 5 else 'Good sample size for analysis.'
        }
