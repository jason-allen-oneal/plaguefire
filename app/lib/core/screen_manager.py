
from app.screens.screen import Screen

class ScreenManager:
    def __init__(self, game) -> None:
        self.game = game
        self.stack: list[Screen] = []

    def push(self, screen: Screen):
        self.stack.append(screen)
        screen.on_push()

    def pop(self):
        if self.stack:
            s = self.stack.pop()
            s.on_pop()

    def remove(self, screen: Screen):
        """Remove a specific screen instance from the stack wherever it is.

        This is useful for screens that may not be the current top (for example
        when a transition overlay is above them) but still need to close them
        directly.
        """
        if screen in self.stack:
            # Call on_pop on the screen being removed
            self.stack.remove(screen)
            screen.on_pop()

    def replace(self, screen: Screen):
        self.pop()
        self.push(screen)

    def current(self):
        return self.stack[-1] if self.stack else None

    def replace_under_top(self, screen: Screen):
        """Replace the screen directly under the top of the stack.

        Useful for transitions: keep the transition on top while swapping the
        underlying screen so the overlay can fade over both old and new screens.
        """
        if not self.stack:
            # No screens; just push
            self.push(screen)
            return
        if len(self.stack) == 1:
            # Only one screen; normal replace
            self.replace(screen)
            return
        # Replace the screen at index -2
        old = self.stack[-2]
        old.on_pop()
        self.stack[-2] = screen
        screen.on_push()

    def push_under_top(self, screen: Screen):
        """Insert a screen directly under the current top (index -2).

        Useful with transitions: keep the transition on top, place the new
        screen beneath it so the overlay fades over both, and when the
        transition pops, the new screen remains above the previous one.
        """
        if not self.stack:
            self.push(screen)
            return
        # Insert before the last element (top)
        self.stack.insert(len(self.stack) - 1, screen)
        screen.on_push()

    def draw(self, surface):
        start = 0
        for i in range(len(self.stack) - 1, -1, -1):
            if not self.stack[i].transparent:
                start = i
                break
        for i in range(start, len(self.stack)):
            self.stack[i].draw(surface)

    def handle_events(self, events):
        """Route events to the topmost non-transparent screen.

        This lets transparent overlays (like transitions) sit above a screen
        without swallowing input events that should go to the screen beneath.
        """
        # Walk from the top down until we find a screen that is not
        # transparent. That screen should receive input events.
        # Debug: list stack top->bottom
        # Intentionally do not emit debug traces for ScreenManager stack routing.

        for i in range(len(self.stack) - 1, -1, -1):
            scr = self.stack[i]
            if not scr.transparent:
                try:
                    scr.handle_events(events)
                except Exception as e:
                    # Don't let a single screen's event error break the loop
                    from app.lib.core.logger import log_exception
                    log_exception(e)
                break

    # Removed debug helpers