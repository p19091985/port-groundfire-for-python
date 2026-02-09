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
//   File name : aiplayer.cc
//
//          By : Tom Russell
//
//        Date : 27-Mar-04
//
// Description : Handles computer controlled players
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "aiplayer.hh"
#include "game.hh"
#include "shopmenu.hh"
#include "common.hh"
#include "landscape.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cAIPlayer
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cAIPlayer::cAIPlayer
(
    cGame     * game,
    int         number
)
        : cPlayer (game, number), _game (game)
{
    // clear the commands list
    for (int i = 0; i < 11; i++)
    {
        _commands[i] = false;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cAIPlayer
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cAIPlayer::~cAIPlayer
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : newRound
//
// Description : Set up for a new round
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::newRound
(
)
{
    // Do the initialisation on our parent class
    cPlayer::newRound ();

    _targetTank  = NULL;
    _targetAngle = 0.0f;
    _targetPower = 0.0f;

    _onTarget   = false;
    _ignoreShot = false;
    _shotsInAir = 0;
    _lastShot   = false;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Calculate the AI's next move
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::update
(
)
{
    // clear the commands list
    for (int i = 0; i < 11; i++)
    {
        _commands[i] = false;
    }

    // decide what to do
    switch (_game->getGameState ())
    {
    case SHOP_MENU:
    {
        cShopMenu * menu = (cShopMenu *)_game->getCurrentMenu ();
        
        if (menu->_playerSelectPos[_number] != 10)
        {
            _commands[CMD_GUNUP] = true;
        }
        else
        {
            _commands[CMD_FIRE] = true;
        }
    }
    break;

    case ROUND_IN_ACTION:
        computeAction ();
        break;

    default:
        break;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getCommand
//
// Description : Get the state of a control for a human player
//
////////////////////////////////////////////////////////////////////////////////
bool
cAIPlayer::getCommand
(
    command_t   command,
    double    & startTime
)
{
    startTime = 0;

    return (_commands[command]);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : computeAction
//
// Description : Work out what to do during a round
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::computeAction
(
)
{
    if (_targetTank == NULL)
    {
        // choose a tank to aim at
        findNewTarget ();

        // Calculate a good starting aim at this tank.
        guessAim ();
    }
    else
    {
        // We already have a tank to aim for...

        // First check that our target tank is still alive...
        if (_targetTank->_state == TANK_ALIVE)
        {
            // Has the tank moved substantially from its original position?
            if (    sqr (_targetTank->_x - _targetLastXPos)
                  + sqr (_targetTank->_y - _targetLastYPos) > 4.00f) 
            {
                // Yes it has, the target has probably used jumpjets to escape. 
                // Look for another tank to kill.
                _targetTank = NULL;
            }
            else
            {
                // Set readytofire as 'true' if we have not finished aiming, 
                // this will be set to false before the ready-to-fire check is 
                // executed.
                bool readyToFire = true;

                // Change angle to target tank
                float angleDiff = _tank._gunAngle - _targetAngle;

                // Are we near enough to our target angle?
                if (angleDiff > 1.0f)
                {
                    // Still aiming, move gun right
                    _commands[CMD_GUNRIGHT] = true;
                    readyToFire = false;
                }
                else if (angleDiff < -1.0f)
                {
                    // Still aiming, more gun left
                    _commands[CMD_GUNLEFT] = true;
                    readyToFire = false;
                }

                // Change power to target tank.
                float powerDiff = _tank._gunPower - _targetPower;

                // Are we near enough to our target power?
                if (powerDiff > 0.2f)
                {
                    _commands[CMD_GUNDOWN] = true;
                    readyToFire = false;
                }
                else if  (powerDiff < -0.2f)
                {
                    _commands[CMD_GUNUP] = true;
                    readyToFire = false;
                }

                if (readyToFire && _tank.readyToFire ())
                {
                    if (_aimDirectly)
                    {
                        // Check that the tank we're pointing at hasn't moved to
                        // far.
                        if (  sqr (_targetTank->_x - _targetLastXPos) 
                              + sqr (_targetTank->_y - _targetLastYPos) > 0.04f)
                        {
                            // It's moved! Re-aim!
                            readyToFire = false;
                            guessAim ();
                        }
                    }

                    if (readyToFire && _shotsInAir == 0)
                    {
                        _commands[CMD_FIRE] = true;
                    }
                }
            }
        }
        else
        {
            // The tank we were aiming at has been destroyed, by us or someone 
            // else. Either way, we need to select a new tank to aim at. Setting
            // targetTank to NULL will cause a new target tank to be selected 
            // the next time we enter this function.
            _targetTank = NULL;
        }

        if (!_targetTank)
        {
            if (_shotsInAir > 0)
            {
                // Ignore shot tells the 'recordShot' function to ignore the 
                // next shot that is passed to it. The chances are this shot was
                // fired against the tank that has just been destroyed, in which
                // case it has nothing to do with our current aiming which is
                // against a different tank.
                _ignoreShot = true;
            }

            // Do not compare the next shot to the last one because they will 
            // be against different targets.
            _lastShot = false;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : recordFired
//
// Description : Tells the AI that a shot was fired sucessfully 
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::recordFired
(
)
{
    _shotsInAir++;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : recordShot
//
// Description : note where our last shot landed
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::recordShot
(
    float x,
    float y,
    int   hitTank
)
{
    _shotsInAir--;

    // If we hit a tank and it's alive
    if (hitTank != -1 && (_game->getPlayers ())[hitTank]->_tank.alive ()) 
    {
        // Cool! We hit a tank.

        if (hitTank == _number)
        {
            // Not cool. We hit ourself. Pick a different tank to aim at
            _targetTank = NULL;
        }
        else if (!_targetTank || hitTank != _targetTank->_player->_number)
        {
            // We hit a tank but not the one we were aiming for. However, let's
            // not let this opportunity go to waste. Kill THIS tank instead!
            _targetTank = &(_game->getPlayers ())[hitTank]->_tank;

            _targetLastXPos = _targetTank->_x;
            _targetLastYPos = _targetTank->_y;

            _onTarget = true;
        }
        else
        {
            // Bullseye! We hit the tank we were aiming at!
            _onTarget = true;
        }
    }
    else
    {
        if (_aimDirectly)
        {
            // We were aiming directly at a target and missed. Obviously 
            // something was in the way. Try aiming normally instead.

            _aimDirectly = false;

            guessAim ();

            // Don't use this shot's position to adjust the next shot.
            _lastShot = false;
        }
        else
        {

            // Should we alter our aim based on where this shot impacted?
            if (!_ignoreShot) 
            {
                float previousXDistance = _lastShotX - _targetTank->_x;
                float currentXDistance  =  x         - _targetTank->_x;

                if (_lastShot 
                    &&
                    ((currentXDistance < 0.0f && previousXDistance < 0.0f 
                      && currentXDistance < previousXDistance)
                     ||
                     (currentXDistance > 0.0f && previousXDistance > 0.0f 
                     && currentXDistance > previousXDistance)))
                {
                    // Our shots are getting worse (further away from the
                    // target). This is usually because there is a mountatin in
                    // between us and the target. To shoot over it, shoot with
                    // more power and at a higher angle.

                    _targetAngle /= 2.0f;
                    _targetPower += 2.0f;

                    // Don't let our target power be more than the maximum 
                    // possible.
                    if (_targetPower > _tank._gunPowerMax)
                    {
                        _targetPower = _tank._gunPowerMax;
                    }

                    _lastShot = false;
                }
                else
                {
                    // Continue adjusting our angle to try and get a better 
                    // shot. 

                    // Did the shot land to the left or right of the target.
                    if (currentXDistance < 0.0f)
                    {
                        _targetAngle +=  fabsf(degSin (_targetAngle)) 
                            * currentXDistance * 4.0f;

                        if (_targetAngle < -_tank._gunAngleMax)
                        {
                            _targetAngle = -_tank._gunAngleMax;
                        }

                        if (_targetTank->_x < _tank._x)
                        {
                            _targetPower -= 
                                -currentXDistance * 1.2f * 
                                (1 - degSin (fabsf (_targetAngle)));
                        }
                        else
                        {
                            _targetPower += 
                                -currentXDistance * 1.2f * 
                                (1 - degSin (fabsf (_targetAngle)));
                        }
                    }
                    else 
                    {
                        _targetAngle += fabsf(degSin (_targetAngle)) 
                            * currentXDistance * 4.0f;

                        if(_targetAngle > _tank._gunAngleMax)
                        {
                            _targetAngle = _tank._gunAngleMax;
                        }

                        if (_targetTank->_x < _tank._x)
                        {
                            _targetPower += 
                                currentXDistance * 1.2f * 
                                (1 - degSin (fabsf (_targetAngle)));
                        }
                        else
                        {
                            _targetPower -= 
                                currentXDistance * 1.2f * 
                                (1 - degSin (fabsf (_targetAngle)));
                        }
                    }         

                    if (_targetPower < _tank._gunPowerMin)
                    {
                        _targetPower = _tank._gunPowerMin;
                    } 
                    else if (_targetPower > _tank._gunPowerMax)
                    {
                        _targetPower = _tank._gunPowerMax;
                    }

                    _lastShot  = true;
                }

                // We didn't hit our target, keep aiming
                _onTarget = false;            
            }
            else 
            {
                // We have been told to ignore the current shot, but subsequent 
                // ones should not be ignored.
                _ignoreShot = false;
            }
        }
    }   

    // Record where this shot landed so that the next time we enter this 
    // function we can see if our aiming is getting better or worse.
    _lastShotX = x;
    _lastShotY = y;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : guessAim
//
// Description : Take a guess at the aim needed to hit a tank
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::guessAim
(
)
{   
    // How far in the x dimension is the tank from us?
    float xDifference = _targetTank->_x - _tank._x;

    if (_aimDirectly)
    {
        // We are going to attempt to fire straight at the target tank, full 
        // power.

        float yDifference = _targetTank->_y - _tank._y;

        if (yDifference > 0.2f) 
        {          
            _targetAngle = -(atanf (xDifference / yDifference) / PI) * 180.0f;
            _targetPower = _tank._gunPowerMax;

            if (_targetAngle > _tank._gunAngleMax 
                || _targetAngle < -_tank._gunAngleMax)
            {
                _aimDirectly = false;
            }
        }
        else 
        {
            _aimDirectly = false;
        }
    }

    // Record the tanks current position so we can see if it's moved later.
    _targetLastXPos = _targetTank->_x;
    _targetLastYPos = _targetTank->_y;

    if (!_aimDirectly)
    {    
        _targetAngle    = -xDifference * 3.0f;
        _targetPower    = 10.0f;
    }

    // Clip the angle to the maximum angle
    if (_targetAngle > _tank._gunAngleMax)
    {
        _targetAngle = _tank._gunAngleMax;
    }
    else if (_targetAngle < -_tank._gunAngleMax)
    {
        _targetAngle = -_tank._gunAngleMax;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : findNewTarget
//
// Description : Choose a new tank to target
//
////////////////////////////////////////////////////////////////////////////////
void
cAIPlayer::findNewTarget
(
)
{
    cPlayer ** players = _game->getPlayers ();

    int topScore = 0;

    _aimDirectly = false;

    // We need to find a new tank to aim at.
    for (int i = 0; i < _game->getNumOfPlayers (); i++)
    {
        int score = 0;

        if (players[i] != this && players[i]->_tank._state == TANK_ALIVE)
        {
            // Work out a score for this tank.

            float startX, startY;
            float endX, endY;

            cTank * enemyTank = &players[i]->_tank;

            _tank.gunLaunchPosition (startX, startY);
            enemyTank->getCentre (endX, endY);

            if (!_game->getLandscape ()->groundCollision (startX, startY, 
                                                          endX, endY,
                                                          NULL, NULL))
            {
                // We are in direct line-of-sight to this tank, that's a BIG 
                // plus!
                score += 100;

                if (enemyTank->_y > _tank._y)
                {
                    // Give extra points to tanks higher up than us. There is a
                    // good chance we can point our gun straight at them.
                    score += 50;
                    _aimDirectly = true;
                }
            }

            score += 40 - (int)rintf(2.0f * fabsf (enemyTank->_x - _tank._x));

            // Have we found a better tank than all the others reviewed so far?
            if (score >= topScore) 
            {
                // Yes, target this tank until a better one can be found.
                topScore = score;
                _targetTank = &players[i]->_tank;
            }
        }
    }
}
