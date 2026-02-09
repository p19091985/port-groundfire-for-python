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
//   File name : missile.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "missile.hh"
#include "game.hh"
#include "tank.hh"
#include "blast.hh"
#include "common.hh"
#include "controls.hh"
#include "soundentity.hh"
#include "inifile.hh"
#include "landscape.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cMissile::OPTION_FuelSupply;
float cMissile::OPTION_SteerSensitivity;
float cMissile::OPTION_Speed;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMissile
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMissile::cMissile
(
    cGame   * game,
    cPlayer * player, // The owner of the missile
    float     x,      // The launch x position
    float     y,      // The launch y position
    float     angle,  // The launch angle
    float     size,   // The size of the blast that this missile will make
    float     damage  // The damage done by a direct hit from this missile
)
: cEntity (game),
  _player (player),
  _angle (angle),
  _size (size),
  _damage (damage)
{
    _x = x;
    _y = y;

    _angleChange = 0.0f;

    // Set the initial fuel supply as specified in the settings file
    _fuel = OPTION_FuelSupply;

    /// Missiles leave a trail. Create a new trail object.
    _trail = new cTrail (game, _x, _y);
    _game->addEntity (_trail);

#ifndef NOSOUND
    // Create the continuous 'missile flying' sound.
    _missileSound = new cSound::cSoundSource (_game->getSound (), 4, true);
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMissile
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMissile::~cMissile
(
)
{
#ifndef NOSOUND
    if (_missileSound)
    {
        delete _missileSound;
    }
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the settings for the missile entities
//
////////////////////////////////////////////////////////////////////////////////
void 
cMissile::readSettings
(
    cReadIniFile const & settings
)
{
    // Seconds worth of fuel carried by each missile
    OPTION_FuelSupply         
        = settings.getFloat ("Missile", "Fuel", 3.0f);

    // How quickly the missile changes direction when the user steers the 
    // missile.
    OPTION_SteerSensitivity 
        = settings.getFloat ("Missile", "SteerSensitivity", 300.0f);

    // The speed at which the missile flies.
    OPTION_Speed
        = settings.getFloat ("Missile", "Speed", 9.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the missile
//
////////////////////////////////////////////////////////////////////////////////
void
cMissile::draw
(
    void
)
{
    glLoadIdentity ();

    // Set the orientation and position of the missile
    glTranslatef (_x, _y, -6.0f);
    glRotatef (_angle, 0.0f, 0.0f, 1.0f);

    glColor3f (1.0f, 1.0f, 1.0f);

    // Currently, the missile is drawn as a rather primitive white shape.
    glBegin (GL_TRIANGLES);

    glVertex3f (-0.08f,  0.00f, 0.0f);
    glVertex3f ( 0.00f,  0.08f, 0.0f);
    glVertex3f ( 0.08f,  0.00f, 0.0f);

    glVertex3f (-0.08f, -0.16f, 0.0f);
    glVertex3f (-0.08f,  0.00f, 0.0f);
    glVertex3f ( 0.08f,  0.00f, 0.0f);

    glVertex3f (-0.08f, -0.16f, 0.0f);
    glVertex3f ( 0.08f,  0.00f, 0.0f);
    glVertex3f ( 0.08f, -0.16f, 0.0f);

    glVertex3f (-0.16f, -0.16f, 0.0f);
    glVertex3f (-0.08f, -0.08f, 0.0f);
    glVertex3f (-0.08f, -0.16f, 0.0f);

    glVertex3f ( 0.08f, -0.08f, 0.0f);
    glVertex3f ( 0.16f, -0.16f, 0.0f);
    glVertex3f ( 0.08f, -0.16f, 0.0f);

    glEnd ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the missile entity. Returns false when the entity has 
//               been destroyed.
//
////////////////////////////////////////////////////////////////////////////////
bool
cMissile::update
(
    float time
)
{
    float oldX = _x;
    float oldY = _y;

    float collisionX;
    float collisionY;

    if (_fuel < 0.0f) 
    {
        _x += _xVel * time;
        _y += _yVel * time;

        _yVel -= 10.0f * time;
    }
    else
    {
        double when; // Not used yet
        
        // The gun left/right controls steer the missile.
        bool steerLeft   = _player->getCommand (CMD_GUNLEFT,  when);
        bool steerRight  = _player->getCommand (CMD_GUNRIGHT, when);
        
        if (steerLeft && !steerRight) 
        {
            _angleChange += OPTION_SteerSensitivity * time;
            
            if (_angleChange > 500.0f)
            {
                _angleChange = 500.0f;
            }
        }
        else if (!steerLeft && steerRight)
        {
            _angleChange -= OPTION_SteerSensitivity * time;
            
            if (_angleChange < -500.0f)
            {
                _angleChange = -500.0f;
            }
        }
        else
        {
            // If not being steered, slowly straighten out the missile path by 
            // reducing 'angleChange' to 0

            if (_angleChange > 0.0f) 
            {
                _angleChange -= 3 * OPTION_SteerSensitivity * time;
                if (_angleChange < 0.0f) 
                {
                    _angleChange = 0.0f;
                }
            }
            
            if (_angleChange < 0.0f)
            {
                _angleChange += 3 * OPTION_SteerSensitivity * time;
                if (_angleChange > 0.0f) 
                {
                    _angleChange = 0.0f;
                }
            }
        }

        // Adjust the flight angle of the missile.
        _angle += time * _angleChange;

        // Calculate the missile's new position
        _x    -= time * sin ((_angle / 180.0f) * PI) * 
            (OPTION_Speed - cos ((_angle / 180.0f) * PI));
        _y    += time * cos ((_angle / 180.0f) * PI) * 
            (OPTION_Speed - cos ((_angle / 180.0f) * PI));
    }

    // If the missile has left the game area...
    if (_x >  (_game->getLandscape ())->getLandscapeWidth () ||
        _x < -(_game->getLandscape ())->getLandscapeWidth ())
    {
        // Stop the trail if it isn't already
        if (_fuel >= 0.0f) 
        {
            _trail->setInactive ();
        }

        // missile has left the side of the screen so destroy it
        delete this;
        return (false);
    }

    // Have we hit the ground?
    if ((_game->getLandscape ())->groundCollision (oldX, oldY, _x, _y, 
                                                   &collisionX, 
                                                   &collisionY))
    {       
        // Lay a final piece of trail going into the ground 
        if (_fuel >= 0.0f)
        {
            _trail->layTrail (collisionX, collisionY);
        }

        explode (collisionX, collisionY, -1);

        return (false);
    }

    if (_fuel >= 0.0f)
    {
        _trail->layTrail (_x, _y);

        _fuel -= time;

        // if the missile has run out of fuel...
        if (_fuel < 0.0f) 
        {
            // Missile that are out of fuel will be in free-fall calculate the
            // current velocity of the missile.
            _xVel = -sin ((_angle / 180.0f) * PI) * 
                (OPTION_Speed - cos ((_angle / 180.0f) * PI));

            _yVel = cos ((_angle / 180.0f) * PI) * 
                (OPTION_Speed - cos ((_angle / 180.0f) * PI));

            // Stop leaving a trail behind us.
            _trail->setInactive ();

#ifndef NOSOUND
            delete _missileSound;
            _missileSound = NULL;
#endif
        }
    }

    // Check for collision with a tank
    cPlayer ** players = _game->getPlayers ();

    for (int i = 0; i < 8 && players[i] != NULL; i++)
    {
        // Check if we've hit this tank. 

        if (players[i]->getTank ()->intersectTank (oldX, oldY, _x, _y))
        {
            explode (_x, _y, i);
            
            return (false);
        }
    }
    
    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : explode
//
// Description : Destroys the missile, blows a hole in the landscape and does 
//               damage to any nearby tanks.
//
////////////////////////////////////////////////////////////////////////////////
void
cMissile::explode
(
    float x, 
    float y,
    int   hitTank // the number of the tank that was directly hit (should be -1 
                  // for no tank.)
)
{
    _game->explosion (x, y,
                      _size,
                      _damage,
                      hitTank, 
                      6,
                      false,
                      _player);
    
    // If not already, disable the laying of a trail behind the missile.
    if (_fuel >= 0)
    {
        _trail->setInactive ();
    }
    
    delete this;
}
