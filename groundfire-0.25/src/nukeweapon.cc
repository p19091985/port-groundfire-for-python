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
//   File name : nukeweapon.cc
//
//          By : Tom Russell
//
//        Date : 28-Apr-03
//
// Description : Handles the nuclear weapons of a tank
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "nukeweapon.hh"

#include "game.hh"
#include "tank.hh"
#include "shell.hh"
#include "soundentity.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cNukeWeapon::OPTION_BlastSize;
float cNukeWeapon::OPTION_CooldownTime;
float cNukeWeapon::OPTION_Damage;
int   cNukeWeapon::OPTION_Cost;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cNukeWeapon
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cNukeWeapon::cNukeWeapon
(
    cGame * game,
    cTank * ownerTank
)
: cWeapon (game, ownerTank)
{
    // We don't start with an nukes.
    _quantity     = 0;
    _cooldownTime = OPTION_CooldownTime;

    // Set the cost of this weapon in the shop
    _cost         = OPTION_Cost;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cNukeWeapon
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cNukeWeapon::~cNukeWeapon
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the options file settings regarding nukes
//
////////////////////////////////////////////////////////////////////////////////
void 
cNukeWeapon::readSettings
(
    cReadIniFile const & settings
)
{
    // The size of the blast created by a nuke.
    OPTION_BlastSize
        = settings.getFloat ("Nuke", "BlastSize", 3.0f);

    // The wait time, before a nuke can be fired and until consecutive nukes can
    // be fired.
    OPTION_CooldownTime
        = settings.getFloat ("Nuke", "CooldownTime", 10.0f);

    // The damage done to a tank by a direct hit from a nuke.
    OPTION_Damage
        = settings.getFloat ("Nuke", "Damage", 90.0f);

    // The cost of nukes in the shop
    OPTION_Cost
        = settings.getInt ("Price", "Nukes", 50);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : fire
//
// Description : Fires a nuke. Return value is whether or not we can fire 
//               another nuke after this one (i.e. have we run out.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cNukeWeapon::fire 
(
    bool  firing,
    float time    // FUTURE : Currently ignored
)
{
    // We can only fire a nuke if the cooldown period has passed.
    if (firing && _cooldown <= 0.0f)
    {
        _cooldown = _cooldownTime;
        
        float xInitial;
        float yInitial;
        float xVelInitial;
        float yVelInitial;

        // Get the launch position and velocity for the nuke from the owner tank
        _ownerTank->gunLaunchPosition (xInitial, yInitial);
        _ownerTank->gunLaunchVelocity (xVelInitial, yVelInitial);
        
        // Create the nuke. Nukes are effectively just bigger shells so are 
        // handled by the same code.
        cShell * shell = new cShell 
            (
                _game, 
                _ownerTank->getPlayer (),
                xInitial,
                yInitial,
                xVelInitial,
                yVelInitial, 
                _game->getTime (),
                OPTION_BlastSize, 
                OPTION_Damage,
                true
            );
        
        _game->addEntity (shell);

        // Play the gun firing sound.
        cSoundEntity * boom = new cSoundEntity
            (
                _game,
                0,
                false
            );
        
        _game->addEntity (boom);  

        // reduce the number of nukes we're carrying
        _quantity--;
    }
    
    // if we're all out of nukes, return false
    if (_quantity == 0)
    {
        return (false);
    }

    return  (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the nuke weapon
//
////////////////////////////////////////////////////////////////////////////////
void
cNukeWeapon::update
(
    float time
)
{
    if (_cooldown > 0.0f)
    {
        _cooldown -= time;
    }
}


////////////////////////////////////////////////////////////////////////////////
//
// Function    : select
//
// Description : Tries to select the nuke weapon as the current weapon. 
//               returns whether or not this is a valid weapon (i.e. do we 
//               actual have any nukes.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cNukeWeapon::select
(
)
{
    if (_quantity == 0) 
    {
        return (false);
    }

    _cooldown = _cooldownTime;

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawGraphic
//
// Description : draw the nuke icon
//
////////////////////////////////////////////////////////////////////////////////
void
cNukeWeapon::drawGraphic
(
    float x
)
{
    drawIcon (x, 1);

    // Currently, we don't tell the user how many nukes they've got during the 
    // round.
}
