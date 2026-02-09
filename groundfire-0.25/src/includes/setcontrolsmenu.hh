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
//   File name : setcontrolsmenu.hh
//
//          By : Tom Russell
//
//        Date : 14-Dec-03
//
// Description : Handles the set controls menu
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __SETCONTROLSMENU_HH__
#define __SETCONTROLSMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"
#include "buttons.hh"
#include "selector.hh"
#include "controls.hh"

class cSetControlsMenu : public cMenu
{ 
public:
    cSetControlsMenu  (cGame * game, int layout);
    ~cSetControlsMenu ();

    enumGameState update (double time);
    void          draw   ();

private:
    cControls   * _controls;

    cTextButton * _controlButtons[NUM_OF_CONTROLS];

    cTextButton * _doneButton;
    cTextButton * _resetToDefaultsButton;

    int _layout;
    int _waitingForKey;

    int _controlKey[NUM_OF_CONTROLS];
};

#endif // __SETCONTROLSMENU_HH__
