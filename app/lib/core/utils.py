from rich.text import Text
from textual.widgets import Static

def colored_text(content: str, color: str, align: str = "center", **styles) -> Static:
    """
    Create a Textual Static widget that preserves Rich markup colors.

    Args:
        content (str): A string containing Rich markup, e.g. "[chartreuse1]Hello[/]".
        align (str): Horizontal text alignment ("left", "center", "right"). Default is "center".
        **styles: Any additional style overrides for the widget (e.g., background, padding).

    Returns:
        Static: A Textual Static widget ready to yield or mount.
    """
    widget = Static(Text.from_markup(f"[{color}]{content}[/{color}]"))
    widget.styles.text_align = align

    # Apply any extra styles you pass as kwargs
    for key, value in styles.items():
        setattr(widget.styles, key, value)

    return widget
