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
//   File name : shopmenu.hh
//
//          By : Tom Russell
//
//        Date : 01-Jul-03
//
// Description : Handles the shopping menu which appears between rounds
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __SHOPMENU_HH__
#define __SHOPMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"

class cShopMenu : public cMenu
{
    // Allow AI players to access our variables to determine what to do next.
    friend class cAIPlayer;

public:
    cShopMenu (cGame * game);
    ~cShopMenu ();

    enumGameState update (double time);
    void          draw   ();

private: 
    void drawBars (float x, float y, float numberOfBars);

    int   _playerSelectPos[8];
    float _playerSelectDelay[8]; // Countdown the Delay for each player between
                                 // buying or moving rows in the shop
    bool  _playerDone[8];
    bool  _lineLit[10];        // Is this row already lit?

    // Cache the cost of jumpjets.
    int   _jumpjetsCost;
};

#endif // __SHOPMENU_HH__
