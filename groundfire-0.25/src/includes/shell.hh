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
//   File name : shell.hh
//
//          By : Tom Russell
//
//        Date : 08-Sep-02
//
// Description : Handles the shell projectiles (i.e. standard gun projectile / 
//               nukes)
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __SHELL_HH__
#define __SHELL_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cPlayer;
class cTrail;
    
class cShell : public cEntity
{
public:
    cShell (cGame   * game,
            cPlayer * player,
            float xLaunch,    float yLaunch, 
            float xLaunchVel, float yLaunchVel, 
            float launchTime,
            float size, float damage, 
            bool whiteOut);
    ~cShell ();

    void draw (void);
    bool update (float time);

private:

    void explode (float x, float y, int tankToIgnore);

    cPlayer * _player;     // Owner

    float     _xLaunch;
    float     _yLaunch;
    float     _xLaunchVel;
    float     _yLaunchVel;
    float     _launchTime;

    float     _size;     // Size of the blast radius
    float     _damage;   // damage caused by the shell
    cTrail  * _trail;    // Trail object we leave behind us
    bool      _whiteOut; // Whether we cause a white-out on explosion (nukes)
};

#endif // __SHELL_HH__
