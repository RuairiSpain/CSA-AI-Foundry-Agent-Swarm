"""CLI commands for Route Writer Agent"""

import sys
import asyncio
import os
from pathlib import Path
from safe_core.interview import RouteInterviewer
from safe_core.code_generator import RouteCodeGenerator
from safe_core.validator import ContractValidator
from safe_core.agent_catalog import AgentCatalog

class RouteCLI:
    """CLI interface for route operations"""
    
    def __init__(self):
        self.catalog = AgentCatalog()
        self.routes_dir = Path("routes")
        self.routes_dir.mkdir(exist_ok=True)
    
    async def create_route(self, dry_run: bool = False) -> bool:
        """Create a new route interactively"""
        
        print("\n" + "="*70)
        print("SAFE Framework - Route Writer Agent")
        print("="*70)
        
        # Run interview
        interviewer = RouteInterviewer(self.catalog)
        route_def = await interviewer.start_interview()
        
        if not route_def:
            print("\n✗ Route creation cancelled")
            return False
        
        # Validate
        print("\n✓ Validating contracts...")
        errors = ContractValidator.validate_route(route_def)
        
        if errors:
            print("\n✗ Validation errors:\n")
            for error in errors:
                print(f"  • {error.error_type}: {error.message}")
                for solution in error.suggested_solutions:
                    print(f"    → {solution}")
            print("\nPlease fix these issues and try again.")
            return False
        
        print("✓ All validations passed!")
        
        # Generate code
        print("\n✓ Generating route code...")
        generated = RouteCodeGenerator.generate(route_def)
        
        # Save or preview
        if dry_run:
            print("\n--- GENERATED CODE (--dry-run mode) ---\n")
            print(generated.route_code[:500] + "...")
            print("\nRoute code generated but not saved (--dry-run mode)")
            return True
        
        # Save to disk
        route_dir = self.routes_dir / route_def.name / "v1.0"
        route_dir.mkdir(parents=True, exist_ok=True)
        
        generated.save_to_disk(str(route_dir))
        
        print(f"\n✓ Route created: {route_dir}")
        print(f"  ├─ route.py")
        print(f"  ├─ requirements.txt")
        print(f"  ├─ config.yaml")
        print(f"  └─ test_data.json")
        
        print(f"\nNext steps:")
        print(f"  1. Review generated code:")
        print(f"     safe route show {route_def.name}")
        print(f"  2. Deploy route:")
        print(f"     safe route deploy {route_def.name}")
        print(f"  3. Monitor route:")
        print(f"     safe route health {route_def.name}")
        
        return True
    
    def show_route(self, route_name: str) -> bool:
        """Show generated route code"""
        
        route_path = self.routes_dir / route_name / "v1.0" / "route.py"
        
        if not route_path.exists():
            print(f"✗ Route not found: {route_name}")
            return False
        
        with open(route_path) as f:
            code = f.read()
        
        print(f"\n{'='*70}")
        print(f"Route: {route_name}")
        print(f"{'='*70}\n")
        print(code)
        
        return True
    
    def list_routes(self) -> bool:
        """List all routes"""
        
        routes = list(self.routes_dir.glob("*/v1.0"))
        
        if not routes:
            print("\nNo routes found")
            return True
        
        print(f"\n{'='*70}")
        print("Available Routes")
        print(f"{'='*70}\n")
        
        for route in sorted(routes):
            route_name = route.parent.name
            config_file = route / "config.yaml"
            
            if config_file.exists():
                with open(config_file) as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith("description:"):
                            description = line.split(":", 1)[1].strip()
                            break
                    else:
                        description = "(no description)"
            else:
                description = "(no description)"
            
            print(f"  • {route_name}")
            print(f"    {description}\n")
        
        return True

async def main():
    """Main CLI entry point"""
    
    cli = RouteCLI()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  safe route create [--dry-run]")
        print("  safe route show <name>")
        print("  safe route list")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        dry_run = "--dry-run" in sys.argv
        await cli.create_route(dry_run=dry_run)
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: safe route show <name>")
            return
        cli.show_route(sys.argv[2])
    elif command == "list":
        cli.list_routes()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    asyncio.run(main())

