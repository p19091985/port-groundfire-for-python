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
//   File name : shell.cc
//
//          By : Tom Russell
//
//        Date : 08-Sep-02
//
// Description : Handles the shell projectiles (i.e. standard gun projectile / 
//               nukes)
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "shell.hh"
#include "game.hh"
#include "tank.hh"
#include "blast.hh"
#include "common.hh"
#include "soundentity.hh"
#include "trail.hh"
#include "landscape.hh"
#include "player.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cShell
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cShell::cShell
(
    cGame   * game,
    cPlayer * player,
    float xLaunch,
    float yLaunch,
    float xLaunchVel,
    float yLaunchVel,
    float launchTime,
    float size,    // The size of the blast created when the shell explodes
    float damage,  // Amount of damage a direct hit from the shell will do 
    bool  whiteOut // Will the shell cause a white flash when it explodes? 
)
: cEntity (game),
  _player (player),
  _xLaunchVel (xLaunchVel),
  _yLaunchVel (yLaunchVel),
  _launchTime (launchTime),
  _size (size),
  _damage (damage),
  _whiteOut (whiteOut)
{
    _x = _xLaunch = xLaunch;
    _y = _yLaunch = yLaunch;

    // Create a new trail object to leave behind the shell
    _trail = new cTrail (game, _x, _y);
    _game->addEntity (_trail);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cShell
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cShell::~cShell
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the shell.
//
////////////////////////////////////////////////////////////////////////////////
void
cShell::draw
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
// Description : Update the shell
//
////////////////////////////////////////////////////////////////////////////////
bool
cShell::update
(
    float time
)
{
    float oldX = _x;
    float oldY = _y;

    float collisionX;
    float collisionY;

    // Calculate the new position of the shell using a formula based on the 
    // elapsed time since the shell was fired. The advantage of this is that it
    // is completely independent of the game's frame rate.

    // Get the number of seconds passed since the shell was created.
    float timeSinceLaunch = _game->getTime () - _launchTime;

    _x = timeSinceLaunch * _xLaunchVel + _xLaunch;
    _y = timeSinceLaunch * (_yLaunchVel - 5.0f * timeSinceLaunch) + _yLaunch;

    // If the shell has left the side of the screen.
    if (_x >  (_game->getLandscape ())->getLandscapeWidth () ||
        _x < -(_game->getLandscape ())->getLandscapeWidth ()) 
    {

        // Lay a final piece of trail and stop laying trail.
        _trail->layTrail (_x, _y);
        _trail->setInactive ();

        // Tell the player who fired the shell that it's left the screen 
        // (this is for the AI)
        _player->recordShot (_x, _y, -1);

        // shell has left the side of the screen so destroy it
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
// Description : Explode the shell at the coordinates provided
//
////////////////////////////////////////////////////////////////////////////////
void
cShell::explode
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
                      _whiteOut ? 7 : 1,
                      _whiteOut,
                      _player);

    // Tell the player where the shot landed (needed by the AI)
    _player->recordShot (x, y, hitTank);

    delete this;
}
