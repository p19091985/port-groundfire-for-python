import pygame
from .report import report, debug

class SoundError(Exception):
    pass

class Sound:
    def __init__(self, num_of_sounds):
        try:
            pygame.mixer.init()
            # Reserve enough channels
            pygame.mixer.set_num_channels(32)
        except pygame.error as e:
            report(f"ERROR: Could not initialise sound: {e}")
            raise SoundError()

        self._num_of_sounds = num_of_sounds
        self._buffers = [None] * num_of_sounds
        self._active_sources = []

    def __del__(self):
        pygame.mixer.quit()

    def load_sound(self, buffer_num, file_name):
        if not pygame.mixer.get_init():
            return

        try:
            sound = pygame.mixer.Sound(file_name)
            self._buffers[buffer_num] = sound
        except Exception:
             debug(f"WARNING: Could not load sound file : '{file_name}'")

    def play_sound(self, sound_id, looping=False):
        """Plays a loaded sound by ID."""
        # Check logic: C++ creates a SoundSource to play.
        # We don't necessarily need to keep the reference unless we want control.
        # Fire and forget for now is fine for "play_sound".
        # SoundSource __init__ plays it.
        try:
             # Just instantiate. The __init__ plays it.
             # We rely on Python GC to not kill it immediately? 
             # Actually pygame mixer channel plays in background. GC of object might stop it?
             # C++ SoundSource destructor stops sound. So YES, we need to keep it alive.
             # But "play_sound" usually implies fire-and-forget.
             # If we return it, caller must keep it.
             # If we don't return it, it dies immediately -> stop() -> silence.
             
             # Wait, in C++, who holds SoundSource?
             # Game::Explosion: Sound::PlaySound(id) (static or what?)
             # Let's check user's request context if possible, but standard is:
             # If C++ SoundSource stops on destruct, we need to keep a reference list of active sounds.
             
             s = self.SoundSource(self, sound_id, looping)
             # Basic management: add to list? 
             # For now, let's assume we need to return it or store it.
             # But Game doesn't store the result of play_sound.
             # So we must store it in Sound manager until it finishes.
             self._active_sources.append(s)
             
             # Cleanup dead sources
             self._active_sources = [src for src in self._active_sources if src.is_source_playing()]
             
             return s
        except Exception:
             pass

    class SoundSource:
        def __init__(self, sound_manager, sound_to_play, looping):
            self._channel = None
            if sound_manager._buffers[sound_to_play]:
                self._sound = sound_manager._buffers[sound_to_play]
                # Play immediately, return channel
                loops = -1 if looping else 0
                self._channel = self._sound.play(loops=loops)
        
        def __del__(self):
            if self._channel:
                 try:
                     self._channel.stop()
                 except:
                     pass

        def is_source_playing(self):
            if self._channel:
                return self._channel.get_busy()
            return False
