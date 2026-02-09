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
//   File name : machinegunround.hh
//
//          By : Tom Russell
//
//        Date : 04-Apr-04
//
// Description : Handles the machine gun rounds
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __MACHINEGUNROUND_HH__
#define __MACHINEGUNROUND_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cPlayer;
    
class cMachineGunRound : public cEntity
{
public:
    cMachineGunRound (cGame   * game,
                      cPlayer * player,
                      float xLaunch,    float yLaunch, 
                      float xLaunchVel, float yLaunchVel, 
                      float launchTime,
                      float damage); 

    ~cMachineGunRound ();

    void draw (void);
    bool update (float time);

private:

    cPlayer * _player;     // Owner

    float     _xLaunch;
    float     _yLaunch;
    float     _xLaunchVel;
    float     _yLaunchVel;
    float     _launchTime;
    float     _damage;     // damage caused by the round

    bool      _killNextFrame;

    float     _xBack;
    float     _yBack;

};

#endif // __MACHINEGUNROUND_HH__
