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
//   File name : missile.hh
//
//          By : Tom Russell
//
//        Date : 24-May-03
//
// Description : Handles the missiles
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __MISSILE_HH__
#define __MISSILE_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"
#include "trail.hh"
#include "sounds.hh"

class cReadInitFile;

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cPlayer;

class cMissile : public cEntity
{
public:
    cMissile (cGame   * game,
              cPlayer * player,
              float x,    float y, 
              float angle,
              float size, float damage);
    ~cMissile ();

    void draw (void);
    bool update (float time);

    static void readSettings (cReadIniFile const & settings);

private:

    void explode (float x, float y, int hitTank);

    // Settings Variables
    static float OPTION_FuelSupply;
    static float OPTION_SteerSensitivity;
    static float OPTION_Speed;

    // Member Variables
    cPlayer * _player;      // Owner
    float     _angle;
    float     _angleChange;
    float     _size;        // Blast size
    float     _damage;      // Damage the missile will do to a tank
    float     _fuel;        // Amount of fuel remaining
    cTrail  * _trail;       // The trail object that we leave behind us
    float     _xVel;
    float     _yVel;

#ifndef NOSOUND
    cSound::cSoundSource * _missileSound;
#endif
};

#endif // __MISSILE_HH__
