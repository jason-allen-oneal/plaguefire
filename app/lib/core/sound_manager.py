import pygame
from pathlib import Path
from debugtools import debug, log_exception


class SoundManager:
    """Properly separates background music and SFX using different mixer channels."""

    def __init__(self, sound_dir: str = "assets/sounds"):
        self.sound_dir = Path(sound_dir)

        # Distinct flags
        self.music_enabled = True
        self.sfx_enabled = True

        # Cache + state
        self.sounds = {}
        self.music_playing = None

        try:
            pygame.mixer.init()
            debug("Sound system initialized.")
        except Exception as e:
            log_exception(f"Failed to initialize sound: {e}")
            self.music_enabled = False
            self.sfx_enabled = False

        # Reserve a dedicated channel for SFX playback
        self.sfx_channel = pygame.mixer.Channel(1)

    # ---------- MUSIC ----------
    def play_music(self, filename: str, loop: bool = True, volume: float = 0.6):
        """Plays looping background music separately from SFX."""
        if not self.music_enabled:
            return
        try:
            path = self.sound_dir / "music" / filename
            if not path.exists():
                debug(f"Missing music file: {path}")
                return
            if self.music_playing == filename:
                return  # Already playing
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self.music_playing = filename
            debug(f"Now playing music: {filename}")
        except Exception as e:
            log_exception(f"Music playback error: {e}")

    def stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.music_playing = None
        debug("Music stopped.")

    def set_music_enabled(self, enabled: bool):
        """Enable/disable background music."""
        previously_playing = self.music_playing
        self.music_enabled = enabled
        if not enabled:
            pygame.mixer.music.stop()
        else:
            # Resume the last track if known
            if previously_playing:
                self.play_music(previously_playing)
        debug(f"Music {'enabled' if enabled else 'disabled'}.")


    # ---------- SFX ----------
    def load_sfx(self, name: str, filename: str, volume: float = 1.0):
        """Preload a short sound effect."""
        try:
            path = self.sound_dir / "sfx" / filename
            if not path.exists():
                debug(f"SFX not found: {path}")
                return
            sound = pygame.mixer.Sound(path)
            sound.set_volume(volume)
            self.sounds[name] = sound
            debug(f"Loaded SFX: {name}")
        except Exception as e:
            log_exception(f"Failed to load SFX {filename}: {e}")

    def play_sfx(self, name: str):
        """Play a sound effect on the dedicated SFX channel."""
        if not self.sfx_enabled:
            return
        try:
            sound = self.sounds.get(name)
            if sound:
                self.sfx_channel.play(sound)
                debug(f"Played SFX: {name}")
            else:
                debug(f"Missing SFX: {name}")
        except Exception as e:
            log_exception(f"Failed to play SFX {name}: {e}")

    def set_sfx_enabled(self, enabled: bool):
        self.sfx_enabled = enabled
        debug(f"SFX {'enabled' if enabled else 'disabled'}.")
