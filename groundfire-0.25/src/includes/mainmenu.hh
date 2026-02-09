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
//   File name : mainmenu.hh
//
//          By : Tom Russell
//
//        Date : 17-March-03
//
// Description : Handles the title screen menu.
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __MAINMENU_HH__
#define __MAINMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"
#include "buttons.hh"

class cMainMenu : public cMenu
{ 
public:
    cMainMenu (cGame * game);
    virtual ~cMainMenu ();

    enumGameState update (double time);
    void          draw   ();

private:

    cTextButton * _startButton;
    cTextButton * _optionsButton;
    cTextButton * _quitButton;
};

#endif // __MAINMENU_HH__
