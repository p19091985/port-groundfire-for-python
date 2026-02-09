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
//   File name : winnermenu.hh
//
//          By : Tom Russell
//
//        Date : 28-Feb-04
//
// Description : Handles the 'We have a winner' screen
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __WINNERMENU_HH__
#define __WINNERMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"
#include <vector>

class cWinnerMenu : public cMenu
{
public:
    cWinnerMenu (cGame * game);
    ~cWinnerMenu ();

    enumGameState update (double time);
    void          draw   ();

private:

    void drawSpinningLetter (float x, float y, float angle, char charToDraw);

    bool               _draw;
    cPlayer         ** _players;
    vector<cPlayer *>  _winners;
    float              _spinning;

    float              _timeTillActive;
};

#endif // __WINNERMENU_HH__
