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

# note: This makefile will build a Windows executable by default.
#       'make unix' will build groundfire for a unix system (e.g. Linux).

EXENAME      = groundfire

WIN32FLAGS   = -mwindows -mcpu=i686 -O9 -fomit-frame-pointer -ffast-math
WIN32INCLUDE = 
WIN32LIBS    = -lglfw -lopengl32 -lalut -lopenal32

UNIXFLAGS    = -O3 -fomit-frame-pointer -ffast-math
UNIXINCLUDE  = -I/usr/include -I./includes
UNIXLIBS     = -lglfw -lGL -lGLU -lopenal -lalut -lpthread -lm -ldl

win32::
	cd src ; $(MAKE) TARGET=$(EXENAME) "FLAGS=$(WIN32FLAGS)" "INCLUDE=$(WIN32INCLUDE)" "LIBS=$(WIN32LIBS)"

unix:
	cd src ; $(MAKE) TARGET=$(EXENAME) "FLAGS=$(UNIXFLAGS)" "INCLUDE=$(UNIXINCLUDE)" "LIBS=$(UNIXLIBS)"

clean:
	rm -f $(EXENAME)*
	cd src ; $(MAKE) clean

depend:
	cd src ; $(MAKE) depend

all:	clean depend
	$(MAKE) win32