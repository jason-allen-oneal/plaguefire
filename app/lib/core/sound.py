import pygame
import random
from pathlib import Path
from app.lib.core.logger import debug, log_exception


class SoundManager:
    """Plays background music, overlapping SFX, and a dedicated ambient loop.

    Categories:
      - music (pygame.mixer.music)
      - sfx (ephemeral one-shot sounds)
      - ambient (single looping environmental track on reserved channel)

    Provides simple category volume and enable toggles. Curated raw source sounds may
    live under assets/sounds/source; we load them directly when requested so we don't
    have to copy large numbers of files into an sfx subfolder yet.
    """

    def __init__(self, assets, sound_dir="assets/sounds", max_channels=16):
        self.assets = assets
        self.sound_dir = Path(sound_dir)
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.ambient_sounds: dict[str, pygame.mixer.Sound] = {}
        # Performance: cache file existence checks to reduce I/O
        self._file_exists_cache: dict[str, bool] = {}

        # Enable flags
        self.music_enabled = True
        self.sfx_enabled = True
        self.ambient_enabled = True

        # Currently playing ids
        self.music_playing: str | None = None
        self.ambient_playing: str | None = None

        # Category volumes (0..1)
        self.music_volume = 0.6
        self.sfx_volume = 1.0
        self.ambient_volume = 0.4

        # Reserved ambient channel (first channel) initialized after mixer init
        self._ambient_channel: pygame.mixer.Channel | None = None
        # Ambient playback pools (for random event playback in town)
        self.ambient_pools: dict[str, list[pygame.mixer.Sound]] = {}
        self._ambient_mode: str | None = None
        self._next_ambient_ms: int = 0
        # Track which depth the ambient mode was chosen for (safety guard)
        self._ambient_depth: int | None = None
        self._ambient_is_day: bool | None = None
        # Minimum/maximum additional silence between ambient events (ms)
        self._ambient_min_gap_ms = 5000
        self._ambient_max_gap_ms = 30000

        try:
            pygame.mixer.init()
            pygame.mixer.set_num_channels(max_channels)
            self._ambient_channel = pygame.mixer.Channel(0)
            debug(f"Sound system initialized with {max_channels} channels (channel 0 reserved for ambient loop).")
        except Exception as e:
            log_exception(e)
            self.music_enabled = False
            self.sfx_enabled = False
            self.ambient_enabled = False
            return

    def play_music(self, filename: str, loop: bool = True, volume: float | None = None):
        if not self.music_enabled:
            return
        try:
            path = self.sound_dir / "music" / filename
            path_str = str(path)
            # Performance: check cache before disk I/O
            if path_str not in self._file_exists_cache:
                self._file_exists_cache[path_str] = path.exists()
            if not self._file_exists_cache[path_str]:
                debug(f"Missing music file: {path}")
                return
            if self.music_playing == filename:
                return
            pygame.mixer.music.load(path)
            vol = self.music_volume if volume is None else volume
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(-1 if loop else 0)
            self.music_playing = filename
            debug(f"Now playing music: {filename} @ {vol:.2f}")
        except Exception as e:
            log_exception(e)

    def stop_music(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.music_playing = None
        debug("Music stopped.")

    def set_music_enabled(self, enabled: bool):
        prev = self.music_playing
        self.music_enabled = enabled
        if not enabled:
            pygame.mixer.music.stop()
        elif prev:
            self.play_music(prev)
        debug(f"Music {'enabled' if enabled else 'disabled'}.")

    def set_music_volume(self, volume: float):
        self.music_volume = max(0.0, min(1.0, volume))
        if pygame.mixer.get_init() and self.music_playing:
            pygame.mixer.music.set_volume(self.music_volume)
        debug(f"Music volume set to {self.music_volume:.2f}")

    # --- SFX ------------------------------------------------------
    def load_sfx(self, name: str, filename: str, volume: float | None = None, raw_source: bool = False):
        """Load an SFX asset either via AssetManager (default) or directly from source folder.
               
        raw_source=True will look under assets/sounds/source/ for the filename.
        """
        try:
            if raw_source:
                path = self.sound_dir / "source" / filename
                path_str = str(path)
                # Performance: check cache before disk I/O
                if path_str not in self._file_exists_cache:
                    self._file_exists_cache[path_str] = path.exists()
                if not self._file_exists_cache[path_str]:
                    debug(f"Missing raw source SFX: {path}")
                    return
                sound = pygame.mixer.Sound(path)
            else:
                sound = self.assets.sound("sounds", "sfx", filename)
            vol = self.sfx_volume if volume is None else volume
            sound.set_volume(vol)
            self.sounds[name] = sound
            debug(f"Loaded SFX: {name} -> {filename} (raw={raw_source})")
        except Exception as e:
            log_exception(e)

    def play_sfx(self, name: str, volume: float | None = None):
        if not self.sfx_enabled:
            return
        try:
            sound = self.sounds.get(name)
            if not sound:
                debug(f"Missing SFX: {name}")
                return
            if volume is not None:
                sound.set_volume(max(0.0, min(1.0, volume)))
            else:
                sound.set_volume(self.sfx_volume)
            channel = pygame.mixer.find_channel(True)
            if channel and (self._ambient_channel is None or channel != self._ambient_channel):
                channel.play(sound)
                debug(f"Played SFX: {name}")
            else:
                debug(f"No free audio channels for SFX: {name}")
        except Exception as e:
            log_exception(e)

    def set_sfx_enabled(self, enabled: bool):
        self.sfx_enabled = enabled
        debug(f"SFX {'enabled' if enabled else 'disabled'}.")

    def set_sfx_volume(self, volume: float):
        self.sfx_volume = max(0.0, min(1.0, volume))
        debug(f"SFX volume set to {self.sfx_volume:.2f}")

    # --- Ambient --------------------------------------------------
    def load_ambient(self, name: str, filename: str, volume: float | None = None):
        if not pygame.mixer.get_init():
            return
        try:
            path = self.sound_dir / "source" / filename
            path_str = str(path)
            # Performance: check cache before disk I/O
            if path_str not in self._file_exists_cache:
                self._file_exists_cache[path_str] = path.exists()
            if not self._file_exists_cache[path_str]:
                debug(f"Missing ambient file: {path}")
                return
            snd = pygame.mixer.Sound(path)
            vol = self.ambient_volume if volume is None else volume
            snd.set_volume(vol)
            self.ambient_sounds[name] = snd
            debug(f"Loaded ambient '{name}' -> {filename}")
        except Exception as e:
            log_exception(e)

    def play_ambient(self, name: str, filename: str | None = None, loop: bool = True):
        if not self.ambient_enabled or not pygame.mixer.get_init():
            return
        if self._ambient_channel is None:
            return
        try:
            # Lazy load if necessary
            if name not in self.ambient_sounds:
                if not filename:
                    debug(f"Ambient '{name}' unknown and no filename provided")
                    return
                self.load_ambient(name, filename)
            snd = self.ambient_sounds.get(name)
            if not snd:
                return
            # Avoid restarting same ambient
            if self.ambient_playing == name and self._ambient_channel.get_busy():
                return
            loops = -1 if loop else 0
            self._ambient_channel.play(snd, loops=loops)
            self._ambient_channel.set_volume(self.ambient_volume)
            self.ambient_playing = name
            debug(f"Ambient playing: {name} (loops={loops})")
        except Exception as e:
            log_exception(e)

    def _load_ambient_pool(self, pool_name: str):
        """Load all files under assets/sounds/ambient/<pool_name>/ into a list."""
        if pool_name in self.ambient_pools:
            return
        pool_dir = self.sound_dir / "ambient" / pool_name
        sounds: list[pygame.mixer.Sound] = []
        try:
            if not pool_dir.exists() or not pool_dir.is_dir():
                debug(f"Ambient pool missing: {pool_dir}")
                self.ambient_pools[pool_name] = []
                return
            for p in sorted(pool_dir.iterdir()):
                if p.is_file():
                    try:
                        s = pygame.mixer.Sound(p)
                        s.set_volume(self.ambient_volume)
                        sounds.append(s)
                    except Exception:
                        # skip unreadable files
                        pass
        except Exception as e:
            log_exception(e)
        self.ambient_pools[pool_name] = sounds

    def update(self):
        """Should be called regularly (e.g., each frame). Handles random ambient playback.

        Town ambient pools (town_day / town_night) play single sounds at random
        intervals rather than looping forever.
        """
        if not self.ambient_enabled or not pygame.mixer.get_init():
            return
        now = pygame.time.get_ticks()
        mode = self._ambient_mode
        if not mode:
            return
        # Only handle pool-driven modes (town_day / town_night)
        if mode in ("town_day", "town_night"):
            # Safety: only play town pools when the chosen ambient depth is actually town (0).
            # This prevents stale town-night pools (crickets/etc) from playing after a depth
            # change if choose_ambient wasn't invoked for some reason.
            if self._ambient_depth is None or self._ambient_depth != 0:
                debug(f"Ambient mode {mode} ignored because ambient_depth={self._ambient_depth}")
                return
            # Ensure pool loaded
            if mode not in self.ambient_pools:
                self._load_ambient_pool(mode)
            pool = self.ambient_pools.get(mode) or []
            if not pool:
                return
            # If channel not available or busy, wait until it's free
            if self._ambient_channel is None or self._ambient_channel.get_busy():
                return
            if now >= self._next_ambient_ms:
                # pick a random sound and play once
                snd = random.choice(pool)
                try:
                    if self._ambient_channel:
                        self._ambient_channel.play(snd)
                        self._ambient_channel.set_volume(self.ambient_volume)
                        self.ambient_playing = mode
                    else:
                        # No ambient channel available; skip
                        return
                    # schedule next play after sound length + random gap
                    length_ms = int(snd.get_length() * 1000)
                    gap = random.randint(self._ambient_min_gap_ms, self._ambient_max_gap_ms)
                    self._next_ambient_ms = now + length_ms + gap
                    debug(f"Scheduled next ambient ({mode}) in {gap} ms")
                except Exception:
                    pass

    def stop_ambient(self):
        if self._ambient_channel and self._ambient_channel.get_busy():
            self._ambient_channel.stop()
        self.ambient_playing = None
        debug("Ambient stopped.")

    def set_ambient_enabled(self, enabled: bool):
        self.ambient_enabled = enabled
        if not enabled:
            self.stop_ambient()
        debug(f"Ambient {'enabled' if enabled else 'disabled'}.")

    def set_ambient_volume(self, volume: float):
        self.ambient_volume = max(0.0, min(1.0, volume))
        if self._ambient_channel and self._ambient_channel.get_busy():
            self._ambient_channel.set_volume(self.ambient_volume)
        debug(f"Ambient volume set to {self.ambient_volume:.2f}")

    # --- Curated convenience --------------------------------------
    def load_curated_defaults(self):
        """Load a curated subset of raw source sounds under semantic names.

        Safe to call multiple times; will skip already loaded keys.
        """
        curated = {
            # SFX
            ('melee_hit', 'clubman_attack4.WAV'),
            ('melee_miss', 'hoplite_attack3.WAV'),
            ('ranged_shot', 'archer_shot6.WAV'),
            ('door_bash', 'hit_wood_hard2.wav'),
            ('door_open', 'building_house1.wav'),
            ('door_close', 'building_house2.wav'),
            ('trap_trigger', 'stonethrower_attack2.WAV'),
            ('entity_die', 'soldier_die_06.WAV'),
        }
        for name, file in curated:
            if name not in self.sounds:
                self.load_sfx(name, file, raw_source=True)
        ambient = {
            ('town_day', 'Birds4.wav'),
            ('town_night', 'Wind5.wav'),
            ('dungeon_default', 'Wind7.wav'),
            ('dungeon_lava', 'fire_small1.WAV'),
        }
        for name, file in ambient:
            if name not in self.ambient_sounds:
                self.load_ambient(name, file)

    def choose_ambient(self, depth: int, is_day: bool):
        """Pick & play an ambient track based on depth and time-of-day."""
        if depth == 0:
            mode = 'town_day' if is_day else 'town_night'
            # Switch to pool-driven random ambient playback for town
            try:
                # Stop any looping ambient and switch mode
                if self._ambient_channel and self._ambient_channel.get_busy():
                    self._ambient_channel.stop()
                self._ambient_mode = mode
                # Record depth/time context for safety checks in update()
                self._ambient_depth = depth
                self._ambient_is_day = is_day
                # schedule first event in a short randomized window
                self._next_ambient_ms = pygame.time.get_ticks() + random.randint(500, 3000)
                debug(f"Ambient mode set to {mode}; first event in ~{self._next_ambient_ms - pygame.time.get_ticks()} ms")
            except Exception:
                pass
        else:
            # Non-town depths use the persistent dungeon ambient loop
            # Clear any pool-driven mode and mark ambient depth
            self._ambient_mode = None
            self._ambient_depth = depth
            self._ambient_is_day = is_day
            # Stop any pending pool events so town sounds don't bleed into dungeons
            try:
                if self._ambient_channel and self._ambient_channel.get_busy():
                    self._ambient_channel.stop()
            except Exception:
                pass
            track = 'dungeon_default'
            if track not in self.ambient_sounds:
                mapping = {
                    'dungeon_default': 'Wind7.wav'
                }
                filename = mapping.get(track)
                if filename:
                    self.play_ambient(track, filename, loop=True)
            else:
                self.play_ambient(track, loop=True)
