#
# Copyright (c) 2004, Tom Russell (tom@groundfire.net)
#
# This file is part of the Groundfire project, distributed under the MIT 
# license. See the file 'COPYING', included with this distribution, for a copy
# of the full MIT licence.
#

# This makefile is only tested with the gnu c++ compiler (mingw on Windows)
# To build this with any other compiler you will probably have to alter this
# Makefile (or write your own makefile.)

CC           = g++
LOCALINCLUDE = -I./includes
CFLAGS       = -Wall $(FLAGS)

SOURCES = 	interface.cc 		\
		main.cc 			\
		game.cc			\
		landscape.cc		\
		entity.cc			\
		tank.cc			\
		shell.cc			\
		blast.cc			\
		trail.cc			\
		font.cc			\
		smoke.cc			\
		menu.cc			\
		mainmenu.cc			\
		quitmenu.cc			\
		optionmenu.cc		\
		weapon.cc			\
		shellweapon.cc 		\
		nukeweapon.cc		\
		missileweapon.cc		\
		missile.cc			\
		playermenu.cc		\
		scoremenu.cc		\
		shopmenu.cc			\
		buttons.cc			\
		selector.cc			\
		controllermenu.cc		\
		setcontrolsmenu.cc	\
		controlsfile.cc		\
		controls.cc			\
		sounds.cc			\
		soundentity.cc		\
		quake.cc			\
		inifile.cc			\
		winnermenu.cc		\
		player.cc			\
		humanplayer.cc		\
		aiplayer.cc			\
		mirv.cc			\
		mirvweapon.cc		\
		machinegunround.cc	\
		machinegunweapon.cc	\
		report.cc

OBJECTS = $(SOURCES:.cc=.o)

.cc.o:
	$(CC) $(CFLAGS) $(INCLUDE) $(LOCALINCLUDE) -c $<

$(TARGET):: $(OBJECTS)
	$(CC) $(CFLAGS) $(OBJECTS) $(LIBS) -o ../$(TARGET)

# Clean uses the unix 'rm' command so might not work on windows unless you have
# a version of this.
clean:
	rm -f *.o

depend:
	makedepend -Y $(LOCALINCLUDE) $(SOURCES)

all:	clean depend
	$(MAKE) $(TARGET)

# DO NOT DELETE

