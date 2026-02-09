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
//   File name : mirv.hh
//
//          By : Tom Russell
//
//        Date : 03-Apr-04
//
// Description : Handles the mirv shells (the ones that split up)
//
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __MIRV_HH__
#define __MIRV_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cPlayer;
class cTrail;
    
class cMirv : public cEntity
{
public:
    cMirv (cGame   * game,
           cPlayer * player,
           float xLaunch,    float yLaunch, 
           float xLaunchVel, float yLaunchVel, 
           float launchTime,
           float size, float damage);
    ~cMirv ();

    void draw (void);
    bool update (float time);

    static void readSettings (cReadIniFile const & settings);

private:

    void explode (float x, float y, int tankToIgnore);

    // Settings Variables
    static int   OPTION_Fragments;
    static float OPTION_Spread;

    // Member Variables
    cPlayer * _player;     // Owner
    float     _xLaunch;
    float     _yLaunch;
    float     _xLaunchVel;
    float     _yLaunchVel;
    float     _launchTime;

    float     _apexTime;

    float     _size;     // Size of the blast radius
    float     _damage;   // damage caused by the mirv
    cTrail  * _trail;    // Trail object we leave behind us
};

#endif // __MIRV_HH__
