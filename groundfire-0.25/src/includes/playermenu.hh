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
//   File name : playermenu.hh
//
//          By : Tom Russell
//
//        Date : 26-May-03
//
// Description : Handles the player selection menu
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __PLAYERMENU_HH__
#define __PLAYERMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"
#include "buttons.hh"
#include "selector.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cPlayerMenu : public cMenu
{
public:
    cPlayerMenu (cGame * game);
    ~cPlayerMenu ();

    enumGameState update (double time);
    void          draw   ();
    
private:

    void getPlayerColoursAndNames ();

    void selectAvailableController (int player, int direction);

    void addPlayers ();

    struct sPlayers
    {
        bool          enabled;
        std::string   name;
        sColour       colour;
        cGfxButton  * addButton;
        cGfxButton  * removeButton;
        cSelector   * humanAISelector;
        cSelector   * controller;
    };

    sPlayers      _player[8];

    cSelector   * _numberOfRounds;
    cTextButton * _startButton;
    cTextButton * _backButton;

    int   _playersJoined; // The number of tanks that have joined.

};

#endif // __PLAYERMENU_HH__
