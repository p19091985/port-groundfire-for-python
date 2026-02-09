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
//   File name : mirv.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "mirv.hh"
#include "trail.hh"
#include "landscape.hh"
#include "shell.hh"
#include "player.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

int   cMirv::OPTION_Fragments;
float cMirv::OPTION_Spread;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMirv
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMirv::cMirv
(
    cGame   * game,
    cPlayer * player,
    float xLaunch,
    float yLaunch,
    float xLaunchVel,
    float yLaunchVel,
    float launchTime,
    float size,    // The size of the blast created when the shell explodes
    float damage   // Amount of damage a direct hit from the shell will do 
)
: cEntity (game),
  _player (player),
  _xLaunchVel (xLaunchVel),
  _yLaunchVel (yLaunchVel),
  _launchTime (launchTime),
  _size (size),
  _damage (damage)
{
    _x = _xLaunch = xLaunch;
    _y = _yLaunch = yLaunch;

    // Create a new trail object to leave behind the shell
    _trail = new cTrail (game, _x, _y);
    _game->addEntity (_trail);

    // Calculate the exact time we'll reach the apex. This is when the mirv
    // will split.
    _apexTime = _launchTime + _yLaunchVel / 10.0f;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMirv
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMirv::~cMirv
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the settings for the mirv entities
//
////////////////////////////////////////////////////////////////////////////////
void 
cMirv::readSettings
(
    cReadIniFile const & settings
)
{
    // The number of fragments the mirv will split into.
    OPTION_Fragments
        = settings.getInt ("Mirv", "Fragments", 5);

    // How widely the fragments spread from their parent's trajectory
    OPTION_Spread
        = settings.getFloat ("Mirv", "Spread", 0.2f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the shell.
//
////////////////////////////////////////////////////////////////////////////////
void
cMirv::draw
(
    void
)
{
    glLoadIdentity ();

    glTranslatef (_x, _y, -6.0f);

    glColor3f (1.0f, 1.0f, 1.0f);

    // Shells are currently drawn as tiny triangles (they look like dots)
    glBegin (GL_TRIANGLES);
    glVertex3f ( 0.00f,  0.018f, 0.0f);
    glVertex3f ( 0.03f, -0.018f, 0.0f);
    glVertex3f (-0.03f, -0.018f, 0.0f);
    glEnd ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the mirv
//
////////////////////////////////////////////////////////////////////////////////
bool
cMirv::update
(
    float time
)
{
    float oldX = _x;
    float oldY = _y;

    float collisionX;
    float collisionY;

    float currentTime = _game->getTime ();

    if (currentTime > _apexTime) 
    {
        // It's time to split the mirv up.

        float splitTime = _apexTime - _launchTime;

        // Work out the x,y coordinates of the apex (i.e. where the split 
        // happens.)
        _x = splitTime * _xLaunchVel + _xLaunch;
        _y = splitTime * (_yLaunchVel - 5.0f * splitTime) + _yLaunch;

        for (int i = 0; i < OPTION_Fragments; i++)
        {
            // Calculate the new xVelocity of this fragment.
            float fragXvel = _xLaunchVel + (_xLaunchVel * OPTION_Spread * 
                                            ((float)i - 
                                             ((OPTION_Fragments - 1) / 2.0f)));

            // Create a standard shell for each fragment.
            cShell * fragment = new cShell 
            (
                _game, 
                _player,
                _x,
                _y,
                fragXvel,
                0.0f, 
                _apexTime,
                _size, 
                _damage,
                false
            );
            _game->addEntity (fragment); 
        }

        // Now that the mirv has split, we don't need it anymore so destroy it.
        _trail->layTrail (_x, _y);
        _trail->setInactive ();

        delete this;
        return (false);
    }

    // Calculate the new position of the mirv using a formula based on the 
    // elapsed time since the mirv was fired. The advantage of this is that it
    // is completely independent of the game's frame rate.

    // Get the number of seconds passed since the shell was created.
    float timeSinceLaunch = _game->getTime () - _launchTime;

    _x = timeSinceLaunch * _xLaunchVel + _xLaunch;
    _y = timeSinceLaunch * (_yLaunchVel - 5.0f * timeSinceLaunch) + _yLaunch;

    // If the mirv has left the side of the screen.
    if (_x >  (_game->getLandscape ())->getLandscapeWidth () ||
        _x < -(_game->getLandscape ())->getLandscapeWidth ()) 
    {

        // Lay a final piece of trail and stop laying trail.
        _trail->layTrail (_x, _y);
        _trail->setInactive ();

        // mirv has left the side of the screen so destroy it
        delete this;
        return (false);
    }

    // Have we hit the ground?
    if ((_game->getLandscape ())->groundCollision (oldX, oldY, _x, _y, 
                                                   &collisionX, 
                                                   &collisionY))
    {       
        _trail->layTrail (collisionX, collisionY);

        explode (collisionX, collisionY, -1);

        return (false);
    }

    _trail->layTrail (_x, _y);

    // Check for collision with a tank
    cPlayer ** players = _game->getPlayers ();

    for (int i = 0; i < 8 && players[i] != NULL; i++)
    {
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
// Description : Explode the mirv at the coordinates provided
//
////////////////////////////////////////////////////////////////////////////////
void
cMirv::explode
(
    float x, 
    float y,
    int   hitTank // The tank to deal full damage to (i.e. the tank we hit)
)
{ 
    _trail->setInactive ();
    
    _game->explosion (x, y,
                      _size,
                      _damage,
                      hitTank, 
                      1,
                      false,
                      _player);

    delete this;
}
