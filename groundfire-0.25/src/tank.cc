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
//   File name : tank.cc
//
//          By : Tom Russell
//
//        Date : 08-Sep-02
//
// Description : Handles the player controlled tanks 
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "tank.hh"
#include "game.hh"
#include "shell.hh"
#include "smoke.hh"
#include "common.hh"
#include "controls.hh"
#include "landscape.hh" 

#include "shellweapon.hh"
#include "nukeweapon.hh"
#include "missileweapon.hh"
#include "mirvweapon.hh"
#include "machinegunweapon.hh"

#include <GLFW/glfw3.h>
#include <math.h>

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cTank
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cTank::cTank
(
    cGame   * game,
    cPlayer * owner,
    int       statsPosition // The X position of this tanks in-game stats.
) 
        : cEntity (game), _player (owner)
{
    // Constants

    // The maximum angle, from straight up, that the gun can extend in either 
    // direction.
    _gunAngleMax = 
        (game->getSettings ())->getFloat ("Tank", "MaxGunAngle", 75.0f);

    // The maximum change of angle that can be achieved (in degrees per second)
    _gunAngleMaxChangeSpeed = 
        (game->getSettings ())->getFloat ("Tank", "MaxGunAngleChangeSpeed", 
                                          75.0f);

    // The acceleration of the change of angle (in degrees per second, 
    // per second)
    _gunAngleChangeAcceleration = 
        (game->getSettings ())->getFloat ("Tank", "GunAngleChangeAcceleration",
                                          60.0f);

    // Maximum gun launch speed in units per second 
    _gunPowerMax = 
        (game->getSettings ())->getFloat ("Tank", "GunPowerMax", 20.0f);

    // Minimum gun launch speed in units per second
    _gunPowerMin = 
        (game->getSettings ())->getFloat ("Tank", "GunPowerMin", 1.0f);

    // The maximum rate of change of power in units per second, per second
    _gunPowerMaxChangeSpeed = 
        (game->getSettings ())->getFloat ("Tank", "GunPowerMaxChangeSpeed",
                                          50.0f);

    // The acceleration of the change of power in units per second, per second,
    // per second.
    _gunPowerChangeAcceleration = 
        (game->getSettings ())->getFloat ("Tank", "GunPowerChangeAcceleration",
                                          20.0f);

    // The speed of the tank along the ground in units per second.
    _movementSpeed              = 
        (game->getSettings ())->getFloat ("Tank", "MoveSpeed", 0.2f);

    // The size of the tank. Actually, the base width of the tank is twice this
    // value. Think of it more as the 'radius' of the tank.
    _tankSize            = 
        (game->getSettings ())->getFloat ("Tank", "Size", 0.25f);

    // Strength of gravity on falling tanks
    _tankGravity = 
        (game->getSettings ())->getFloat ("Tank", "Gravity", 5.0f);

    // Effectiveness of jumpjets
    _tankBoost = 
        (game->getSettings ())->getFloat ("Tank", "Boost", 7.0f);

    // Rate at which smoke clouds appear from dead tanks on the ground.
    _groundSmokeReleaseTime = 
        (game->getSettings ())->getFloat ("Tank", "GroundSmokeReleaseTime", 
                                          1.0f);

    // Rate at which smoke clouds appear from dead tanks in the air.
    _airSmokeReleaseTime =
        (game->getSettings ())->getFloat ("Tank", "AirSmokeReleaseTime", 
                                          0.05f);

    // Rate at which jumpjets use up fuel
    _fuelUsageRate = 
        (game->getSettings ())->getFloat ("Tank", "FuelUsageRate", 
                                          0.2f);

    // Create all the weapons that a tank can have
    _weapon[SHELLS]     = new cShellWeapon      (game, this);
    _weapon[MACHINEGUN] = new cMachineGunWeapon (game, this);
    _weapon[MIRVS]      = new cMirvWeapon       (game, this);
    _weapon[MISSILES]   = new cMissileWeapon    (game, this);
    _weapon[NUKES]      = new cNukeWeapon       (game, this);

    _statsPosition  = statsPosition;

    // The tanks initial (maximum) health. This is 100 so that the health can 
    // be roughly measured as a percentage of full health.
    _maxHealth = 100.0f;

    // Set initial fuel supply. We don't start with any.
    _totalFuel = 0.0f;

    // We don't start with jumpjets burning, so set to off.
    _boosting      = false;

#ifndef NOSOUND
    _boostingSound = NULL;
#endif

    _state = TANK_ALIVE;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cTank
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cTank::~cTank
(
)
{
    // Delete the weapons objects for this tank
    for (int i = 0; i < MAX_WEAPONS; i++)
    {
        delete _weapon[i];
    }

#ifndef NOSOUND
    if (_boostingSound)
    {
        delete _boostingSound;
    }
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the tank and the stats for it.
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::draw
(
    void
)
{
    glLoadIdentity ();

    glTranslatef (_x, _y, -6.0f);

    glRotatef (_tankAngle, 0.0f, 0.0f, 1.0f);

    // Draw body of tank
    if (_health < (_maxHealth / 2.0f))
    {
        glEnable (GL_TEXTURE_2D);

        texture (4);

        glColor3f (_colour.r, _colour.g, _colour.b);

        glBegin (GL_QUADS);
        
        glTexCoord2f (0.0f, 0.0f);
        glVertex3f (-_tankSize,          0.0f,      0.0f);
        
        glTexCoord2f (0.0f, 1.0f);
        glVertex3f (-(_tankSize / 2.0f), _tankSize, 0.0f);
        
        glTexCoord2f (1.0f, 1.0f);
        glVertex3f ( (_tankSize / 2.0f), _tankSize, 0.0f);
        
        glTexCoord2f (1.0f, 0.0f);
        glVertex3f ( _tankSize,          0.0f,      0.0f);
        
        glEnd ();
        
        glDisable (GL_TEXTURE_2D);
    }
    else
    {
        glColor3f (_colour.r, _colour.g, _colour.b);

        glBegin (GL_QUADS);
        glVertex3f (-_tankSize,          0.0f,      0.0f);
        glVertex3f (-(_tankSize / 2.0f), _tankSize, 0.0f);
        glVertex3f ( (_tankSize / 2.0f), _tankSize, 0.0f);
        glVertex3f ( _tankSize,          0.0f,      0.0f);
        glEnd ();
    }

    // If the tank is dead, we don't need to draw the aiming
    // arrow or the health bar anymore
    if (_state == TANK_ALIVE)
    {
        // Draw aiming arrow

        // Get the centre of the tank. This will be where the gun will aim from.
        float x, y;
        getCentre (x, y);

        float arrowLength = (_gunPower / 8.0f) + (_tankSize * 2);

        glEnable (GL_BLEND);

        glLoadIdentity ();
        glTranslatef (x, y, -6.0f);
        glRotatef (_gunAngle, 0.0f, 0.0f, 1.0f);

        if (!_weapon[_selectedWeapon]->readyToFire ()) 
        {
            glColor4f (1.0f, 0.0f, 0.0f, 0.5f);
        }
        else
        {
            glColor4f (0.0f, 1.0f, 0.0f, 0.5f);
        }
        
        glBegin (GL_TRIANGLES);
        
        glVertex3f (-0.1f, (_tankSize * 1.5f), 0.0f);
        glVertex3f (-0.1f, arrowLength,        0.0f);
        glVertex3f ( 0.1f, arrowLength,        0.0f);
        
        glVertex3f ( 0.1f, arrowLength,        0.0f);
        glVertex3f ( 0.1f, (_tankSize * 1.5f), 0.0f);
        glVertex3f (-0.1f, (_tankSize * 1.5f), 0.0f);
        
        glVertex3f (-0.2f, arrowLength,        0.0f);
        glVertex3f ( 0.0f, arrowLength + (arrowLength / 4.0f), 0.0f);
        glVertex3f ( 0.2f, arrowLength,        0.0f);  
        
        glEnd ();
        glDisable (GL_BLEND);

        // draw health bar        
        
        glLoadIdentity ();
        
        // Panel

        float startOfBar = -10.0f + (2.5f * _statsPosition) + 0.1f;

        glEnable (GL_BLEND);

        glColor4f (0.5f, 0.9f, 0.6f, 0.3f);

        glBegin (GL_QUADS);
        glVertex3f (startOfBar,         7.4f, 0.0f);
        glVertex3f (startOfBar + 2.3f,  7.4f, 0.0f);
        glVertex3f (startOfBar + 2.3f,  6.6f, 0.0f);
        glVertex3f (startOfBar,         6.6f, 0.0f);
        glEnd ();
        glDisable (GL_BLEND);

        // Draw energy bar.

        startOfBar += 0.1f;

        float endOfBar   = startOfBar + 2.1f * (_health / 100.0f);

        glBegin (GL_QUADS);

        glColor3f (1.0f, 0.5f, 0.5f);
        glVertex3f (startOfBar, 7.4f, 0.0f);
        glVertex3f (startOfBar, 7.3f, 0.0f);

        glColor3f (1.0f - (_health / 200.0f), 0.5f + (_health / 200.0f), 0.5f);
        glVertex3f (endOfBar,   7.3f, 0.0f);
        glVertex3f (endOfBar,   7.4f, 0.0f);

        glEnd ();

        // Draw fuel bar.

        endOfBar   = startOfBar + 2.1f * _fuel;

        glBegin (GL_QUADS);

        glColor3f (0.5f, 0.5f, 0.5f);
        glVertex3f (startOfBar, 7.2f, 0.0f);
        glVertex3f (startOfBar, 7.1f, 0.0f);

        glColor3f (0.5f - (_fuel * 0.5f), 0.5f, 0.5f + (_fuel * 0.5f));
        glVertex3f (endOfBar,   7.1f, 0.0f);
        glVertex3f (endOfBar,   7.2f, 0.0f);

        glEnd ();

        // Draw small tank

        glColor3f (_colour.r, _colour.g, _colour.b);
        glBegin (GL_QUADS);
        glVertex3f (startOfBar + 0.15f, 7.0f, 0.0f);
        glVertex3f (startOfBar + 0.00f, 6.7f, 0.0f);
        glVertex3f (startOfBar + 0.60f, 6.7f, 0.0f);
        glVertex3f (startOfBar + 0.45f, 7.0f, 0.0f);
        glEnd ();

        // Draw the currently selected weapon

        _weapon[_selectedWeapon]->drawGraphic (startOfBar + 0.7f);
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the tank
//
////////////////////////////////////////////////////////////////////////////////
bool
cTank::update
(
    float time
)
{
    bool  boost = false;
    float tiltAngleRadians = (_tankAngle / 180.0f) * PI;
    float cosAngle         = cos (tiltAngleRadians);
    float sinAngle         = sin (tiltAngleRadians);
    
    // Update the owner player (used to make the AIs think)
    _player->update ();

    if (_game->getGameState () != ROUND_STARTING)
    {
        double when; // This is not used yet.
        
        // Are the jumpjets being used?
        boost = _player->getCommand (CMD_JUMPJETS, when);
    }

    // Handle the user input and movement of the tank
    moveTank (time, boost);

    if (_state == TANK_ALIVE)
    {
        if (_game->getGameState () != ROUND_STARTING)
        {
            updateGun (time);

            // If the weapon switch delay has passed.
            if (_switchWeaponTime <= 0.0f)
            {
                double when; // Not used yet
                
                // Do Weapon Selection
                bool weaponLeft  = _player->getCommand (CMD_WEAPONDOWN, when);
                bool weaponRight = _player->getCommand (CMD_WEAPONUP,   when);
                
                // Change weapons
                if (weaponLeft && !weaponRight) 
                {
                    _weapon[_selectedWeapon]->unselect ();
                    _firing = false;

                    for (;;)
                    {
                        _selectedWeapon--;
                        if (_selectedWeapon < 0)
                        {
                            _selectedWeapon = MAX_WEAPONS - 1;
                        }
                        
                        if (_weapon[_selectedWeapon]->select ()) 
                        {
                            break;
                        }
                    }
                    
                    _switchWeaponTime = 0.2f;
                }
                
                if (weaponRight && !weaponLeft) 
                {
                    _weapon[_selectedWeapon]->unselect ();
                    _firing = false;

                    for (;;)
                    {
                        _selectedWeapon++;
                        if (_selectedWeapon == MAX_WEAPONS)
                        {
                            _selectedWeapon = 0;
                        }
                        
                        if (_weapon[_selectedWeapon]->select ()) 
                        {
                            break;
                        }
                    }
                    
                    _switchWeaponTime = 0.2f;
                }
            }
            else
            {
                _switchWeaponTime -= time;
            }
        }
    }
    else
    {
        // Tanks that are dead, sit there burning.
        burn (time);
    }

    // Keep the tank within the screen boundaries.

    if (_x < -10.0f)
    {
        _x             = -10.0f;
        _airbourneXvel = 0.0f;
    }

    if (_x > 10.0f)
    {
        _x             = 10.0f;
        _airbourneXvel = 0.0f;
    }

    // Calculate the angle of the tank by looking at the terrain underneath
    // it
    
    // Get a coordinates of the far left and far right sides of the tank.
    float leftX  = _x - (_tankSize / 2.0f) * cosAngle;
    float leftY  = _y - (_tankSize / 2.0f) * sinAngle;
    float rightX = _x + (_tankSize / 2.0f) * cosAngle;
    float rightY = _y + (_tankSize / 2.0f) * sinAngle;
    
    // Work out how far each side of the tank is inside the terrain

    float leftDisplacement =
        (_game->getLandscape ())->moveToGround (leftX, leftY) - leftY;
    
    float rightDisplacement = 
        (_game->getLandscape ())->moveToGround (rightX, rightY) - rightY;
    
    float midDisplacement = 
        (_game->getLandscape ())->moveToGround (_x, _y) - _y;
    
    float relativeDisplacement;
    float maxDisplacement;
    
    if (midDisplacement > leftDisplacement &&
        midDisplacement > rightDisplacement)
    {
        if (leftDisplacement > rightDisplacement)
        {
            relativeDisplacement = leftDisplacement - midDisplacement;
        }
        else
        {
            relativeDisplacement = midDisplacement - rightDisplacement;
        }
        
        maxDisplacement = midDisplacement;
    }
    else if (rightDisplacement > leftDisplacement)
    {
        if ((rightDisplacement - leftDisplacement) > 
            (2.0f * (rightDisplacement - midDisplacement)))
        {
            relativeDisplacement = midDisplacement - rightDisplacement;
        }
        else
        {
            relativeDisplacement = leftDisplacement - rightDisplacement;
        }
        
        maxDisplacement = rightDisplacement;
    }
    else
    {
        if ((leftDisplacement - rightDisplacement) >
            (2.0f * (leftDisplacement - midDisplacement)))
        {
            relativeDisplacement = midDisplacement - rightDisplacement;
        }
        else
        {
            relativeDisplacement = leftDisplacement - rightDisplacement;
        }
        
        maxDisplacement = leftDisplacement;
    }
    
    // If the tank is a certain minimum distance off the ground, mark it as 
    // such.
    if (maxDisplacement < -0.05f || (boost && maxDisplacement <= 0.0f))
    {
        _onGround = false;
    }
    else
    {
        // Tank is on the ground
        _airbourneXvel = 0.0f;
        _airbourneYvel = 0.0f;
        _onGround = true;

        if (relativeDisplacement > 0.1f)
        {
            relativeDisplacement = 0.1f;
        }
        
        if (relativeDisplacement < -0.1f)
        {
            relativeDisplacement = -0.1f;
        }
        
        _tankAngle -= relativeDisplacement * 75.0f;
        
        _y += maxDisplacement;
    }

    // update the current weapon
    _weapon[_selectedWeapon]->update (time);

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : moveTank
//
// Description : Move the tank according to user input
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::moveTank
(
    float time,
    bool  boost
)
{
    bool  left  = false;
    bool  right = false;

    if (_game->getGameState () != ROUND_STARTING)
    {
        double when; // Not used yet
        
        // Grab the left and right controls
        left  = _player->getCommand (CMD_TANKLEFT,  when);
        right = _player->getCommand (CMD_TANKRIGHT, when);
    }

    float moveX = 0.0f;
    float moveY = 0.0f;

    // Find the angle the tank is orientated at and store the cos and sin
    // because we'll be using it a lot later.
    float tiltAngleRadians = (_tankAngle / 180.0f) * PI;
    float cosAngle = cos (tiltAngleRadians);
    float sinAngle = sin (tiltAngleRadians);

    // If we're using our jumpjets
    if (boost && _state == TANK_ALIVE && _fuel > 0.0f)
    {
        // Use fuel while boosting
        float fuelUsed = time * _fuelUsageRate;

        _totalFuel -= fuelUsed;
        _fuel      -= fuelUsed;

        // leave an exhaust trail while flying

        if (_exhaustTime < 0.0f ) 
        {
            cSmoke * exhaust;
 
            // Exhaust travels backwards, away from the tank.
            float exhaustXvel = _airbourneXvel + sinAngle * 2.0f;
            float exhaustYvel = _airbourneYvel - cosAngle * 2.0f;
            
            exhaust = new cSmoke (_game,
                                  _x, _y,
                                  exhaustXvel, exhaustYvel,
                                  2,     // texture
                                  0.0f,  // rotation
                                  0.0f,  // growth
                                  2.5f); // fade rate

            _game->addEntity (exhaust);

            _exhaustTime += 0.05f;
        }
        else
        {
            _exhaustTime -= time;
        }
        
        // Increase velocity while boosting

        _airbourneYvel += cosAngle * _tankBoost * time;
        _airbourneXvel -= sinAngle * _tankBoost * time;

        // While boosting, the left and right controls angle the tank slightly,
        // allowing some steering.
        if (left && !right && _tankAngle < 15.0f) 
        {
            _tankAngle += (90.0f * time);
        } 
        else if (right && !left && _tankAngle > -15.0f) 
        {
            _tankAngle -= (90.0f * time);
        }
        else
        {
            if (_tankAngle < 0.0f)
            {
                _tankAngle += 90.0f * time;
                if (_tankAngle > 0.0f) 
                {
                    _tankAngle = 0.0f;
                }
            } else if (_tankAngle > 0.0f)
            {
                _tankAngle -= 90.0f * time;
                if (_tankAngle < 0.0f)
                {
                    _tankAngle = 0.0f;
                }
            }
        }

        if (!_boosting) 
        {
#ifndef NOSOUND
            _boostingSound = new cSound::cSoundSource (_game->getSound (), 
                                                       3, 
                                                       true);
#endif
            _boosting = true;
        }
    }
    else if (_boosting)
    {
        _boosting = false;
#ifndef NOSOUND
        delete _boostingSound;
        _boostingSound = NULL;
#endif
    }

    if (true == _onGround)
    {
        bool moved = false;

        // we are on the ground so we can move the tank normally

        if (left && !right && _state == TANK_ALIVE)
        {
            moveX += cosAngle * -_movementSpeed;
            moveY += sinAngle * -_movementSpeed;
            moved = true;
        }
        
        if (right && !left && _state == TANK_ALIVE)
        {
            moveX += cosAngle * _movementSpeed;
            moveY += sinAngle * _movementSpeed;
            moved = true;
        }

        // Over a certain angle of tilt, the tank will start rolling backwards.
        if (fabs(_tankAngle) > 30.0f || moved == true)
        {      
            moveX += cosAngle * -(_movementSpeed * (_tankAngle / 65.0f));
            moveY += sinAngle * -(_movementSpeed * (_tankAngle / 65.0f));
        }
    }
    else
    {
        // We are in the air and not boosting. Thus gravity takes over.

        _airbourneYvel -= (_tankGravity * time);

        moveY           = _airbourneYvel;
        moveX           = _airbourneXvel;
    }

    // Update the tank's position.
    _x += moveX * time;
    _y += moveY * time;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : updateGun
//
// Description : Updates the tank's gun angle and power
//
////////////////////////////////////////////////////////////////////////////////
void 
cTank::updateGun 
(
    float time
)
{
    double when; // Not currently used
    
    // Get all the controls.
    bool gunleft   = _player->getCommand (CMD_GUNLEFT,  when);
    bool gunright  = _player->getCommand (CMD_GUNRIGHT, when);
    bool morePower = _player->getCommand (CMD_GUNUP,    when);
    bool lessPower = _player->getCommand (CMD_GUNDOWN,  when);
    bool fire      = _player->getCommand (CMD_FIRE,     when);
    
    // Control the gun angle

    if (gunleft && !gunright)
    {
        _gunAngleChangeSpeed += time * _gunAngleChangeAcceleration;
        
        if (_gunAngleChangeSpeed > _gunAngleMaxChangeSpeed)
        {
            _gunAngleChangeSpeed = _gunAngleMaxChangeSpeed;
        }
    }
    else if (gunright && !gunleft)
    {
        _gunAngleChangeSpeed -= time * _gunAngleChangeAcceleration;
        
        if (_gunAngleChangeSpeed < -_gunAngleMaxChangeSpeed)
        {
            _gunAngleChangeSpeed = -_gunAngleMaxChangeSpeed;
        }
    }
    else
    {
        // If left or right aren't being pressed stop the gun moving
        _gunAngleChangeSpeed = 0.0f;
    }
    
    // Change the gun angle
    _gunAngle += time * _gunAngleChangeSpeed;
    
    // Limit the angle of the gun to a certain range
    if (_gunAngle < -_gunAngleMax)
    {
        _gunAngle = -_gunAngleMax;
    }
    
    if (_gunAngle > _gunAngleMax)
    {
        _gunAngle = _gunAngleMax;
    }
    
    // Control the power of the gun
    if (morePower)
    {
        _gunPowerChangeSpeed += time * _gunPowerChangeAcceleration;
        
        if (_gunPowerChangeSpeed > _gunPowerMaxChangeSpeed)
        {
            _gunPowerChangeSpeed = _gunPowerMaxChangeSpeed;
        }
    }
    else if (lessPower)
    {
        _gunPowerChangeSpeed -= time * _gunPowerChangeAcceleration;
        
        if (_gunPowerChangeSpeed < -_gunPowerMaxChangeSpeed)
        {
            _gunPowerChangeSpeed = -_gunPowerMaxChangeSpeed;
        }
    }
    else
    {
        // If the up or down controls are not being pressed, stop the power 
        // changing
        _gunPowerChangeSpeed = 0.0f;
    }
    
    _gunPower += time * _gunPowerChangeSpeed;
    
    // Limit the gun power to between its min and max range
    if (_gunPower < _gunPowerMin)
    {
        _gunPower = _gunPowerMin;
    }
    
    if (_gunPower > _gunPowerMax)
    {
        _gunPower = _gunPowerMax;
    }
    
    if (fire && !_firing) 
    {  
        // Attempt to fire the current weapon
        // Note: the parameters passed to 'fire' are currently dummy ones as 
        //       they are not used yet.
        if (!_weapon[_selectedWeapon]->fire (true, 0.0f))
        {
            // Out of ammo, select the normal gun.
            _selectedWeapon = 0;
            _weapon[_selectedWeapon]->select ();
        }
        else
        {
            _firing = true;  
        }
    }
    else if (_firing && !fire)
    {
        // We were firing but not any more. Tell the weapon we've stopped.
        if (!_weapon[_selectedWeapon]->fire (false, 0.0f))
        {
            // Out of ammo, select the normal gun.
            _selectedWeapon = 0;
            _weapon[_selectedWeapon]->select ();
        }
        
        _firing = false;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : setPositionOnGround
//
// Description : Positions the tank on the highest piece of ground at a given x
//               coordinate.
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::setPositionOnGround
(
    float x
)
{
    _x = x;
    _y = (_game->getLandscape ())->moveToGround (x, 100.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : pointInTank
//
// Description : returns 'true' if the specified x,y is inside the body of the 
//               tank, 'false' otherwise.
//
////////////////////////////////////////////////////////////////////////////////
/*
bool
cTank::pointInTank
(
    float x, // IN : the x coordinate of the point we're interested in.
    float y  // IN : the y coordinate of the point we're interested in.
) 
{
    // First check that the point is anywhere near the tank. This speeds up 
    // the rejection time for points obviously not in the tank.
    if (x < (_x + _tankSize) && x > (_x - _tankSize) &&
        y < (_y + _tankSize) && y > (_y - _tankSize))
    { 
        // Get the relative coordinates of the points from the center of the 
        // tank.
        float relX = x - _x;
        float relY = y - _y;

        float angleRads = -(_tankAngle / 180.0f) * PI;

        // transform the point so that it matches the orientation of the tank.
        float transX = relX * cos (angleRads) - relY * sin (angleRads);
        float transY = relX * sin (angleRads) + relY * cos (angleRads);

        // Finally, check the point is within the body of the tank.
        if (transY > 0.0f && transY < _tankSize)
        {
            if (transY < (2.0f * (_tankSize + transX)) && 
                transY < (2.0f * (_tankSize - transX))) 
            {
                return (true);
            }
        }
    }

    return (false);
}
*/
////////////////////////////////////////////////////////////////////////////////
//
// Function    : getCentre
//
// Description : returns the size and centre point of the tank
//
////////////////////////////////////////////////////////////////////////////////
float
cTank::getCentre
(
    float & x, // OUT : The x coordinate of the tank's centre
    float & y  // OUT : The y coordinate of the tank's centre
) 
{
    float angleRads = (_tankAngle / 180.0f) * PI;

    x = _x - sin (angleRads) * (_tankSize / 2.0f);
    y = _y + cos (angleRads) * (_tankSize / 2.0f);

    return (_tankSize * 0.75f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : doDamage
//
// Description : Apply damage to the tank, and kill it if it's out of health.
//               Returns 'false' if tank is still alive, 'true' if dead.
//
////////////////////////////////////////////////////////////////////////////////
bool
cTank::doDamage
(
    float damage // amount of damage to do.
)
{
    _health -= damage; 
    
    if (_health < 0.0f && _state == TANK_ALIVE)
    {
        // The tank has died. Cap health at 0, set it to dead.
        _health      = 0.0f;
        _state       = TANK_DEAD;

        _game->recordTankDeath ();
        
        // Set exhaust timer so that a smoke cloud will be immediately formed.
        _exhaustTime = -0.5f;

        if (_firing)
        {
            // we were firing, obviously we can't any more so tell the weapon.
            _weapon[_selectedWeapon]->fire (false, 0.0f);
            _firing = false;
        }
        
        return (true);
    }
    
    return (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : burn
//
// Description : Produces clouds of smoke from a dead tank
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::burn
(
    float time
)
{
    if (_exhaustTime < 0.0f)
    {
        cSmoke * smoke;
 
        if (_onGround) 
        {
            // When on the ground, produce smoke slowly, but make it last 
            // longer
            
            smoke = new cSmoke (_game,
                                _x, _y + 0.2f,
                                0.0f, 0.5f,
                                5,     // texture
                                0.1f,  // rotation
                                0.3f,  // growth
                                0.15f); // fade rate
            
            _exhaustTime += _groundSmokeReleaseTime;
        }
        else
        {
            // When in the air, produce short lived smoke that is released
            // rapidly. This produces a nice trail effect as the tank crashes
            // to the ground.
            
            smoke = new cSmoke (_game,
                                _x, _y,
                                0.0f, 0.5f,
                                5,     // texture
                                0.1f,  // rotation
                                0.3f,  // growth
                                0.3f); // fade rate
            
            _exhaustTime += _airSmokeReleaseTime;
        }
        
        _game->addEntity (smoke);
    }
    else
    {
        _exhaustTime -= time;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : doPreRound
//
// Description : All the stuff that needs setting up for a tank before the 
//               round begins
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::doPreRound
(
)
{
    if (TANK_RESIGNED != _state)
    {
        _state = TANK_ALIVE;
    }

    // Variables

    // The current angle of the gun
    _gunAngle            = 0.0f;

    // The current rate at which the angle of the gun is changing
    _gunAngleChangeSpeed = 0.0f;

    // The power at which the gun will fire
    _gunPower            = 10.0f;

    // The rate at which the power of the gun is changing
    _gunPowerChangeSpeed = 0.0f;

    // The tilt of the tank
    _tankAngle           = 0.0f;

    // the x velocity of the tank while it is in the air.
    _airbourneXvel       = 0.0f;

    // the y velocity of the tank while it is in the air.
    _airbourneYvel       = 0.0f;

    // A flag which records whether the tank is on the ground, or airbourne.
    _onGround            = false;

    // The health level of the tank
    _health      = _maxHealth;

    // Timer for exhaust/smoke cloud releases
    _exhaustTime = 0.0f;
    
    // Set fuel supply for round
    _fuel = _totalFuel;

    if (_fuel > 1.0f) 
    {
        _fuel = 1.0f;
    }

    // Select weapon.
    _selectedWeapon = SHELLS;

    for (int i = 0; i < MAX_WEAPONS; i++) 
    {
        _weapon[i]->setAmmoForRound ();
    }

    // Initialise the weapon
    _weapon[_selectedWeapon]->select ();

    // Time before we can change weapons again.
    _switchWeaponTime = 0.0f;

    // Start the round not firing.
    _firing = false;
}


////////////////////////////////////////////////////////////////////////////////
//
// Function    : doPostRound
//
// Description : Tidy up after a round.
//
////////////////////////////////////////////////////////////////////////////////
bool
cTank::doPostRound
(
)
{

    if (_firing)
    {
        // we were firing, so stop
        _weapon[_selectedWeapon]->fire (false, 0.0f);
        _firing = false;
    }

#ifndef NOSOUND    
    // Stop the 'jumpjets' sound if currently playing
    if (_boostingSound)
    {
        delete _boostingSound;
        _boostingSound = NULL;
        _boosting = false;
    }
#endif
    
    // Don't destroy the tank between rounds.
    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : gunLaunchPosition
//
// Description : Get the launch position from the gun
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::gunLaunchPosition
(
    float & x,
    float & y
)
{
    getCentre (x, y);

    x += (-degSin (_gunAngle) * _tankSize * 1.2f);
    y += ( degCos (_gunAngle) * _tankSize * 1.2f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : gunLaunchVelocity
//
// Description : Get the x/y velocity from the angle and power of the gun
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::gunLaunchVelocity
(
    float &xVel,
    float &yVel
)
{
    xVel = _airbourneXvel - degSin (_gunAngle) * _gunPower;
    yVel = _airbourneYvel + degCos (_gunAngle) * _gunPower;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : gunLaunchVelocityAtPower
//
// Description : Get the x/y velocity from the angle of the gun and the power 
//               specified.
//
////////////////////////////////////////////////////////////////////////////////
void
cTank::gunLaunchVelocityAtPower
(
    float &xVel,
    float &yVel,
    float power
)
{
    xVel = _airbourneXvel - degSin (_gunAngle) * power;
    yVel = _airbourneYvel + degCos (_gunAngle) * power;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readyToFire
//
// Description : Is this tank able to fire the current weapon?
//
////////////////////////////////////////////////////////////////////////////////
bool 
cTank::readyToFire
(
)
    const
{
    return (_weapon[_selectedWeapon]->readyToFire ());
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : intersectTank
//
// Description : Does a line intersect the tank?
//
////////////////////////////////////////////////////////////////////////////////
bool
cTank::intersectTank
(
    float x1,
    float y1,
    float x2,
    float y2
)
    const
{
    // This is a roughly the maximum distance that is considered to be 'near the
    // tank'
    float nearTank = _tankSize * 1.12;

    // If both ends of the line are too far to the left to be in collision 
    // with the tank we can't be intersecting
    if (x1 < (_x - nearTank) && x2 < (_x - nearTank))
    {
        return (false);
    }
    
    // If both ends of the line are too far to the right to be in collision 
    // with the tank we can't be intersecting
    if (x1 > (_x + nearTank) && x2 > (_x + nearTank))
    {
        return (false);
    }

    // If both ends of the line are too far below the tank to be in collision 
    // with the tank we can't be intersecting
    if (y1 < (_y - nearTank) && y2 < (_y - nearTank))
    {
        return (false);
    }

    // If both ends of the line are too far above the tank to be in collision 
    // with the tank we can't be intersecting
    if (y1 > (_y + nearTank) && y2 > (_y + nearTank))
    {
        return (false);
    }

    // Ok, we've rejected the obviously none colliding lines, so we can do a 
    // more accurate check between the tank and the line.
    
    // Transform the line points to be relative to the tank's coordinates.
    float rx1 = x1 - _x;
    float ry1 = y1 - _y;
    float rx2 = x2 - _x;
    float ry2 = y2 - _y;

    // Get the angle (in radians) to rotate the points to match them to the 
    // orientation of the tank.
    float angleRads = -(_tankAngle / 180.0f) * PI;

    // Cache the sine and cosine of this angle
    float cosAng = cos (angleRads);
    float sinAng = sin (angleRads);

    // transform the line to be in the same orientation as the tank.
    float tx1 = rx1 * cosAng - ry1 * sinAng;
    float ty1 = rx1 * sinAng + ry1 * cosAng;
    float tx2 = rx2 * cosAng - ry2 * sinAng;
    float ty2 = rx2 * sinAng + ry2 * cosAng;

    float xLen = (tx2 - tx1);
    float yLen = (ty2 - ty1);

    bool horizontal;
    float m;
    float c;

    if (fabsf(xLen) > fabsf(yLen))
    {
        // do horizontal line checking   
        m = yLen / xLen; 
        c = ty1 - m * tx1;
        horizontal = true;
    }
    else
    {
        // do vertical line checking
        m = xLen / yLen;
        c = tx1 - m * ty1;
        horizontal = false;
    }

    // Check line against the bottom of the tank
    if ((ty1 > 0.0f && ty2 < 0.0f) || (ty1 < 0.0f && ty2 > 0.0f))
    {
        float xIntersect = horizontal ? (-c / m) : c;

        if (xIntersect > -_tankSize && xIntersect < _tankSize)
        {
            // Bottom of tank intersects the line!
            return (true);
        }
    }

    // Check line against the top of the tank
    if (   (ty1 > _tankSize && ty2 < _tankSize) 
        || (ty1 < _tankSize && ty2 > _tankSize))
    {
        float xIntersect = 
            horizontal ? ((_tankSize - c) / m) : (_tankSize * m) + c;

        if (xIntersect > -(_tankSize / 2.0f) && xIntersect < (_tankSize / 2.0f))
        {
            // Top of tank intersects the line!
            return (true);
        }
    }

    // Check line against the left side of the tank
    float xIntersect = horizontal 
        ? ((2 * _tankSize) - c) / (m - 2) 
        : ((2 * m * _tankSize) + c) / (1 - 2 * m);

    if ((   (xIntersect >= tx1 && xIntersect <= tx2) 
         || (xIntersect <= tx1 && xIntersect >= tx2))
        && (xIntersect > -_tankSize && xIntersect < (-_tankSize / 2.0f)))
    {
        // Left of tank intersects the line!
        return (true);
    }

    // Check line against right side of the tank
    xIntersect = horizontal
        ? (2 * _tankSize - c) / (m + 2)
        : ((2 * m * _tankSize) + c) / (1 + 2 * m);

    if ((   (xIntersect >= tx1 && xIntersect <= tx2)
         || (xIntersect <= tx1 && xIntersect >= tx2))
        && (xIntersect < _tankSize && xIntersect > (_tankSize / 2.0f)))
    {
        // Right of tank intersects the line!
        return (true);
    }

    // Got this far so the line obviously doesn't intersect the tank.
    return (false);   
}
