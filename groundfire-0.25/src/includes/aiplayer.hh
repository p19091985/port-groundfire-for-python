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
//   File name : aiplayer.hh
//
//          By : Tom Russell
//
//        Date : 27-March-04
//
// Description : Handles computer controlled players
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __AIPLAYER_HH__
#define __AIPLAYER_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "player.hh"

class cAIPlayer : public cPlayer
{
public:
    cAIPlayer (cGame * game,
               int number);
    ~cAIPlayer ();

    void update ();

    void newRound ();

    void recordShot  (float x, float y, int hitTank);
    void recordFired (void);

    // Get the state of a command for an AI player
    bool getCommand (command_t command, double & startTime);

private:
    // Internal functions
    void computeAction ();
    void guessAim ();
    void findNewTarget ();

    // Member Variables
    bool    _commands [11];
    cGame * _game;

    // AI state variables
    cTank * _targetTank;
    float   _targetAngle;
    float   _targetLastXPos;
    float   _targetLastYPos;
    float   _targetPower;

    int     _shotsInAir;
    float   _lastShotX;
    float   _lastShotY;
    bool    _lastShot;
    bool    _ignoreShot;
    bool    _onTarget;
    bool    _aimDirectly;
};

#endif // __AIPLAYER_HH__
