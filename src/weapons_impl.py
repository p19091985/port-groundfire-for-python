from .weapon import Weapon
from .shell import Shell
from .missile import Missile
from .mirv import Mirv
from .machinegunround import MachineGunRound
from .soundentity import SoundEntity
from .inifile import ReadIniFile
from .renderprimitives import RectPrimitive

# -----------------------------------------------------------------------------
# ShellWeapon
# -----------------------------------------------------------------------------
class ShellWeapon(Weapon):
    OPTION_BlastSize = 0.3
    OPTION_CooldownTime = 5.0
    OPTION_Damage = 40.0

    def __init__(self, game, owner_tank):
        super().__init__(game, owner_tank)
        self._cooldown_time = ShellWeapon.OPTION_CooldownTime

    @staticmethod
    def read_settings(settings: ReadIniFile):
        ShellWeapon.OPTION_BlastSize = settings.get_float("Shell", "BlastSize", 0.3)
        ShellWeapon.OPTION_CooldownTime = settings.get_float("Shell", "CooldownTime", 5.0)
        ShellWeapon.OPTION_Damage = settings.get_float("Shell", "Damage", 40.0)

    def fire(self, firing, time):
        if firing and self._cooldown <= 0.0:
            self._cooldown = self._cooldown_time
            
            x_init, y_init = self._owner_tank.gun_launch_position()
            vx_init, vy_init = self._owner_tank.gun_launch_velocity()
            
            shell = Shell(self._game, self._owner_tank.get_player(),
                          x_init, y_init, vx_init, vy_init,
                          self._game.get_time(),
                          ShellWeapon.OPTION_BlastSize,
                          ShellWeapon.OPTION_Damage,
                          False)
            self._game.add_entity(shell)
            
            boom = SoundEntity(self._game, 0, False)
            self._game.add_entity(boom)
            
            self._owner_tank.get_player().record_fired()
        return True

    def update(self, time):
        if self._cooldown > 0.0:
            self._cooldown -= time

    def select(self):
        self._cooldown = self._cooldown_time
        return True

    def draw_graphic(self, x):
        self.draw_icon(x, 0)

    def get_graphic_primitives(self, x: float) -> tuple[object, ...]:
        primitive = self._build_icon_primitive(x, 0)
        return () if primitive is None else (primitive,)

# -----------------------------------------------------------------------------
# MissileWeapon
# -----------------------------------------------------------------------------
class MissileWeapon(Weapon):
    OPTION_BlastSize = 0.3
    OPTION_CooldownTime = 5.0
    OPTION_Damage = 40.0
    OPTION_Cost = 50

    def __init__(self, game, owner_tank):
        super().__init__(game, owner_tank)
        self._cooldown_time = MissileWeapon.OPTION_CooldownTime
        self._quantity = 0
        self._cost = MissileWeapon.OPTION_Cost
        self._available_quantity = 0

    @staticmethod
    def read_settings(settings: ReadIniFile):
        MissileWeapon.OPTION_BlastSize = settings.get_float("Missile", "BlastSize", 0.3)
        MissileWeapon.OPTION_CooldownTime = settings.get_float("Missile", "CooldownTime", 5.0)
        MissileWeapon.OPTION_Damage = settings.get_float("Missile", "Damage", 40.0)
        MissileWeapon.OPTION_Cost = settings.get_int("Price", "Missiles", 50)

    def fire(self, firing, time):
        if firing and self._cooldown <= 0.0:
            self._cooldown = self._cooldown_time
            
            x_init, y_init = self._owner_tank.gun_launch_position()
            angle = self._owner_tank.gun_launch_angle()
            
            missile = Missile(self._game, self._owner_tank.get_player(),
                              x_init, y_init, angle,
                              MissileWeapon.OPTION_BlastSize,
                              MissileWeapon.OPTION_Damage)
            self._game.add_entity(missile)
            
            launch = SoundEntity(self._game, 5, False)
            self._game.add_entity(launch)
            
            self._quantity -= 1
            self._available_quantity -= 1
            
        if self._available_quantity == 0:
            return False
        return True

    def update(self, time):
        if self._cooldown > 0.0:
            self._cooldown -= time

    def select(self):
        if self._available_quantity == 0:
            return False
        self._cooldown = self._cooldown_time
        return True
        
    def set_ammo_for_round(self):
        self._available_quantity = self._quantity

    def draw_graphic(self, x):
        self.draw_icon(x, 10)
        
        # Draw bars for ammo
        if not self._game.get_interface(): return
        
        # White rects
        # (x + i*0.2 + 0.40, 6.8) to (..., 6.9)
        # width 0.15 height 0.1
        
        interface = self._game.get_interface()
        
        for i in range(self._available_quantity):
             gx = x + i * 0.2 + 0.40
             self._game.get_graphics().draw_world_rect(gx, 6.9, gx + 0.15, 6.8, (255, 255, 255))

    def get_graphic_primitives(self, x: float) -> tuple[object, ...]:
        primitive = self._build_icon_primitive(x, 10)
        if primitive is None:
            return ()
        return (primitive,) + self._build_ammo_bar_primitives(x, self._available_quantity)

