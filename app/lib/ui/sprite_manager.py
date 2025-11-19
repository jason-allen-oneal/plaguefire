"""
Sprite management system for handling animated sprites.
"""

import os
import json
import pygame
from typing import Optional, Tuple, Dict


class AnimatedSprite:
    """Represents an animated sprite with multiple frames."""
    
    def __init__(self, sprite_sheet: pygame.Surface, frame_width: int, frame_height: int, 
                 frames_per_row: int, animation_speed: float = 0.15):
        """
        Initialize an animated sprite.
        
        Args:
            sprite_sheet: The sprite sheet image
            frame_width: Width of each frame
            frame_height: Height of each frame
            frames_per_row: Number of frames in each row
            animation_speed: Time in seconds per frame
        """
        self.sprite_sheet = sprite_sheet
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frames_per_row = frames_per_row
        self.animation_speed = animation_speed
        
        # Animation state
        self.current_frame = 0
        self.animation_timer = 0
        self.current_row = 0  # Which animation row (down, up, left, right)
        self.is_animating = False
        
        # Calculate total frames
        self.total_rows = sprite_sheet.get_height() // frame_height
        
        # Optional atlas metadata (set externally for atlas-based sprites)
        self._atlas_entry: Optional[Dict] = None
        self._sprite_path: Optional[str] = None
        
        # Performance: pre-extract and cache all frames
        self._frame_cache: Dict[Tuple[int, int, Optional[Tuple[int, int]]], pygame.Surface] = {}
        
    def set_direction(self, direction: str):
        """
        Set the animation direction/row.
        
        Args:
            direction: 'down', 'up', 'left', or 'right'
        """
        direction_map = {
            'down': 0,
            'left': 1,
            'right': 2,
            'up': 3,
        }
        self.current_row = direction_map.get(direction, 0)
    
    def update(self, dt: float, is_moving: bool = False):
        """
        Update animation state.
        
        Args:
            dt: Delta time in seconds
            is_moving: Whether the sprite should be animating
        """
        self.is_animating = is_moving
        
        if self.is_animating:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % self.frames_per_row
        else:
            # When not moving, show idle frame (first frame)
            self.current_frame = 0
            self.animation_timer = 0
    
    def get_current_frame(self, scale_to: Optional[Tuple[int, int]] = None) -> pygame.Surface:
        """
        Get the current animation frame.
        
        Args:
            scale_to: Optional tuple (width, height) to scale the frame to
            
        Returns:
            Surface containing the current frame
        """
        # Performance: check cache first
        cache_key = (self.current_row, self.current_frame, scale_to)
        if cache_key in self._frame_cache:
            return self._frame_cache[cache_key]
        
        # Check if this is an atlas-based sprite
        if hasattr(self, '_atlas_entry') and self._atlas_entry:
            try:
                atlas_entry = self._atlas_entry
                direction_map = {0: 'down', 1: 'left', 2: 'right', 3: 'up'}
                direction = direction_map.get(self.current_row, 'down')
                
                # Get frame coordinates from atlas
                frame_key = f'frame_{self.current_frame}'
                coords = None
                
                # Try directional first
                if direction in atlas_entry and isinstance(atlas_entry[direction], dict):
                    coords = atlas_entry[direction].get(frame_key)
                    # If current frame doesn't exist, cycle back to frame 0
                    if not coords:
                        frame_key = 'frame_0'
                        coords = atlas_entry[direction].get(frame_key)
                        self.current_frame = 0
                # Fall back to simple format
                elif frame_key in atlas_entry:
                    coords = atlas_entry[frame_key]
                elif 'frame_0' in atlas_entry:
                    coords = atlas_entry['frame_0']
                    self.current_frame = 0
                
                if coords and len(coords) == 4:
                    x, y, w, h = coords
                    frame = pygame.Surface((w, h), pygame.SRCALPHA)
                    frame.blit(self.sprite_sheet, (0, 0), (x, y, w, h))
                    
                    if scale_to:
                        frame = pygame.transform.scale(frame, scale_to)
                    
                    # Cache the extracted frame
                    self._frame_cache[cache_key] = frame
                    return frame
            except Exception as e:
                print(f"Atlas frame extraction failed: {e}")
        
        # Standard grid-based frame extraction
        frame_x = self.current_frame * self.frame_width
        frame_y = self.current_row * self.frame_height
        
        # Extract frame
        frame = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        frame.blit(self.sprite_sheet, (0, 0), 
                  (frame_x, frame_y, self.frame_width, self.frame_height))
        
        # Scale if requested
        if scale_to:
            frame = pygame.transform.scale(frame, scale_to)
        
        # Cache the extracted frame
        self._frame_cache[cache_key] = frame
        return frame


