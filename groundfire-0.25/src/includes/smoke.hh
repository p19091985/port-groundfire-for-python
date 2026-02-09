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
//   File name : smoke.hh
//
//          By : Tom Russell
//
//        Date : 18-Jan-03
//
// Description : Handles the smoke clouds that rise from destroyed things
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __SMOKE_HH__
#define __SMOKE_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cSmoke : public cEntity
{
public:
    cSmoke  (cGame * game,
             float x,    float y,
             float xVel, float yVel,
             int   texture,
             float rotationRate,
             float growthRate,
             float fadeRate);
    ~cSmoke ();

    void draw (void);
    bool update (float time);

private:
    float _xVel;
    float _yVel;
    float _size;          // The current size of the smoke cloud
    float _rotate;        // The rotation of the smoke cloud
    float _fadeAway;      // How faded the cloud is

    // Constant properties
    int   _texture;       // The texture to use for the smoke
    float _rotationRate;  // The speed for rotation
    float _growthRate;    // How quickly the smoke cloud grows
    float _fadeRate;      // The rate at which the cloud fades.
};

#endif // __SMOKE_HH__
