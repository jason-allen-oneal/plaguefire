import pygame

class Screen:
    transparent = False

    def __init__(self, game):
        self.game = game

    def on_push(self): pass
    def on_pop(self): pass
    def handle_events(self, events): pass
    def update(self, dt): pass
    def draw(self, surface): pass

class FadeTransition(Screen):
    def __init__(self, game, new_screen, duration=0.5, mode: str = "replace"):
        super().__init__(game)
        self.new_screen = new_screen
        self.duration = duration
        self.time = 0
        self.phase = "fade_out"
        # mode: "replace" (default) replaces the screen under the transition;
        #       "push" inserts the new screen under the transition leaving the
        #       previous screen in the stack (good for modal overlays like shops).
        self.mode = mode
        self.overlay = pygame.Surface(game.surface.get_size()).convert_alpha()
        # Let underlying screens draw; this overlay will be composited on top
        self.transparent = True

    def update(self, dt):
        self.time += dt
        if self.phase == "fade_out":
            if self.time >= self.duration:
                # Swap or insert the screen UNDER this transition, keeping us on top
                if self.mode == "push":
                    self.game.screens.push_under_top(self.new_screen)
                else:
                    self.game.screens.replace_under_top(self.new_screen)
                self.phase = "fade_in"
                self.time = 0
        elif self.phase == "fade_in" and self.time >= self.duration:
            # Pop only the transition (we are still on top)
            self.game.screens.pop()

    def draw(self, surface):
        alpha = int(255 * (self.time / self.duration))
        if self.phase == "fade_in":
            alpha = 255 - alpha
        self.overlay.fill((0, 0, 0, max(0, min(255, alpha))))
        surface.blit(self.overlay, (0, 0))