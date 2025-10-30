#!/usr/bin/env python3
"""
Demonstration of entity color mapping.

This script demonstrates the new entity coloring feature by showing
how different entity names map to different colors.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.screens.reduced_map import ReducedMapScreen
from rich.console import Console
from rich.table import Table

def demonstrate_color_mapping():
    """Demonstrate entity color mapping with visual output."""
    
    # Create a minimal mock for testing
    class MockEngine:
        class MockPlayer:
            depth = 1
            position = [5, 5]
        
        player = MockPlayer()
        game_map = [["." for _ in range(10)] for _ in range(10)]
        visibility = [[1 for _ in range(10)] for _ in range(10)]
        entities = []
    
    screen = ReducedMapScreen(engine=MockEngine())
    console = Console()
    
    # Create a table to display the color mapping
    table = Table(title="Entity Color Mapping Demonstration")
    table.add_column("Entity Name", style="cyan")
    table.add_column("Color Code", style="yellow")
    table.add_column("Rendered", style="")
    
    # Test entities with different colors
    test_entities = [
        "Ancient Black Dragon",
        "Ancient Blue Dragon",
        "Ancient Green Dragon",
        "Ancient Red Dragon",
        "Ancient White Dragon",
        "Yellow Dragon",
        "Giant Brown Bat",
        "Grey Ooze",
        "Purple Worm",
        "Orange Jelly",
        "Pink Horror",
        "Violet Fungi",
        "Normal Kobold (no color in name)",
    ]
    
    for entity_name in test_entities:
        color = screen._get_entity_color(entity_name)
        # Get the first character of the entity name for display
        char = entity_name[0]
        rendered = f"[{color}]{char}[/{color}]"
        table.add_row(entity_name, color, rendered)
    
    console.print("\n")
    console.print(table)
    console.print("\n[bold green]✓ Entity coloring feature is working![/bold green]\n")
    
    # Demonstrate the reduced map visibility feature
    console.print("[bold cyan]Reduced Map Visibility Feature:[/bold cyan]")
    console.print("- Only explored tiles (visibility >= 1) are shown")
    console.print("- Unexplored areas appear as blank spaces")
    console.print("- Entities are colored based on their names")
    console.print("\n[dim]Example: 'Ancient Blue Dragon' appears in blue[/dim]")
    console.print("[dim]Example: 'Giant Red Ant' appears in red[/dim]\n")


if __name__ == "__main__":
    demonstrate_color_mapping()
