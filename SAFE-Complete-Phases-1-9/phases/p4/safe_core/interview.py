"""Interactive interview loop for route creation"""

import json
from typing import Dict, List, Optional
from enum import Enum
from .models import RoutePattern, RouteDefinition, Agent, ValidationError
from .agent_catalog import AgentCatalog

class InterviewStep(str, Enum):
    """Steps in the interview"""
    PATTERN = "pattern"
    AGENTS = "agents"
    LOGIC = "logic"
    TIMEOUTS = "timeouts"
    METADATA = "metadata"
    REVIEW = "review"

class RouteInterviewer:
    """Interactive interviewer for route creation"""
    
    def __init__(self, catalog: AgentCatalog):
        self.catalog = catalog
        self.current_step = InterviewStep.PATTERN
        self.route_def = None
        self.history = []  # For going back
        
    async def start_interview(self) -> RouteDefinition:
        """Start interactive interview loop"""
        
        print("\n" + "="*60)
        print("SAFE Route Writer Agent - Interactive Interview")
        print("="*60)
        print("\nLet's create a new route! You can go back at any time.\n")
        
        # Step 1: Pattern selection
        pattern = await self._ask_pattern()
        
        # Step 2: Agent selection
        agents = await self._ask_agents(pattern)
        
        # Step 3: Logic configuration
        routing_field, routing_rules = await self._ask_logic(pattern, agents)
        
        # Step 4: Timeouts
        total_timeout, per_agent_timeout = await self._ask_timeouts(agents)
        
        # Step 5: Metadata
        name, description, csa_email = await self._ask_metadata()
        
        # Create route definition
        self.route_def = RouteDefinition(
            name=name,
            pattern=pattern,
            agents=agents,
            description=description,
            timeout_seconds=total_timeout,
            per_agent_timeout_seconds=per_agent_timeout,
            csa_email=csa_email,
            routing_field=routing_field,
            routing_rules=routing_rules,
        )
        
        # Step 6: Review
        confirmed = await self._review_and_confirm()
        
        if not confirmed:
            print("\nRoute creation cancelled.")
            return None
        
        print("\n✓ Route definition created!")
        return self.route_def
    
    async def _ask_pattern(self) -> RoutePattern:
        """Ask user to select a pattern"""
        print("\n--- Step 1: Select Pattern ---")
        print("\nWhat pattern do you need?\n")
        print("1. Supervisor-Manager")
        print("   └─ Route requests to different specialists")
        print("   └─ Best for: Decision routing (loan type → specialist)\n")
        
        print("2. Fan-Out/Fan-In")
        print("   └─ Process in parallel, then combine results")
        print("   └─ Best for: Multi-source data gathering\n")
        
        print("3. Map-Reduce")
        print("   └─ Transform/aggregate large datasets")
        print("   └─ Best for: Batch processing, transformations\n")
        
        print("4. Sequential-Pipeline")
        print("   └─ Step-by-step processing")
        print("   └─ Best for: Extract → Clean → Enrich\n")
        
        while True:
            choice = input("Choose (1-4, or 'b' to go back): ").strip()
            
            pattern_map = {
                "1": RoutePattern.SUPERVISOR_MANAGER,
                "2": RoutePattern.FAN_OUT_FAN_IN,
                "3": RoutePattern.MAP_REDUCE,
                "4": RoutePattern.SEQUENTIAL_PIPELINE,
            }
            
            if choice in pattern_map:
                selected = pattern_map[choice]
                print(f"\n✓ Selected: {selected.value}")
                return selected
            elif choice == 'b':
                print("Cannot go back from first step.")
                continue
            else:
                print("Invalid choice. Please enter 1-4.")
    
    async def _ask_agents(self, pattern: RoutePattern) -> Dict[str, Agent]:
        """Ask user to select agents for the pattern"""
        print(f"\n--- Step 2: Select Agents for {pattern.value} ---\n")
        
        agents = {}
        
        if pattern == RoutePattern.SUPERVISOR_MANAGER:
            # Supervisor
            supervisor = await self._select_agent(
                role="Supervisor (routes requests)",
                category="supervisor",
                required=True
            )
            agents["supervisor"] = supervisor
            
            # Specialists
            specialist_count = int(input("\nHow many specialists? (2-5): ") or "2")
            specialist_count = max(2, min(5, specialist_count))
            
            for i in range(specialist_count):
                specialist = await self._select_agent(
                    role=f"Specialist {i+1}",
                    category="specialist",
                    required=True
                )
                agents[f"specialist_{i}"] = specialist
            
            # Aggregator
            aggregator = await self._select_agent(
                role="Aggregator (combines results)",
                category="aggregator",
                required=True
            )
            agents["aggregator"] = aggregator
        
        elif pattern == RoutePattern.FAN_OUT_FAN_IN:
            # Parallel processors
            processor_count = int(input("\nHow many parallel processors? (2-5): ") or "2")
            processor_count = max(2, min(5, processor_count))
            
            for i in range(processor_count):
                processor = await self._select_agent(
                    role=f"Processor {i+1}",
                    category="processor",
                    required=True
                )
                agents[f"processor_{i}"] = processor
            
            # Aggregator
            aggregator = await self._select_agent(
                role="Aggregator",
                category="aggregator",
                required=True
            )
            agents["aggregator"] = aggregator
        
        elif pattern == RoutePattern.MAP_REDUCE:
            agents["splitter"] = await self._select_agent("Splitter", "splitter")
            agents["mapper"] = await self._select_agent("Mapper", "mapper")
            agents["reducer"] = await self._select_agent("Reducer", "reducer")
        
        elif pattern == RoutePattern.SEQUENTIAL_PIPELINE:
            stage_count = int(input("\nHow many stages? (2-5): ") or "2")
            stage_count = max(2, min(5, stage_count))
            
            for i in range(stage_count):
                stage = await self._select_agent(
                    role=f"Stage {i+1}",
                    category="processor",
                    required=True
                )
                agents[f"stage_{i}"] = stage
        
        print(f"\n✓ Selected {len(agents)} agents")
        return agents
    
    async def _select_agent(self, role: str, category: str, required: bool = True) -> Agent:
        """Help user select a single agent"""
        print(f"\n{role}:")
        
        # Get recommendations
        recommended = self.catalog.search_by_category(category)[:3]
        
        print(f"Recommended agents:")
        for i, agent in enumerate(recommended, 1):
            print(f"  {i}. {agent.name} (⭐{'⭐'*(5-i)})")
        
        while True:
            search = input(f"\nSearch agent name or press Enter for recommendation: ").strip()
            
            if not search:
                # Use first recommendation
                selected = recommended[0] if recommended else None
            else:
                # Search
                results = self.catalog.search_by_name(search)
                if not results:
                    print(f"No agents found matching '{search}'")
                    continue
                
                if len(results) == 1:
                    selected = results[0]
                else:
                    # Multiple matches
                    for i, agent in enumerate(results[:5], 1):
                        print(f"  {i}. {agent.name}")
                    choice = input("Select (1-5): ")
                    try:
                        selected = results[int(choice) - 1]
                    except (ValueError, IndexError):
                        print("Invalid choice")
                        continue
            
            if selected:
                print(f"✓ Selected: {selected.name}")
                return selected
    
    async def _ask_logic(self, pattern: RoutePattern, agents: Dict[str, Agent]) -> tuple:
        """Ask about route logic configuration"""
        print(f"\n--- Step 3: Configure Logic ---\n")
        
        routing_field = None
        routing_rules = {}
        
        if pattern == RoutePattern.SUPERVISOR_MANAGER:
            supervisor = agents["supervisor"]
            input_schema = supervisor.input_schema
            
            print("Routing field (which input field determines routing):\n")
            
            # List input fields
            if "properties" in input_schema:
                fields = list(input_schema["properties"].keys())
                for i, field in enumerate(fields, 1):
                    print(f"  {i}. {field}")
                
                choice = input(f"\nChoose field (1-{len(fields)}): ").strip()
                try:
                    routing_field = fields[int(choice) - 1]
                except (ValueError, IndexError):
                    routing_field = fields[0]
                
                print(f"✓ Routing field: {routing_field}")
        
        return routing_field, routing_rules
    
    async def _ask_timeouts(self, agents: Dict[str, Agent]) -> tuple:
        """Ask about timeout configuration"""
        print(f"\n--- Step 4: Configure Timeouts ---\n")
        
        print("Total route timeout (seconds): ")
        total_timeout = int(input("Default (120): ") or "120")
        
        print("\nPer-agent timeout (seconds): ")
        per_agent_timeout = int(input("Default (60): ") or "60")
        
        # Validate
        if total_timeout < per_agent_timeout:
            print(f"⚠ Warning: Total timeout ({total_timeout}s) < per-agent ({per_agent_timeout}s)")
            print("Adjusting total timeout...")
            total_timeout = per_agent_timeout * 2
        
        print(f"\n✓ Timeout: {total_timeout}s total, {per_agent_timeout}s per agent")
        return total_timeout, per_agent_timeout
    
    async def _ask_metadata(self) -> tuple:
        """Ask for route metadata"""
        print(f"\n--- Step 5: Route Information ---\n")
        
        name = input("Route name (lowercase, hyphens): ").strip()
        if not name:
            name = "my-route"
        
        description = input("Description (optional): ").strip()
        csa_email = input("Your email (for audit trail): ").strip()
        
        print(f"\n✓ Route: {name}")
        return name, description, csa_email
    
    async def _review_and_confirm(self) -> bool:
        """Review route and ask for confirmation"""
        print(f"\n--- Step 6: Review ---\n")
        
        print(f"Route: {self.route_def.name}")
        print(f"Pattern: {self.route_def.pattern.value}")
        print(f"Agents: {len(self.route_def.agents)}")
        print(f"  - " + "\n  - ".join(self.route_def.agents.keys()))
        print(f"Timeouts: {self.route_def.timeout_seconds}s total, {self.route_def.per_agent_timeout_seconds}s per agent")
        print(f"Description: {self.route_def.description}")
        
        while True:
            response = input("\nConfirm and generate? (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False

