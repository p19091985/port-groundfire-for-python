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
//   File name :smoke.cc
//
//          By : Tom Russell
//
//        Date : 13-Feb-03
//
// Description : Handles the smoke clouds that rise from destroyed things
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "smoke.hh"
#include "game.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cSmoke
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cSmoke::cSmoke
(
    cGame * game,
    float   x,
    float   y,
    float   xVel,
    float   yVel,
    int     texture,      // the smoke texture to use
    float   rotationRate, // Speed at which smoke cloud rotates
    float   growthRate,   // Rate at which smoke cloud expands
    float   fadeRate      // Rate at which smoke cloud fades to nothing
)
    : cEntity (game), _xVel (xVel), _yVel (yVel), 
      _texture (texture), _rotationRate (rotationRate), 
      _growthRate (growthRate), _fadeRate (fadeRate)
{
    _x = x;
    _y = y;
    
    // Set the initial values
    _size     = 0.25f; // The initial size
    _fadeAway = 0.7f;  // the starting transparency 
    _rotate   = 0.0f;  // The initial rotation
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cSmoke
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cSmoke::~cSmoke
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the smoke cloud
//
////////////////////////////////////////////////////////////////////////////////
void
cSmoke::draw
(
    void
)
{
    glEnable (GL_TEXTURE_2D);

    glTexEnvf (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    glEnable (GL_BLEND);
    glDisable (GL_DEPTH_TEST);	

    glLoadIdentity ();

    glRotatef (_rotate, 0.0f, 0.0f, 1.0f);
    
    glTranslatef (_x, _y, -7.0f);

    glColor4f (1.0f, 1.0f, 1.0f, _fadeAway);

    texture (_texture);

    glBegin (GL_QUADS);
    glTexCoord2f (0.0f, 0.0f); glVertex3f (-_size, -_size, 0.0f);
    glTexCoord2f (1.0f, 0.0f); glVertex3f ( _size, -_size, 0.0f);
    glTexCoord2f (1.0f, 1.0f); glVertex3f ( _size,  _size, 0.0f);
    glTexCoord2f (0.0f, 1.0f); glVertex3f (-_size,  _size, 0.0f);
    glEnd ();

    glEnable(GL_DEPTH_TEST);
    glDisable (GL_BLEND);
    glDisable (GL_TEXTURE_2D);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the smoke cloud
//
////////////////////////////////////////////////////////////////////////////////
bool
cSmoke::update
(
    float time
)
{
    _rotate   += time * _rotationRate;
    _size     += time * _growthRate;
    _fadeAway -= time * _fadeRate;

    _x += (_xVel * time);
    _y += (_yVel * time);

    // If we've completely faded away.
    if (_fadeAway < 0.0f)
    {
        delete this;
        return (false);
    }

    return (true);
}
