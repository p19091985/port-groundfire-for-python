import os
import sys
import types


def install_fake_pygame():
    existing = sys.modules.get("pygame")
    if existing is not None:
        return existing

    pygame = types.ModuleType("pygame")

    class PygameError(Exception):
        pass

    class FakeKeyState:
        def __len__(self):
            return 2048

        def __getitem__(self, key):
            return False

    class FakeRect:
        def __init__(self, x, y, w, h):
            self.x = x
            self.y = y
            self.w = w
            self.h = h

    class FakeSurface:
        def __init__(self, size=(640, 480), flags=0):
            self._size = tuple(size)
            self._flags = flags
            self._alpha = 255

        def fill(self, *_args, **_kwargs):
            return None

        def blit(self, *_args, **_kwargs):
            return None

        def subsurface(self, rect):
            width = getattr(rect, "w", 1)
            height = getattr(rect, "h", 1)
            return FakeSurface((width, height))

        def convert_alpha(self):
            return self

        def get_size(self):
            return self._size

        def get_width(self):
            return self._size[0]

        def get_height(self):
            return self._size[1]

        def copy(self):
            return FakeSurface(self._size, self._flags)

        def set_alpha(self, alpha):
            self._alpha = alpha

        def get_rect(self, **kwargs):
            rect = {"x": 0, "y": 0, "width": self._size[0], "height": self._size[1]}
            rect.update(kwargs)
            return types.SimpleNamespace(**rect)

    class FakeChannel:
        def __init__(self):
            self._busy = True

        def stop(self):
            self._busy = False

        def get_busy(self):
            return self._busy

    class FakeSound:
        def __init__(self, _file_name):
            self._channel = FakeChannel()

        def play(self, loops=0):
            self._channel = FakeChannel()
            if loops == 0:
                self._channel._busy = False
            return self._channel

    class FakeJoystick:
        def __init__(self, _index):
            pass

        def init(self):
            return None

        def get_numbuttons(self):
            return 0

        def get_numaxes(self):
            return 0

        def get_button(self, _button):
            return False

        def get_axis(self, _axis):
            return 0.0

    mixer_state = {"init": False}

    def mixer_init():
        mixer_state["init"] = True

    def mixer_quit():
        mixer_state["init"] = False

    pygame.error = PygameError
    pygame.RESIZABLE = 1
    pygame.FULLSCREEN = 2
    pygame.SRCALPHA = 4
    pygame.BLEND_MULT = 5
    pygame.BLEND_RGBA_MULT = 6
    pygame.QUIT = 256
    pygame.K_ESCAPE = 27
    pygame.K_SPACE = 32
    pygame.K_RETURN = 13
    pygame.Rect = FakeRect
    pygame.Surface = FakeSurface
    pygame.init = lambda: None
    pygame.quit = lambda: None
    pygame.display = types.SimpleNamespace(
        set_mode=lambda size, _flags=0: FakeSurface(size),
        set_caption=lambda _title: None,
        flip=lambda: None,
    )
    pygame.event = types.SimpleNamespace(
        get=lambda *_args, **_kwargs: [],
        pump=lambda: None,
    )
    pygame.mouse = types.SimpleNamespace(
        get_pos=lambda: (0, 0),
        get_pressed=lambda: (False, False, False),
        set_visible=lambda _visible: None,
    )
    pygame.key = types.SimpleNamespace(get_pressed=lambda: FakeKeyState())
    pygame.joystick = types.SimpleNamespace(
        init=lambda: None,
        get_count=lambda: 0,
        Joystick=FakeJoystick,
    )
    pygame.mixer = types.SimpleNamespace(
        init=mixer_init,
        quit=mixer_quit,
        get_init=lambda: mixer_state["init"],
        set_num_channels=lambda _count: None,
        Sound=FakeSound,
    )
    pygame.image = types.SimpleNamespace(load=lambda _file_name: FakeSurface((64, 64)))
    pygame.transform = types.SimpleNamespace(
        scale=lambda _surface, size: FakeSurface(size),
        rotate=lambda surface, _angle: surface,
    )
    pygame.draw = types.SimpleNamespace(
        polygon=lambda *_args, **_kwargs: None,
        rect=lambda *_args, **_kwargs: None,
        line=lambda *_args, **_kwargs: None,
    )

    def module_getattr(name):
        if name.startswith("K_"):
            return 0
        raise AttributeError(name)

    pygame.__getattr__ = module_getattr

    sys.modules["pygame"] = pygame
    return pygame


install_fake_pygame()


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FlatLandscape:
    def __init__(self, ground_y=0.0, width=11.0):
        self.ground_y = ground_y
        self.width = width
        self.update_calls = []
        self.holes = []
        self.drop_calls = []
        self.collisions = []

    def move_to_ground(self, _x, _y):
        return self.ground_y

    def ground_collision(self, _x1, _y1, _x2, _y2):
        if self.collisions:
            return self.collisions.pop(0)
        return (False, 0.0, 0.0)

    def update(self, dt):
        self.update_calls.append(dt)

    def draw(self):
        return None

    def make_hole(self, x, y, size):
        self.holes.append((x, y, size))

    def get_landscape_width(self):
        return self.width

    def drop_terrain(self, amount):
        self.drop_calls.append(amount)


