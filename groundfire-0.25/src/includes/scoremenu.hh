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
//   File name : scoremenu.hh
//
//          By : Tom Russell
//
//        Date : 01-May-03
//
// Description : Handles the scoring menu
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __SCOREMENU_HH__
#define __SCOREMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"

class cPlayer;

class cScoreMenu : public cMenu
{
public:
    cScoreMenu (cGame * game);
    ~cScoreMenu ();

    enumGameState update (double time);
    void          draw   ();

private:
    void drawScoreForPlayer     (cPlayer * player, float yPos);
    void addPlayerToOrderedList (cPlayer * player);

    cPlayer * _orderedPlayers[8]; // a list of tanks in order of score
    int       _numOfPlayers;      // Number of tanks in the game

    float     _timeTillActive;  // Don't allow users to quit the menu until this
                                // counter hits zero.

};

#endif // __SCOREMENU_HH__
