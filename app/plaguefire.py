from typing import Optional
import pygame
from app.lib.core.game_engine import Game
from app.model.player import Player

from app.lib.core.logger import debug, log_exception

class Plaguefire:
    def __init__(self, project_root):
        pygame.init()
        pygame.display.set_caption("Plaguefire")
        self.engine: Game = Game(project_root)
        self.engine.init()

    def run(self):
        while self.engine.running:
            dt = self.engine.clock.tick(60) / 1000
            events = pygame.event.get()

            for e in events:
                if e.type == pygame.QUIT:
                    # Ensure we stop the engine's main loop. Previously this
                    # set `self.running` which is a non-existent attribute on
                    # Plaguefire, so the engine kept running. Set the engine's
                    # running flag instead.
                    try:
                        self.engine.running = False
                    except Exception:
                        # Fallback: break out of the loop by returning from run
                        return

            self.engine.screens.handle_events(events)
            # Update sound manager (handles random ambient events)
            try:
                if hasattr(self.engine, 'sound') and self.engine.sound:
                    self.engine.sound.update()
            except Exception:
                pass
            current = self.engine.screens.current()
            if current:
                current.update(dt)

            self.engine.screens.draw(self.engine.surface)
            pygame.display.flip()

        pygame.quit()