class DummySoundManager:
    class SoundSource:
        def __init__(self, _sound_manager, _sound_id, looping):
            self._playing = looping

        def stop(self):
            self._playing = False

        def is_source_playing(self):
            return self._playing

    def __init__(self):
        self.loaded = []

    def load_sound(self, sound_id, file_name):
        self.loaded.append((sound_id, file_name))


class DummyGameForTank:
    def __init__(self, settings, landscape=None):
        from src.common import GameState

        self.GameState = GameState
        self._settings = settings
        self._landscape = landscape or FlatLandscape()
        self._entities = []
        self._sound = DummySoundManager()
        self._recorded_tank_deaths = 0
        self._game_state = GameState.ROUND_IN_ACTION
        self._time = 0.0

    def get_settings(self):
        return self._settings

    def get_landscape(self):
        return self._landscape

    def get_interface(self):
        return None

    def get_sound(self):
        return self._sound

    def add_entity(self, entity):
        self._entities.append(entity)

    def record_tank_death(self):
        self._recorded_tank_deaths += 1

    def get_game_state(self):
        return self._game_state

    def set_game_state(self, state):
        self._game_state = state

    def get_time(self):
        return self._time

    def set_time(self, value):
        self._time = value


class CommandPlayer:
    def __init__(self):
        self.commands = {}
        self.recorded_shots = []
        self.recorded_fired = 0
        self.defeated = []
        self.update_calls = 0
        self._number = 0
        self._colour = (255, 255, 255)

    def get_command(self, command, start_time_ref=None):
        if isinstance(start_time_ref, list) and start_time_ref:
            start_time_ref[0] = 0.0
        return self.commands.get(command, False)

    def update(self, time=0.0):
        self.update_calls += 1

    def record_shot(self, x, y, hit_tank):
        self.recorded_shots.append((x, y, hit_tank))

    def record_fired(self):
        self.recorded_fired += 1

    def defeat(self, player):
        self.defeated.append(player)

    def get_player(self):
        return self


class RecordingWeapon:
    def __init__(self, fire_results=None):
        self.fire_results = list(fire_results or [True])
        self.fire_calls = []
        self.select_calls = 0
        self.unselect_calls = 0
        self.update_calls = []
        self.ammo_round_calls = 0

    def fire(self, firing, time):
        self.fire_calls.append((firing, time))
        if not self.fire_results:
            return True
        if len(self.fire_results) == 1:
            return self.fire_results[0]
        return self.fire_results.pop(0)

    def update(self, time):
        self.update_calls.append(time)

    def select(self):
        self.select_calls += 1
        return True

    def unselect(self):
        self.unselect_calls += 1

    def set_ammo_for_round(self):
        self.ammo_round_calls += 1

    def ready_to_fire(self):
        return True

    def draw_graphic(self, _x):
        return None


class ExplosionTank:
    def __init__(self, x, y, hit_range=0.1875, dies_on_damage=False):
        self.x = x
        self.y = y
        self.hit_range = hit_range
        self.damage_calls = []
        self.dies_on_damage = dies_on_damage

    def get_centre(self):
        return (self.x, self.y, self.hit_range)

    def do_damage(self, damage):
        self.damage_calls.append(damage)
        return self.dies_on_damage


class ExplosionPlayer:
    def __init__(self, tank):
        self._tank = tank

    def get_tank(self):
        return self._tank


class FlowTank:
    def __init__(self, name):
        self.name = name
        self.pre_round_calls = 0
        self.post_round_calls = 0
        self.position_calls = []
        self._alive = True
        self._colour = (255, 255, 255)

    def do_pre_round(self):
        self.pre_round_calls += 1
        self._alive = True
        return True

    def do_post_round(self):
        self.post_round_calls += 1
        return True

    def set_position_on_ground(self, x):
        self.position_calls.append(x)

    def draw(self):
        return None

    def alive(self):
        return self._alive

    def get_colour(self):
        return self._colour


class FlowPlayer:
    def __init__(self, name, score=0, human=False):
        self._name = name
        self._score = score
        self._leader = False
        self._human = human
        self._defeated_players = []
        self._tank = FlowTank(name)
        self.new_round_calls = 0
        self.end_round_calls = 0

    def get_tank(self):
        return self._tank

    def new_round(self):
        self.new_round_calls += 1
        self._defeated_players = []

    def end_round(self):
        self.end_round_calls += 1

    def get_score(self):
        return self._score

    def set_leader(self, leader):
        self._leader = leader

    def is_leader(self):
        return self._leader

    def get_name(self):
        return self._name

    def is_computer(self):
        return not self._human

    def get_command(self, _command, start_time_ref=None):
        if isinstance(start_time_ref, list) and start_time_ref:
            start_time_ref[0] = 0.0
        return False

    def get_defeated_players(self):
        return list(self._defeated_players)
