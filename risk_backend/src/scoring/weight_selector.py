import yaml
import os
from typing import Dict

class WeightSelector:
    def __init__(self, config_path: str = 'config/risk_weights.yaml'):
        self.weights = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.weights = yaml.safe_load(f) or {}

    def get_weights(self, industry: str) -> Dict[str, float]:
        industry_lower = industry.lower() if industry else 'default'
        return self.weights.get(industry_lower, self.weights.get('default', {
            'PROBLEM': 1.0,
            'MARKET': 1.0,
            'PMF': 1.0,
            'COMPETITION': 1.0,
            'BUSINESS_MODEL': 1.0,
            'FINANCIAL': 1.0,
            'TECHNOLOGY': 1.0,
            'REGULATORY': 1.0,
            'OPERATIONAL': 1.0,
            'TEAM': 1.0,
            'FUNDING': 1.0,
            'MACRO': 1.0
        }))