# -----------------------------------------------------------------------------
# MirvWeapon
# -----------------------------------------------------------------------------
class MirvWeapon(Weapon):
    OPTION_BlastSize = 0.3
    OPTION_CooldownTime = 6.0
    OPTION_Damage = 20.0
    OPTION_Cost = 50

    def __init__(self, game, owner_tank):
        super().__init__(game, owner_tank)
        self._quantity = 0
        self._cooldown_time = MirvWeapon.OPTION_CooldownTime
        self._cost = MirvWeapon.OPTION_Cost

    @staticmethod
    def read_settings(settings: ReadIniFile):
        MirvWeapon.OPTION_BlastSize = settings.get_float("Mirv", "BlastSize", 0.3)
        MirvWeapon.OPTION_CooldownTime = settings.get_float("Mirv", "CooldownTime", 6.0)
        MirvWeapon.OPTION_Damage = settings.get_float("Mirv", "Damage", 20.0)
        MirvWeapon.OPTION_Cost = settings.get_int("Price", "Mirvs", 50)

    def fire(self, firing, time):
        if firing and self._cooldown <= 0.0:
            self._cooldown = self._cooldown_time
            
            x, y = self._owner_tank.gun_launch_position()
            vx, vy = self._owner_tank.gun_launch_velocity()
            
            mirv = Mirv(self._game, self._owner_tank.get_player(),
                        x, y, vx, vy, self._game.get_time(),
                        MirvWeapon.OPTION_BlastSize, MirvWeapon.OPTION_Damage)
            self._game.add_entity(mirv)
            
            boom = SoundEntity(self._game, 0, False)
            self._game.add_entity(boom)
            
            self._quantity -= 1
            
        if self._quantity == 0:
            return False
        return True

    def update(self, time):
        if self._cooldown > 0.0:
            self._cooldown -= time

    def select(self):
        if self._quantity == 0:
            return False
        self._cooldown = self._cooldown_time
        return True

    def draw_graphic(self, x):
        self.draw_icon(x, 4)

    def get_graphic_primitives(self, x: float) -> tuple[object, ...]:
        primitive = self._build_icon_primitive(x, 4)
        return () if primitive is None else (primitive,)

# -----------------------------------------------------------------------------
# NukeWeapon
# -----------------------------------------------------------------------------
class NukeWeapon(Weapon):
    OPTION_BlastSize = 3.0
    OPTION_CooldownTime = 10.0
    OPTION_Damage = 90.0
    OPTION_Cost = 50

    def __init__(self, game, owner_tank):
        super().__init__(game, owner_tank)
        self._quantity = 0
        self._cooldown_time = NukeWeapon.OPTION_CooldownTime
        self._cost = NukeWeapon.OPTION_Cost

    @staticmethod
    def read_settings(settings: ReadIniFile):
        NukeWeapon.OPTION_BlastSize = settings.get_float("Nuke", "BlastSize", 3.0)
        NukeWeapon.OPTION_CooldownTime = settings.get_float("Nuke", "CooldownTime", 10.0)
        NukeWeapon.OPTION_Damage = settings.get_float("Nuke", "Damage", 90.0)
        NukeWeapon.OPTION_Cost = settings.get_int("Price", "Nukes", 50)

    def fire(self, firing, time):
        if firing and self._cooldown <= 0.0:
            self._cooldown = self._cooldown_time
            
            x, y = self._owner_tank.gun_launch_position()
            vx, vy = self._owner_tank.gun_launch_velocity()
            
            # Nukes are Shells with white_out=True
            nuke = Shell(self._game, self._owner_tank.get_player(),
                         x, y, vx, vy, self._game.get_time(),
                         NukeWeapon.OPTION_BlastSize,
                         NukeWeapon.OPTION_Damage,
                         True)
            self._game.add_entity(nuke)
            
            boom = SoundEntity(self._game, 0, False)
            self._game.add_entity(boom)
            
            self._quantity -= 1
            
        if self._quantity == 0:
            return False
        return True

    def update(self, time):
        if self._cooldown > 0.0:
            self._cooldown -= time

    def select(self):
        if self._quantity == 0:
            return False
        self._cooldown = self._cooldown_time
        return True

    def draw_graphic(self, x):
        self.draw_icon(x, 1)

    def get_graphic_primitives(self, x: float) -> tuple[object, ...]:
        primitive = self._build_icon_primitive(x, 1)
        return () if primitive is None else (primitive,)