interface.o: ./includes/interface.hh ./includes/report.hh
main.o: ./includes/game.hh ./includes/interface.hh ./includes/inifile.hh
main.o: ./includes/report.hh
game.o: ./includes/game.hh ./includes/interface.hh ./includes/inifile.hh
game.o: ./includes/tank.hh ./includes/entity.hh ./includes/sounds.hh
game.o: ./includes/font.hh ./includes/mainmenu.hh ./includes/menu.hh
game.o: ./includes/buttons.hh ./includes/quitmenu.hh ./includes/optionmenu.hh
game.o: ./includes/selector.hh ./includes/controllermenu.hh
game.o: ./includes/controlsfile.hh ./includes/controls.hh
game.o: ./includes/player.hh ./includes/setcontrolsmenu.hh
game.o: ./includes/landscape.hh ./includes/playermenu.hh
game.o: ./includes/winnermenu.hh ./includes/scoremenu.hh
game.o: ./includes/shopmenu.hh ./includes/quake.hh ./includes/missile.hh
game.o: ./includes/trail.hh ./includes/missileweapon.hh ./includes/weapon.hh
game.o: ./includes/shellweapon.hh ./includes/nukeweapon.hh
game.o: ./includes/blast.hh ./includes/humanplayer.hh ./includes/aiplayer.hh
game.o: ./includes/soundentity.hh ./includes/mirv.hh ./includes/mirvweapon.hh
game.o: ./includes/machinegunweapon.hh ./includes/common.hh
landscape.o: ./includes/landscape.hh ./includes/interface.hh
landscape.o: ./includes/common.hh ./includes/inifile.hh
entity.o: ./includes/entity.hh ./includes/game.hh ./includes/interface.hh
entity.o: ./includes/inifile.hh
tank.o: ./includes/tank.hh ./includes/entity.hh ./includes/game.hh
tank.o: ./includes/interface.hh ./includes/inifile.hh ./includes/sounds.hh
tank.o: ./includes/shell.hh ./includes/smoke.hh ./includes/common.hh
tank.o: ./includes/controls.hh ./includes/player.hh ./includes/landscape.hh
tank.o: ./includes/shellweapon.hh ./includes/weapon.hh
tank.o: ./includes/nukeweapon.hh ./includes/missileweapon.hh
tank.o: ./includes/mirvweapon.hh ./includes/machinegunweapon.hh
shell.o: ./includes/shell.hh ./includes/entity.hh ./includes/game.hh
shell.o: ./includes/interface.hh ./includes/inifile.hh ./includes/tank.hh
shell.o: ./includes/sounds.hh ./includes/blast.hh ./includes/common.hh
shell.o: ./includes/soundentity.hh ./includes/trail.hh
shell.o: ./includes/landscape.hh ./includes/player.hh
blast.o: ./includes/blast.hh ./includes/entity.hh ./includes/game.hh
blast.o: ./includes/interface.hh ./includes/inifile.hh
trail.o: ./includes/trail.hh ./includes/entity.hh ./includes/game.hh
trail.o: ./includes/interface.hh ./includes/inifile.hh ./includes/common.hh
font.o: ./includes/font.hh ./includes/interface.hh
smoke.o: ./includes/smoke.hh ./includes/entity.hh ./includes/game.hh
smoke.o: ./includes/interface.hh ./includes/inifile.hh
menu.o: ./includes/menu.hh ./includes/game.hh ./includes/interface.hh
menu.o: ./includes/inifile.hh
mainmenu.o: ./includes/mainmenu.hh ./includes/menu.hh ./includes/game.hh
mainmenu.o: ./includes/interface.hh ./includes/inifile.hh
mainmenu.o: ./includes/buttons.hh ./includes/font.hh
quitmenu.o: ./includes/quitmenu.hh ./includes/menu.hh ./includes/game.hh
quitmenu.o: ./includes/interface.hh ./includes/inifile.hh
quitmenu.o: ./includes/buttons.hh ./includes/font.hh
optionmenu.o: ./includes/optionmenu.hh ./includes/menu.hh ./includes/game.hh
optionmenu.o: ./includes/interface.hh ./includes/inifile.hh
optionmenu.o: ./includes/buttons.hh ./includes/selector.hh ./includes/font.hh
weapon.o: ./includes/weapon.hh ./includes/game.hh ./includes/interface.hh
weapon.o: ./includes/inifile.hh ./includes/tank.hh ./includes/entity.hh
weapon.o: ./includes/sounds.hh
shellweapon.o: ./includes/shellweapon.hh ./includes/weapon.hh
shellweapon.o: ./includes/game.hh ./includes/interface.hh
shellweapon.o: ./includes/inifile.hh ./includes/tank.hh ./includes/entity.hh
shellweapon.o: ./includes/sounds.hh ./includes/shell.hh
shellweapon.o: ./includes/soundentity.hh ./includes/player.hh
nukeweapon.o: ./includes/nukeweapon.hh ./includes/weapon.hh
nukeweapon.o: ./includes/game.hh ./includes/interface.hh
nukeweapon.o: ./includes/inifile.hh ./includes/tank.hh ./includes/entity.hh
nukeweapon.o: ./includes/sounds.hh ./includes/shell.hh
nukeweapon.o: ./includes/soundentity.hh
missileweapon.o: ./includes/missileweapon.hh ./includes/weapon.hh
missileweapon.o: ./includes/game.hh ./includes/interface.hh
missileweapon.o: ./includes/inifile.hh ./includes/tank.hh
missileweapon.o: ./includes/entity.hh ./includes/sounds.hh
missileweapon.o: ./includes/missile.hh ./includes/trail.hh
missileweapon.o: ./includes/soundentity.hh
missile.o: ./includes/missile.hh ./includes/entity.hh ./includes/game.hh
missile.o: ./includes/interface.hh ./includes/inifile.hh ./includes/trail.hh
missile.o: ./includes/sounds.hh ./includes/tank.hh ./includes/blast.hh
missile.o: ./includes/common.hh ./includes/controls.hh ./includes/player.hh
missile.o: ./includes/soundentity.hh ./includes/landscape.hh
playermenu.o: ./includes/playermenu.hh ./includes/menu.hh ./includes/game.hh
playermenu.o: ./includes/interface.hh ./includes/inifile.hh
playermenu.o: ./includes/buttons.hh ./includes/selector.hh ./includes/tank.hh
playermenu.o: ./includes/entity.hh ./includes/sounds.hh
playermenu.o: ./includes/controls.hh ./includes/player.hh ./includes/font.hh
scoremenu.o: ./includes/scoremenu.hh ./includes/menu.hh ./includes/game.hh
scoremenu.o: ./includes/interface.hh ./includes/inifile.hh ./includes/tank.hh
scoremenu.o: ./includes/entity.hh ./includes/sounds.hh ./includes/controls.hh
scoremenu.o: ./includes/player.hh ./includes/font.hh
shopmenu.o: ./includes/shopmenu.hh ./includes/menu.hh ./includes/game.hh
shopmenu.o: ./includes/interface.hh ./includes/inifile.hh ./includes/tank.hh
shopmenu.o: ./includes/entity.hh ./includes/sounds.hh ./includes/weapon.hh
shopmenu.o: ./includes/controls.hh ./includes/player.hh ./includes/font.hh
buttons.o: ./includes/buttons.hh ./includes/menu.hh ./includes/game.hh
buttons.o: ./includes/interface.hh ./includes/inifile.hh ./includes/font.hh
selector.o: ./includes/selector.hh ./includes/menu.hh ./includes/game.hh
selector.o: ./includes/interface.hh ./includes/inifile.hh ./includes/font.hh
controllermenu.o: ./includes/controllermenu.hh ./includes/menu.hh
controllermenu.o: ./includes/game.hh ./includes/interface.hh
controllermenu.o: ./includes/inifile.hh ./includes/buttons.hh
controllermenu.o: ./includes/selector.hh ./includes/controlsfile.hh
controllermenu.o: ./includes/controls.hh ./includes/player.hh
controllermenu.o: ./includes/tank.hh ./includes/entity.hh
controllermenu.o: ./includes/sounds.hh ./includes/font.hh
setcontrolsmenu.o: ./includes/setcontrolsmenu.hh ./includes/menu.hh
setcontrolsmenu.o: ./includes/game.hh ./includes/interface.hh
setcontrolsmenu.o: ./includes/inifile.hh ./includes/buttons.hh
setcontrolsmenu.o: ./includes/selector.hh ./includes/controls.hh
setcontrolsmenu.o: ./includes/player.hh ./includes/tank.hh
setcontrolsmenu.o: ./includes/entity.hh ./includes/sounds.hh
setcontrolsmenu.o: ./includes/font.hh
controlsfile.o: ./includes/controlsfile.hh ./includes/controls.hh
controlsfile.o: ./includes/interface.hh ./includes/player.hh
controlsfile.o: ./includes/tank.hh ./includes/entity.hh ./includes/game.hh
controlsfile.o: ./includes/inifile.hh ./includes/sounds.hh
controls.o: ./includes/controls.hh ./includes/interface.hh
controls.o: ./includes/player.hh ./includes/tank.hh ./includes/entity.hh
controls.o: ./includes/game.hh ./includes/inifile.hh ./includes/sounds.hh
sounds.o: ./includes/sounds.hh ./includes/report.hh
soundentity.o: ./includes/soundentity.hh ./includes/entity.hh
soundentity.o: ./includes/game.hh ./includes/interface.hh
soundentity.o: ./includes/inifile.hh ./includes/sounds.hh
quake.o: ./includes/quake.hh ./includes/entity.hh ./includes/game.hh
quake.o: ./includes/interface.hh ./includes/inifile.hh ./includes/sounds.hh
quake.o: ./includes/landscape.hh
inifile.o: ./includes/inifile.hh
winnermenu.o: ./includes/winnermenu.hh ./includes/menu.hh ./includes/game.hh
winnermenu.o: ./includes/interface.hh ./includes/inifile.hh
winnermenu.o: ./includes/tank.hh ./includes/entity.hh ./includes/sounds.hh
winnermenu.o: ./includes/controls.hh ./includes/player.hh
winnermenu.o: ./includes/common.hh ./includes/font.hh
player.o: ./includes/player.hh ./includes/tank.hh ./includes/entity.hh
player.o: ./includes/game.hh ./includes/interface.hh ./includes/inifile.hh
player.o: ./includes/sounds.hh
humanplayer.o: ./includes/humanplayer.hh ./includes/player.hh
humanplayer.o: ./includes/tank.hh ./includes/entity.hh ./includes/game.hh
humanplayer.o: ./includes/interface.hh ./includes/inifile.hh
humanplayer.o: ./includes/sounds.hh ./includes/controls.hh
aiplayer.o: ./includes/aiplayer.hh ./includes/player.hh ./includes/tank.hh
aiplayer.o: ./includes/entity.hh ./includes/game.hh ./includes/interface.hh
aiplayer.o: ./includes/inifile.hh ./includes/sounds.hh ./includes/shopmenu.hh
aiplayer.o: ./includes/menu.hh ./includes/common.hh ./includes/landscape.hh
mirv.o: ./includes/mirv.hh ./includes/entity.hh ./includes/game.hh
mirv.o: ./includes/interface.hh ./includes/inifile.hh ./includes/trail.hh
mirv.o: ./includes/landscape.hh ./includes/shell.hh ./includes/player.hh
mirv.o: ./includes/tank.hh ./includes/sounds.hh
mirvweapon.o: ./includes/mirvweapon.hh ./includes/weapon.hh
mirvweapon.o: ./includes/game.hh ./includes/interface.hh
mirvweapon.o: ./includes/inifile.hh ./includes/tank.hh ./includes/entity.hh
mirvweapon.o: ./includes/sounds.hh ./includes/mirv.hh
mirvweapon.o: ./includes/soundentity.hh
machinegunround.o: ./includes/machinegunround.hh ./includes/entity.hh
machinegunround.o: ./includes/game.hh ./includes/interface.hh
machinegunround.o: ./includes/inifile.hh ./includes/tank.hh
machinegunround.o: ./includes/sounds.hh ./includes/common.hh
machinegunround.o: ./includes/soundentity.hh ./includes/landscape.hh
machinegunround.o: ./includes/player.hh
machinegunweapon.o: ./includes/machinegunweapon.hh ./includes/weapon.hh
machinegunweapon.o: ./includes/game.hh ./includes/interface.hh
machinegunweapon.o: ./includes/inifile.hh ./includes/sounds.hh
machinegunweapon.o: ./includes/tank.hh ./includes/entity.hh
machinegunweapon.o: ./includes/machinegunround.hh ./includes/soundentity.hh
report.o: ./includes/report.hh
