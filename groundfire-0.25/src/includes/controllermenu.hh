////////////////////////////////////////////////////////////////////////////////
//
//               Groundfire
//
////////////////////////////////////////////////////////////////////////////////
//
// Copyright (c) 2004, Tom Russell (tom@groundfire.net)
//
// This file is part of the Groundfire project, distributed under the MIT 
// license. See the file 'COPYING', included with this distribution, for a copy
// of the full MIT licence.
//
////////////////////////////////////////////////////////////////////////////////
//
//   File name : controllermenu.hh
//
//          By : Tom Russell
//
//        Date : 09-Nov-03
//
// Description : Handles the controller configuration menu accessible from the
//               options menu.
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __CONTROLLERMENU_HH__
#define __CONTROLLERMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"
#include "buttons.hh"
#include "selector.hh"
#include "controlsfile.hh"

// Handy names
enum  
{
    KEYBOARD = 0,
    JOYSTICK = 1,
    NONE     = 2
};

struct sJoystick
{
    cSelector   * layout;
    cTextButton * define;
};

class cControllerMenu : public cMenu
{ 
public:
    cControllerMenu  (cGame * game);
    ~cControllerMenu ();

    enumGameState update (double time);
    void          draw   ();

private:
    cControls   * _controls;
    cTextButton * _keyboard[2];
    sJoystick     _joystick[8];
    cTextButton * _backButton;
};

#endif // __CONTROLLERMENU_HH__
