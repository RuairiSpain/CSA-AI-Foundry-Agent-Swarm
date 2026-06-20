"""Agent catalog - provides access to available agents"""

import json
from typing import List, Optional, Dict, Any
from .models import Agent

class AgentCatalog:
    """Catalog of available agents"""
    
    # Hardcoded catalog (in production, would load from YAML)
    AGENTS = {
        "loan-supervisor-router": Agent(
            name="loan-supervisor-router",
            category="supervisor",
            version="1.0",
            description="Routes loan applications to specialists",
            input_schema={
                "type": "object",
                "required": ["amount", "loan_type", "credit_score"],
                "properties": {
                    "amount": {"type": "number"},
                    "loan_type": {"type": "string"},
                    "credit_score": {"type": "integer"}
                }
            },
            output_schema={
                "type": "object",
                "required": ["loan_type", "specialist", "amount", "credit_score"],
                "properties": {
                    "loan_type": {"type": "string"},
                    "specialist": {"type": "string"},
                    "amount": {"type": "number"},
                    "credit_score": {"type": "integer"}
                }
            }
        ),
        "loan-specialist-mortgage": Agent(
            name="loan-specialist-mortgage",
            category="specialist",
            version="1.0",
            description="Analyzes mortgage loan applications",
            input_schema={
                "type": "object",
                "required": ["amount", "credit_score"],
                "properties": {
                    "amount": {"type": "number"},
                    "credit_score": {"type": "integer"}
                }
            },
            output_schema={
                "type": "object",
                "required": ["decision", "confidence"],
                "properties": {
                    "decision": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        ),
        "loan-specialist-auto": Agent(
            name="loan-specialist-auto",
            category="specialist",
            version="1.0",
            description="Analyzes auto loan applications",
            input_schema={
                "type": "object",
                "required": ["amount", "credit_score"],
                "properties": {
                    "amount": {"type": "number"},
                    "credit_score": {"type": "integer"}
                }
            },
            output_schema={
                "type": "object",
                "required": ["decision", "confidence"],
                "properties": {
                    "decision": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        ),
        "loan-specialist-personal": Agent(
            name="loan-specialist-personal",
            category="specialist",
            version="1.0",
            description="Analyzes personal loan applications",
            input_schema={
                "type": "object",
                "required": ["amount", "credit_score"],
                "properties": {
                    "amount": {"type": "number"},
                    "credit_score": {"type": "integer"}
                }
            },
            output_schema={
                "type": "object",
                "required": ["decision", "confidence"],
                "properties": {
                    "decision": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        ),
        "standard-aggregator": Agent(
            name="standard-aggregator",
            category="aggregator",
            version="1.0",
            description="Combines decisions from multiple specialists",
            input_schema={
                "type": "object",
                "required": ["decisions"],
                "properties": {
                    "decisions": {"type": "array"}
                }
            },
            output_schema={
                "type": "object",
                "required": ["final_decision", "confidence"],
                "properties": {
                    "final_decision": {"type": "string"},
                    "confidence": {"type": "number"}
                }
            }
        ),
    }
    
    def search_by_name(self, query: str) -> List[Agent]:
        """Search agents by name"""
        query = query.lower()
        return [
            agent for agent in self.AGENTS.values()
            if query in agent.name.lower()
        ]
    
    def search_by_category(self, category: str) -> List[Agent]:
        """Search agents by category"""
        return [
            agent for agent in self.AGENTS.values()
            if agent.category == category
        ]
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get agent by name"""
        return self.AGENTS.get(name)
    
    def list_all(self) -> List[Agent]:
        """List all agents"""
        return list(self.AGENTS.values())

