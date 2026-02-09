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
//   File name : machinegunweapon.cc
//
//          By : Tom Russell
//
//        Date : 04-Apr-04
//
// Description : Handles the machine gun weapon of a tank
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "machinegunweapon.hh"

#include "game.hh"
#include "tank.hh"
#include "machinegunround.hh"
#include "soundentity.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cMachineGunWeapon::OPTION_CooldownTime;
float cMachineGunWeapon::OPTION_Damage;
float cMachineGunWeapon::OPTION_Speed;
int   cMachineGunWeapon::OPTION_Cost;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMachineGunWeapon
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMachineGunWeapon::cMachineGunWeapon
(
    cGame * game,
    cTank * ownerTank
)
: cWeapon (game, ownerTank)
{
    // We don't start with an machine gun rounds.
    _quantity     = 0;
    _cooldownTime = OPTION_CooldownTime;

    // Set the cost of this weapon in the shop
    _cost         = OPTION_Cost;

#ifndef NOSOUND
    _gunSound     = NULL;
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMachineGunWeapon
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMachineGunWeapon::~cMachineGunWeapon
(
)
{
#ifndef NOSOUND
    if (_gunSound)
    {
        delete _gunSound;
    }
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the options file settings regarding nukes
//
////////////////////////////////////////////////////////////////////////////////
void 
cMachineGunWeapon::readSettings
(
    cReadIniFile const & settings
)
{
    // The time between firing rounds (The firing rate)
    OPTION_CooldownTime
        = settings.getFloat ("MachineGun", "CooldownTime", 0.1f);

    // The damage done to a tank by a hit from a machine gun round.
    OPTION_Damage
        = settings.getFloat ("MachineGun", "Damage", 2.0f);

    // The speed of the machine gun rounds
    OPTION_Speed
        = settings.getFloat ("MachineGun", "Speed", 25.0f);

    // The cost of Machine Gun Rounds in the shop
    OPTION_Cost
        = settings.getInt ("Price", "MachineGun", 50);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : fire
//
// Description : Fires a round. Return value is whether or not we can fire 
//               another round after this one (i.e. have we run out.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cMachineGunWeapon::fire 
(
    bool  firing,
    float time    // FUTURE : Currently ignored
)
{
    if (firing)
    {
#ifndef NOSOUND
        // Play the looping machine gun sound
        _gunSound = new cSound::cSoundSource (_game->getSound (), 8, true);
#endif
    }
    else
    {
#ifndef NOSOUND
        if (_gunSound)
        {
            delete _gunSound;
            _gunSound = NULL;
        }
#endif
    }

    // if we're all out of rounds, return false
    if (_quantityAvailable == 0)
    {
        return (false);
    }
    
    return  (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the machine gun weapon
//
////////////////////////////////////////////////////////////////////////////////
void
cMachineGunWeapon::update
(
    float time
)
{
    if (_ownerTank->isFiring () && _quantityAvailable != 0)
    {
        _cooldown -= time;

        while (_cooldown < 0.0f &&  _quantityAvailable != 0)
        {
            float xInitial;
            float yInitial;
            float xVelInitial;
            float yVelInitial;
            
            // Get the launch position and velocity for the round from the owner
            _ownerTank->gunLaunchPosition (xInitial, yInitial);
            _ownerTank->gunLaunchVelocityAtPower (xVelInitial, yVelInitial, 
                                                  OPTION_Speed);
        
            // Create the bullet!
            cMachineGunRound * round = new cMachineGunRound 
                (
                    _game, 
                    _ownerTank->getPlayer (),
                    xInitial,
                    yInitial,
                    xVelInitial,
                    yVelInitial, 
                    _game->getTime () + _cooldown,
                    OPTION_Damage
                    );
            
            _game->addEntity (round);
            
            // reduce the number of rounds we're carrying
            _quantity--;
            _quantityAvailable--;
            
            _cooldown += _cooldownTime;
        }
        
#ifndef NOSOUND
        if (_quantityAvailable == 0)
        {
            if (_gunSound)
            {
                delete _gunSound;
                _gunSound = NULL;
            }
        }
#endif

    }
    else if (_cooldown > 0.0f)
    {
        _cooldown -= time;
        if (_cooldown < 0.0f)
        {
            _cooldown = 0.0f;
        }
    }
}


////////////////////////////////////////////////////////////////////////////////
//
// Function    : select
//
// Description : Tries to select the machine gun weapon as the current weapon. 
//               returns whether or not this is a valid weapon (i.e. do we 
//               have any ammo.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cMachineGunWeapon::select
(
)
{
    if (_quantityAvailable == 0) 
    {
        return (false);
    }

    _cooldown = _cooldownTime;

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : unselect
//
// Description : called when unselecting the machine gun weapon.
//
////////////////////////////////////////////////////////////////////////////////
void
cMachineGunWeapon::unselect
(
)
{
#ifndef NO_SOUND
    if (_gunSound)
    {
        delete _gunSound;
        _gunSound = NULL;
    }
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawGraphic
//
// Description : draw the machine gun icon
//
////////////////////////////////////////////////////////////////////////////////
void
cMachineGunWeapon::drawGraphic
(
    float x
)
{
    drawIcon (x, 2);

    // Draw a bar showing how many rounds we have left.

    glBegin (GL_QUADS);

    glColor3f (1.0f, 1.0f, 1.0f);

    glVertex3f (x + 0.40f, 6.75f, 0.0f);
    glVertex3f (x + 0.40f, 6.95f, 0.0f);
    glVertex3f (x + _quantityAvailable / 50.0f + 0.40f, 6.95f, 0.0f);
    glVertex3f (x + _quantityAvailable / 50.0f + 0.40f, 6.75f, 0.0f);

    glEnd ();
}
