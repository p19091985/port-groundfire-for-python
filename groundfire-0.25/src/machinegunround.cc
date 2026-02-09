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
//   File name : machinegunround.cc
//
//          By : Tom Russell
//
//        Date : 08-Sep-02
//
// Description : Handles the machine gun rounds
//
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "machinegunround.hh"
#include "game.hh"
#include "tank.hh"
#include "common.hh"
#include "soundentity.hh"
#include "landscape.hh"
#include "player.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMachineGunRound
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMachineGunRound::cMachineGunRound
(
    cGame   * game,
    cPlayer * player,
    float xLaunch,
    float yLaunch,
    float xLaunchVel,
    float yLaunchVel,
    float launchTime,
    float damage      // Amount of damage the round will do 
)
: cEntity (game),
  _player (player),
  _xLaunchVel (xLaunchVel),
  _yLaunchVel (yLaunchVel),
  _launchTime (launchTime),
  _damage (damage)
{
    _x = _xBack = _xLaunch = xLaunch;
    _y = _yBack = _yLaunch = yLaunch;

    _killNextFrame = false;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMachineGunRound
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMachineGunRound::~cMachineGunRound
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the Round.
//
////////////////////////////////////////////////////////////////////////////////
void
cMachineGunRound::draw
(
    void
)
{
    glLoadIdentity ();

    glColor3f (1.0f, 1.0f, 1.0f);

    // Rounds are drawn as lines
    glBegin (GL_LINES);
    glVertex3f ( _xBack, _yBack, 0.0f);
    glVertex3f ( _x,     _y,     0.0f);
    glEnd ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the round
//
////////////////////////////////////////////////////////////////////////////////
bool
cMachineGunRound::update
(
    float time
)
{
    if (_killNextFrame)
    {
        delete this;
        return (false);    
    }
    else
    {
        
        float oldX = _x;
        float oldY = _y;

        // Calculate the new position of the round using a formula based on the 
        // elapsed time since the round was fired. The advantage of this is that
        // it is completely independent of the game's frame rate.

        // Get the number of seconds passed since the shell was created.
        float timeSinceLaunch = _game->getTime () - _launchTime;

        _x = timeSinceLaunch * _xLaunchVel + _xLaunch;
        _y = timeSinceLaunch * (_yLaunchVel - 5.0f * timeSinceLaunch)
            + _yLaunch;

        // Each round is drawn as a line. To find the back end of the line, we 
        // see where the round was a small time ago.

        timeSinceLaunch -= 0.01;

        if (timeSinceLaunch < 0.0f)
        {
            timeSinceLaunch = 0.0f;
        }

        _xBack = timeSinceLaunch * _xLaunchVel + _xLaunch;
        _yBack = timeSinceLaunch * (_yLaunchVel - 5.0f * timeSinceLaunch) 
            +_yLaunch;

        // If the shell has left the side of the screen.
        if (_x >  (_game->getLandscape ())->getLandscapeWidth () ||
            _x < -(_game->getLandscape ())->getLandscapeWidth ()) 
        {
            // The round has left the side of the screen so destroy it next time
            _killNextFrame = true;
            return (true);
        }

        float collX;
        float collY;

        // Have we hit the ground?
        if ((_game->getLandscape ())->groundCollision (oldX, oldY,
                                                       _x, _y, 
                                                       &collX, &collY))
        {
            _x = collX;
            _y = collY;

            _killNextFrame = true;
            return (true);
        }

        // Check for collision with a tank
        cPlayer ** players = _game->getPlayers ();

        for (int i = 0; i < 8 && players[i] != NULL; i++)
        {
            if (players[i]->getTank ()->intersectTank (oldX, oldY, _x, _y))
            {
                // Play a metallic hit sound
                cSoundEntity * clang = new cSoundEntity
                    (
                        _game,
                        9,
                        false
                    );
        
                _game->addEntity (clang);

                // Do maximum damage to hit tank
                if (players[i]->getTank ()->doDamage (_damage))
                {
                    // The tank was destroyed, credit the kill to the player 
                    // that fired this round.
                    _player->defeat (players[i]);
                }

                _killNextFrame = true;
                break;
            }
        }
    }
    
    return (true);
}
