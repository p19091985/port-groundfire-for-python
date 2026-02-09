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
//   File name : shellweapon.cc
//
//          By : Tom Russell
//
//        Date : 28-Apr-03
//
// Description : Handles the standard weapon 
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "shellweapon.hh"

#include "game.hh"
#include "tank.hh"
#include "shell.hh"
#include "soundentity.hh"
#include "player.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cShellWeapon::OPTION_BlastSize;
float cShellWeapon::OPTION_CooldownTime;
float cShellWeapon::OPTION_Damage;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cShellWeapon
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cShellWeapon::cShellWeapon
(
    cGame * game,
    cTank * ownerTank
)
: cWeapon (game, ownerTank)
{
    _cooldownTime = OPTION_CooldownTime;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cShellWeapon
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cShellWeapon::~cShellWeapon
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the options file settings regarding Shells
//
////////////////////////////////////////////////////////////////////////////////
void 
cShellWeapon::readSettings
(
    cReadIniFile const & settings
)
{

    // The blast size created by exploding shells
    OPTION_BlastSize
        = settings.getFloat ("Shell", "BlastSize", 0.3f);

    // Minimum time between launching shells
    OPTION_CooldownTime
        = settings.getFloat ("Shell", "CooldownTime", 5.0f);

    // The amount of damage caused by a direct hit from a shell
    OPTION_Damage
        = settings.getFloat ("Shell", "Damage", 40.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : fire
//
// Description : Fires the shell weapon
//
////////////////////////////////////////////////////////////////////////////////
bool
cShellWeapon::fire 
(
    bool  firing,
    float time    // FUTURE : Currently ignored
)
{
    if (firing && _cooldown <= 0.0f)
    {
        _cooldown = _cooldownTime;
        
        float xInitial;
        float yInitial;
        float xVelInitial;
        float yVelInitial;

        // Get the launch angle and speed from the owner tank
        _ownerTank->gunLaunchPosition (xInitial, yInitial);
        _ownerTank->gunLaunchVelocity (xVelInitial, yVelInitial);
        
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
                false
            );
        _game->addEntity (shell);  

        // Play the gun firing sound
        cSoundEntity * boom = new cSoundEntity
            (
                _game,
                0,
                false
            );
        
        _game->addEntity (boom);

        _ownerTank->getPlayer ()->recordFired ();
    }

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the shell weapon
//
////////////////////////////////////////////////////////////////////////////////
void
cShellWeapon::update
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
// Description : Selects the shell weapon
//
////////////////////////////////////////////////////////////////////////////////
bool
cShellWeapon::select
(
)
{
    _cooldown = _cooldownTime;

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawGraphic
//
// Description : Draw the shell weapon icon for the tank
//
////////////////////////////////////////////////////////////////////////////////
void
cShellWeapon::drawGraphic
(
    float x
)
{
    drawIcon (x, 0);
}
