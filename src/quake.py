import math
from .entity import Entity
from .sounds import Sound

class Quake(Entity):
    
    # Static options
    OPTION_QuakeDuration = 5.0
    OPTION_QuakeDropRate = 0.2
    OPTION_TimeTillFirstQuake = 90.0
    OPTION_TimeBetweenQuakes = 30.0
    OPTION_ShakeAmplitude = 0.05
    OPTION_ShakeFrequency = 50.0

    def __init__(self, game):
        super().__init__(game)
        self._earthquake = False
        self._earthquake_countdown = Quake.OPTION_TimeTillFirstQuake
        self._x = 0.0
        self._rumble = None

    def __del__(self):
        # Stop sound if any
        self._rumble = None
        # Recenter
        if self._earthquake and self._game.get_interface():
            self._game.get_interface().offset_viewport(0.0, 0.0)

    @staticmethod
    def read_settings(settings):
        Quake.OPTION_QuakeDuration = settings.get_float("Quake", "QuakeDuration", 5.0)
        Quake.OPTION_QuakeDropRate = settings.get_float("Quake", "QuakeDropRate", 0.2)
        Quake.OPTION_TimeTillFirstQuake = settings.get_float("Quake", "TimeTillFirstQuake", 90.0)
        Quake.OPTION_TimeBetweenQuakes = settings.get_float("Quake", "TimeBetweenQuakes", 30.0)
        Quake.OPTION_ShakeAmplitude = settings.get_float("Quake", "ShakeAmplitude", 0.05)
        Quake.OPTION_ShakeFrequency = settings.get_float("Quake", "ShakeFrequency", 50.0)

    def draw(self):
        # Earthquake is invisible
        pass

    def update(self, time):
        self._earthquake_countdown -= time

        if self._earthquake:
            # Drop terrain
            if self._game.get_landscape():
                self._game.get_landscape().drop_terrain(time * Quake.OPTION_QuakeDropRate)

            # Shake screen
            self._x = math.sin((Quake.OPTION_QuakeDuration - self._earthquake_countdown) * Quake.OPTION_ShakeFrequency) * Quake.OPTION_ShakeAmplitude
            
            if self._game.get_interface():
                self._game.get_interface().offset_viewport(self._x, 0.0)

            if self._earthquake_countdown < 0.0:
                self._earthquake = False
                self._earthquake_countdown = Quake.OPTION_TimeBetweenQuakes
                
                if self._game.get_interface():
                    self._game.get_interface().offset_viewport(0.0, 0.0)
                self._rumble = None # Stop sound
        
        elif self._earthquake_countdown < 0.0:
            self._earthquake = True
            self._earthquake_countdown = Quake.OPTION_QuakeDuration
            
            # Start sound
            if self._game.get_sound():
                 # 2 is hardcoded sound ID for rumble in C++ original? (quake.cc line 201)
                 # "_rumble = new cSound::cSoundSource (_game->getSound (), 2, true);"
                 self._rumble = self._game.get_sound().SoundSource(self._game.get_sound(), 2, True)

        return True
