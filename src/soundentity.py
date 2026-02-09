from .entity import Entity

class SoundEntity(Entity):
    def __init__(self, game, sound_to_play, looping):
        super().__init__(game)
        self._looping = looping
        self._die = False
        
        # Init sound
        # cSound::cSoundSource _sound (game->getSound(), soundToPlay, looping)
        if self._game.get_sound():
             self._sound = self._game.get_sound().SoundSource(self._game.get_sound(), sound_to_play, looping)
        else:
             self._sound = None

    def draw(self):
        pass

    def update(self, time):
        if self._die:
            return False

        if not self._looping:
            if self._sound and not self._sound.is_source_playing():
                return False
        
        return True

    def stop(self):
        # Not implemented in original but header had it?
        # Orig uses _die flag or just delete logic
        self._die = True