class SpriteManager:
    """Manages sprite loading and caching."""
    
    def __init__(self, assets):
        """
        Initialize the sprite manager.
        
        Args:
            assets: AssetManager instance for loading images
        """
        self.assets = assets
        self.sprite_cache = {}
        self.animated_sprites = {}
        self.atlas_metadata = self._load_atlas_metadata()
        # Performance optimization: cache scaled and dimmed variants
        self.scaled_sprite_cache = {}  # (path, scale_to) -> Surface
        self.dimmed_sprite_cache = {}  # (path, scale_to) -> dimmed Surface
    
    def _load_atlas_metadata(self) -> Dict:
        """Load sprite atlas metadata from data/sprite_atlas.json"""
        try:
            atlas_path = os.path.join(os.getcwd(), 'data', 'sprite_atlas.json')
            if os.path.exists(atlas_path):
                with open(atlas_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Failed to load sprite atlas metadata: {e}")
        return {}
    
    def load_sprite(self, path: str, scale_to: Optional[Tuple[int, int]] = None, direction: str = 'down', frame_index: int = 0) -> Optional[pygame.Surface]:
        """
        Load a static sprite.
        
        Args:
            path: Path to the sprite (e.g., "images/monsters/angel.png")
            scale_to: Optional tuple (width, height) to scale to
            direction: Direction for directional sprites ('down', 'left', 'right', 'up')
            frame_index: Frame index for multi-frame sprites
            
        Returns:
            The loaded sprite surface or None if loading fails
        """
        # Performance: check scaled cache first if scaling requested
        if scale_to:
            scaled_key = (path, scale_to, direction, frame_index)
            if scaled_key in self.scaled_sprite_cache:
                return self.scaled_sprite_cache[scaled_key]
        
        cache_key = (path, scale_to, direction, frame_index)
        
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        
        try:
            # Check if this path has atlas metadata (non-grid spritesheet)
            atlas_entry = self.atlas_metadata.get(path)
            if atlas_entry and isinstance(atlas_entry, dict):
                # Check for directional format first
                if direction in atlas_entry and isinstance(atlas_entry[direction], dict):
                    frame_key = f'frame_{frame_index}'
                    frame_coords = atlas_entry[direction].get(frame_key)
                    if frame_coords and len(frame_coords) == 4:
                        return self._load_atlas_frame(path, frame_coords, scale_to, cache_key)
                # Fall back to simple frame format
                frame_key = f'frame_{frame_index}'
                frame_coords = atlas_entry.get(frame_key)
                if frame_coords and len(frame_coords) == 4:
                    return self._load_atlas_frame(path, frame_coords, scale_to, cache_key)
            
            # Normal sprite loading (single image or grid sheet)
            path_parts = path.split('/')
            # TileMapper returns paths relative to assets/images/, so if the
            # first segment isn't 'images' but an images folder exists under
            # the asset root, prefix with 'images'. This keeps callers that
            # already provide 'images/..' working.
            # If the caller provided a path that is already rooted under
            # 'images', 'sprites', or 'assets', leave it alone. Otherwise,
            # TileMapper returns paths relative to assets/images/, so when
            # an images/ folder exists, prefix with 'images'. This avoids
            # breaking paths that reference the top-level 'sprites/' folder.
            if path_parts and path_parts[0] not in ('images', 'sprites', 'assets'):
                images_root = os.path.join(self.assets.root or '', 'images')
                if os.path.isdir(images_root):
                    path_parts = ['images'] + path_parts

            # For better diagnostics, compute the resolved filesystem path
            # before attempting to load.
            try:
                resolved = self.assets._resolve(*path_parts)
            except Exception:
                resolved = None

            sprite = self.assets.image(*path_parts)
            
            # Performance: convert to optimal pixel format immediately
            if sprite.get_flags() & pygame.SRCALPHA:
                sprite = sprite.convert_alpha()
            else:
                sprite = sprite.convert()

            if scale_to:
                sprite = pygame.transform.scale(sprite, scale_to)
                # Cache the scaled version separately for faster lookups
                scaled_key = (path, scale_to, direction, frame_index)
                self.scaled_sprite_cache[scaled_key] = sprite

            self.sprite_cache[cache_key] = sprite
            return sprite
        except Exception as e:
            # Include the resolved path in the error message when available.
            resolved_path = locals().get('resolved')
            if resolved_path:
                print(f"Failed to load sprite {path} -> {resolved_path}: {e}")
            else:
                print(f"Failed to load sprite {path}: {e}")
            return None
    
    def _load_atlas_frame(self, sheet_path: str, coords: list, scale_to: Optional[Tuple[int, int]], cache_key) -> Optional[pygame.Surface]:
        """Load a single frame from a sprite atlas using coordinates [x, y, w, h]"""
        try:
            path_parts = sheet_path.split('/')
            if path_parts and path_parts[0] not in ('images', 'sprites', 'assets'):
                images_root = os.path.join(self.assets.root or '', 'images')
                if os.path.isdir(images_root):
                    path_parts = ['images'] + path_parts
            
            # Load full sheet
            full_sheet = self.assets.image(*path_parts)
            
            # Extract frame
            x, y, w, h = coords
            frame = pygame.Surface((w, h), pygame.SRCALPHA)
            frame.blit(full_sheet, (0, 0), (x, y, w, h))
            
            if scale_to:
                frame = pygame.transform.scale(frame, scale_to)
            
            self.sprite_cache[cache_key] = frame
            return frame
        except Exception as e:
            print(f"Failed to load atlas frame from {sheet_path} at {coords}: {e}")
            return None
    
    def get_dimmed_sprite(self, path: str, scale_to: Optional[Tuple[int, int]] = None, direction: str = 'down', frame_index: int = 0) -> Optional[pygame.Surface]:
        """
        Get a pre-dimmed version of a sprite (for explored but not visible tiles).
        
        Args:
            path: Path to the sprite
            scale_to: Optional tuple (width, height) to scale to
            direction: Direction for directional sprites
            frame_index: Frame index for multi-frame sprites
            
        Returns:
            Dimmed sprite surface or None if loading fails
        """
        cache_key = (path, scale_to, direction, frame_index, 'dimmed')
        
        if cache_key in self.dimmed_sprite_cache:
            return self.dimmed_sprite_cache[cache_key]
        
        # Load the original sprite
        sprite = self.load_sprite(path, scale_to, direction, frame_index)
        if not sprite:
            return None
        
        # Create dimmed version
        dimmed = sprite.copy()
        dimmed.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
        
        # Cache it
        self.dimmed_sprite_cache[cache_key] = dimmed
        return dimmed
    
    def load_animated_sprite(self, sprite_id: str, path: str, frame_width: int, 
                            frame_height: int, frames_per_row: int = 4,
                            animation_speed: float = 0.15) -> Optional[AnimatedSprite]:
        """
        Load an animated sprite sheet.
        
        Args:
            sprite_id: Unique identifier for this sprite
            path: Path to the sprite sheet
            frame_width: Width of each frame
            frame_height: Height of each frame
            frames_per_row: Number of frames per animation row
            animation_speed: Time in seconds per frame
            
        Returns:
            AnimatedSprite instance or None if loading fails
        """
        if sprite_id in self.animated_sprites:
            return self.animated_sprites[sprite_id]
        
        try:
            path_parts = path.split('/')
            if path_parts and path_parts[0] not in ('images', 'sprites', 'assets'):
                images_root = os.path.join(self.assets.root or '', 'images')
                if os.path.isdir(images_root):
                    path_parts = ['images'] + path_parts

            try:
                resolved = self.assets._resolve(*path_parts)
            except Exception:
                resolved = None

            sprite_sheet = self.assets.image(*path_parts)

            animated_sprite = AnimatedSprite(
                sprite_sheet, frame_width, frame_height, 
                frames_per_row, animation_speed
            )

            self.animated_sprites[sprite_id] = animated_sprite
            return animated_sprite
        except Exception as e:
            resolved_path = locals().get('resolved')
            if resolved_path:
                print(f"Failed to load animated sprite {path} -> {resolved_path}: {e}")
            else:
                print(f"Failed to load animated sprite {path}: {e}")
            return None
    
    def get_animated_sprite(self, sprite_id: str) -> Optional[AnimatedSprite]:
        """Get a previously loaded animated sprite."""
        return self.animated_sprites.get(sprite_id)