# -----------------------------------------------------------------------------
# MachineGunWeapon
# -----------------------------------------------------------------------------
class MachineGunWeapon(Weapon):
    OPTION_CooldownTime = 0.1
    OPTION_Damage = 2.0
    OPTION_Speed = 25.0
    OPTION_Cost = 50

    def __init__(self, game, owner_tank):
        super().__init__(game, owner_tank)
        self._cooldown_time = MachineGunWeapon.OPTION_CooldownTime
        self._quantity = 0
        self._cost = MachineGunWeapon.OPTION_Cost
        self._available_quantity = 0
        self._gun_source = None

    @staticmethod
    def read_settings(settings: ReadIniFile):
        MachineGunWeapon.OPTION_CooldownTime = settings.get_float("MachineGun", "CooldownTime", 0.1)
        MachineGunWeapon.OPTION_Damage = settings.get_float("MachineGun", "Damage", 2.0)
        MachineGunWeapon.OPTION_Speed = settings.get_float("MachineGun", "Speed", 25.0)
        MachineGunWeapon.OPTION_Cost = settings.get_int("Price", "MachineGun", 50)

    def fire(self, firing, time):
        if firing:
            if self._gun_source is None and self._game.get_sound():
                self._gun_source = self._game.get_sound().SoundSource(self._game.get_sound(), 8, True)
        else:
            self._gun_source = None

        if self._available_quantity == 0:
            return False
        return True

    def update(self, time):
        if self._owner_tank.is_firing() and self._available_quantity != 0:
            self._cooldown -= time
            while self._cooldown < 0.0 and self._available_quantity != 0:
                x, y = self._owner_tank.gun_launch_position()
                vx, vy = self._owner_tank.gun_launch_velocity_at_power(MachineGunWeapon.OPTION_Speed)
                
                round = MachineGunRound(self._game, self._owner_tank.get_player(),
                                        x, y, vx, vy,
                                        self._game.get_time() + self._cooldown,
                                        MachineGunWeapon.OPTION_Damage)
                self._game.add_entity(round)
                
                self._quantity -= 1
                self._available_quantity -= 1
                self._cooldown += self._cooldown_time
                
            if self._available_quantity == 0:
                self._gun_source = None
        elif self._cooldown > 0.0:
            self._cooldown -= time
            if self._cooldown < 0.0: self._cooldown = 0.0

    def select(self):
        if self._available_quantity == 0:
            return False
        self._cooldown = self._cooldown_time
        return True
    
    def unselect(self):
        self._gun_source = None

    def set_ammo_for_round(self):
        self._available_quantity = self._quantity

    def draw_graphic(self, x):
        self.draw_icon(x, 2)
        
        # Draw bar
        if not self._game.get_interface(): return
        
        amt = self._available_quantity / 50.0 # Length
        
        x_start = x + 0.40
        y_top = 6.95
        y_bot = 6.75
        
        self._game.get_graphics().draw_world_rect(x_start, y_top, x_start + amt, y_bot, (255, 255, 255))

    def get_graphic_primitives(self, x: float) -> tuple[object, ...]:
        primitive = self._build_icon_primitive(x, 2)
        if primitive is None:
            return ()
        amt = self._available_quantity / 50.0
        return (
            primitive,
            RectPrimitive(x + 0.40, 6.95, x + 0.40 + amt, 6.75, (255, 255, 255)),
        )
