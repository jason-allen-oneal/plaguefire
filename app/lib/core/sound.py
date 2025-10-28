"""
Sound and music management system.

This module provides the SoundManager class which handles background music
and sound effects using pygame.mixer. It separates music (looping background
tracks) from sound effects (one-shot audio) and provides independent volume
and enable/disable controls for each.
"""

import pygame
from pathlib import Path
from debugtools import debug, log_exception


class SoundManager:
    """
    Manages background music and sound effects.
    
    Uses pygame.mixer to play music separately from sound effects, with
    independent controls for each. Gracefully handles missing audio hardware
    by disabling sound features when initialization fails.
    """

    def __init__(self, sound_dir: str = "assets/sounds"):
        """
        Initialize the sound manager.
        
        Args:
            sound_dir: Directory containing sounds/music subdirectories
        """
        self.sound_dir = Path(sound_dir)

        self.music_enabled = True
        self.sfx_enabled = True

        self.sounds = {}
        self.music_playing = None
        self.sfx_channel = None

        try:
            pygame.mixer.init()
            debug("Sound system initialized.")
        except Exception as e:
            log_exception(f"Failed to initialize sound: {e}")
            self.music_enabled = False
            self.sfx_enabled = False
            return
        
        try:
            self.sfx_channel = pygame.mixer.Channel(1)
        except Exception as e:
            log_exception(f"Failed to create SFX channel: {e}")
            self.sfx_enabled = False

    def play_music(self, filename: str, loop: bool = True, volume: float = 0.6):
        """
        Play background music.
        
        Args:
            filename: Name of music file in sound_dir/music/
            loop: Whether to loop the music (default: True)
            volume: Music volume from 0.0 to 1.0 (default: 0.6)
        """
        if not self.music_enabled:
            return
        try:
            path = self.sound_dir / "music" / filename
            if not path.exists():
                debug(f"Missing music file: {path}")
                return
            if self.music_playing == filename:
                return
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0)
            self.music_playing = filename
            debug(f"Now playing music: {filename}")
        except Exception as e:
            log_exception(f"Music playback error: {e}")

    def stop_music(self):
        """Stop currently playing background music."""
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.music_playing = None
        debug("Music stopped.")

    def set_music_enabled(self, enabled: bool):
        """
        Enable or disable background music.
        
        Args:
            enabled: True to enable music, False to disable
        """
        previously_playing = self.music_playing
        self.music_enabled = enabled
        if not enabled:
            pygame.mixer.music.stop()
        else:
            if previously_playing:
                self.play_music(previously_playing)
        debug(f"Music {'enabled' if enabled else 'disabled'}.")

    def load_sfx(self, name: str, filename: str, volume: float = 1.0):
        """
        Preload a sound effect.
        
        Args:
            name: Identifier for the sound effect
            filename: Name of sound file in sound_dir/sfx/
            volume: Sound effect volume from 0.0 to 1.0 (default: 1.0)
        """
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
        """
        Play a preloaded sound effect.
        
        Args:
            name: Identifier of the sound effect to play
        """
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
        """
        Enable or disable sound effects.
        
        Args:
            enabled: True to enable SFX, False to disable
        """
        self.sfx_enabled = enabled
        debug(f"SFX {'enabled' if enabled else 'disabled'}.")
