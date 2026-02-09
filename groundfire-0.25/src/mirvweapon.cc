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
//   File name : mirvweapon.cc
//
//          By : Tom Russell
//
//        Date : 04-Apr-04
//
// Description : Handles the mirv weapons of a tank
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "mirvweapon.hh"

#include "game.hh"
#include "tank.hh"
#include "mirv.hh"
#include "soundentity.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cMirvWeapon::OPTION_BlastSize;
float cMirvWeapon::OPTION_CooldownTime;
float cMirvWeapon::OPTION_Damage;
int   cMirvWeapon::OPTION_Cost;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMirvWeapon
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMirvWeapon::cMirvWeapon
(
    cGame * game,
    cTank * ownerTank
)
: cWeapon (game, ownerTank)
{
    // We don't start with an mirvs.
    _quantity     = 0;
    _cooldownTime = OPTION_CooldownTime;

    // Set the cost of this weapon in the shop
    _cost         = OPTION_Cost;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMirvWeapon
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMirvWeapon::~cMirvWeapon
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the options file settings regarding mirvs
//
////////////////////////////////////////////////////////////////////////////////
void 
cMirvWeapon::readSettings
(
    cReadIniFile const & settings
)
{
    // The size of the blast created by a mirv.
    OPTION_BlastSize
        = settings.getFloat ("Mirv", "BlastSize", 0.3f);

    // The wait time, before a mirv can be fired and until consecutive mirvs can
    // be fired.
    OPTION_CooldownTime
        = settings.getFloat ("Mirv", "CooldownTime", 6.0f);

    // The damage done to a tank by a direct hit from a mirv.
    OPTION_Damage
        = settings.getFloat ("Mirv", "Damage", 20.0f);

    // The cost of mirvs in the shop
    OPTION_Cost
        = settings.getInt ("Price", "Mirvs", 50);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : fire
//
// Description : Fires a mirv. Return value is whether or not we can fire 
//               another mirv after this one (i.e. have we run out.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cMirvWeapon::fire 
(
    bool  firing,
    float time    // FUTURE : Currently ignored
)
{
    // We can only fire a mirv if the cooldown period has passed.
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
        
        // Create the mirv. 
        cMirv * mirv = new cMirv
            (
                _game, 
                _ownerTank->getPlayer (),
                xInitial,
                yInitial,
                xVelInitial,
                yVelInitial, 
                _game->getTime (),
                OPTION_BlastSize, 
                OPTION_Damage
            );
        
        _game->addEntity (mirv);

        // Play the gun firing sound.
        cSoundEntity * boom = new cSoundEntity
            (
                _game,
                0,
                false
            );
        
        _game->addEntity (boom);  

        // reduce the number of mirvs we're carrying
        _quantity--;
    }

    // if we're all out of mirvs, return false
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
// Description : Updates the mirv weapon
//
////////////////////////////////////////////////////////////////////////////////
void
cMirvWeapon::update
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
// Description : Tries to select the mirv weapon as the current weapon. 
//               returns whether or not this is a valid weapon (i.e. do we 
//               actual have any mirvs.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cMirvWeapon::select
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
// Description : draw the mirv icon
//
////////////////////////////////////////////////////////////////////////////////
void
cMirvWeapon::drawGraphic
(
    float x
)
{
    drawIcon (x, 4);

    // Currently, we don't tell the user how many mirvs they've got during the 
    // round.
}
