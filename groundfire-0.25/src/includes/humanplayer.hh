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
//   File name : humanplayer.hh
//
//          By : Tom Russell
//
//        Date : 24-March-04
//
// Description : Handles local-human (non-AI) players
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __HUMANPLAYER_HH__
#define __HUMANPLAYER_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "player.hh"

class cControls;

class cHumanPlayer : public cPlayer
{
public:
    cHumanPlayer (cGame * game,
                  int number, 
                  int controller,
                  cControls * controls);
    ~cHumanPlayer ();

    // Get the state of a command for a human player
    bool getCommand (command_t command, double & startTime);

    int getController () const { return (_controller); }

private:
    int         _controller;
    cControls * _controls;
};

#endif // __HUMANPLAYER_HH__
