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
//   File name : missileweapon.cc
//
//          By : Tom Russell
//
//        Date : 24-May-03
//
// Description : Handles the missile weapon of a tank
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "missileweapon.hh"

#include "game.hh"
#include "tank.hh"
#include "missile.hh"
#include "soundentity.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cMissileWeapon::OPTION_BlastSize;
float cMissileWeapon::OPTION_CooldownTime;
float cMissileWeapon::OPTION_Damage;
int   cMissileWeapon::OPTION_Cost;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMissileWeapon
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMissileWeapon::cMissileWeapon
(
    cGame * game,
    cTank * ownerTank
)
: cWeapon (game, ownerTank)
{
    _cooldownTime = OPTION_CooldownTime;

    // Sorry, nobody starts with missiles, you must earn them :-)
    _quantity = 0;

    // Set the price of this weapon in the shop
    _cost = OPTION_Cost;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMissileWeapon
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMissileWeapon::~cMissileWeapon
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the options file settings regarding missiles
//
////////////////////////////////////////////////////////////////////////////////
void 
cMissileWeapon::readSettings
(
    cReadIniFile const & settings
)
{

    // The blast size of the missiles fired by tanks
    OPTION_BlastSize
        = settings.getFloat ("Missile", "BlastSize", 0.3f);

    // The wait time, before a missile can be fired and until consecutive 
    // missiles can be fired.
    OPTION_CooldownTime
        = settings.getFloat ("Missile", "CooldownTime", 5.0f);

    // The damage done to a tank by a direct hit from a missile.
    OPTION_Damage
        = settings.getFloat ("Missile", "Damage", 40.0f);

    // The cost of Missiles in the shop
    OPTION_Cost
        = settings.getInt ("Price", "Missiles", 50);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : fire
//
// Description : launch a missile! (return value is whether or not we can fire 
//               another missile after this one (i.e. have we run out.))
//
////////////////////////////////////////////////////////////////////////////////
bool
cMissileWeapon::fire 
(
    bool  firing,
    float time    // FUTURE : Currently ignored
)
{
    // We can only fire a missile if the cooldown period has passed.
    if (firing && _cooldown <= 0.0f)
    {
        // Set a new cooldown period
        _cooldown = _cooldownTime;
        
        float xInitial;
        float yInitial;

        // Get the start position and angle of the missile from the owner tank
        _ownerTank->gunLaunchPosition (xInitial, yInitial);
        float angle = _ownerTank->gunLaunchAngle ();
        
        // Create the missile object
        cMissile * missile = new cMissile
            (
                _game, 
                _ownerTank->getPlayer (),
                xInitial,
                yInitial,
                angle,
                OPTION_BlastSize,
                OPTION_Damage
            );
        
        _game->addEntity (missile);

        // Play the 'missile launching' sound
        cSoundEntity * launchSound = new cSoundEntity (_game, 5, false);
        _game->addEntity (launchSound);
        
        // Reduce by one, the number of missiles in our arsenal.
        _quantity--;
        _quantityAvailable--;
    }

    // If we've run out of missiles for this round, return false.
    if (_quantityAvailable == 0)
    {
        return  (false);
    }        
    
    return  (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the missile weapon
//
////////////////////////////////////////////////////////////////////////////////
void
cMissileWeapon::update
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
// Description : Tries to select the missile weapon as the current weapon. 
//               returns whether or not this is a valid weapon (i.e. do we 
//               actual have any missiles.)
//
////////////////////////////////////////////////////////////////////////////////
bool
cMissileWeapon::select
(
)
{    
    if (_quantityAvailable == 0) 
    {
        return (false);
    }

    // You must wait for the missile weapon to charge before you can fire!
    _cooldown = _cooldownTime;

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawGraphic
//
// Description : draw the missile weapon icon
//
////////////////////////////////////////////////////////////////////////////////
void
cMissileWeapon::drawGraphic
(
    float x
)
{
    drawIcon (x, 10);

    glBegin (GL_QUADS);

    glColor3f (1.0f, 1.0f, 1.0f);

    // Draw a small tab for each available missile

    for (int i = 0; i < _quantityAvailable; i++) 
    {
        glVertex3f (x + i * 0.2f + 0.40f, 6.8f, 0.0f);
        glVertex3f (x + i * 0.2f + 0.40f, 6.9f, 0.0f);
        glVertex3f (x + i * 0.2f + 0.55f, 6.9f, 0.0f);
        glVertex3f (x + i * 0.2f + 0.55f, 6.8f, 0.0f);
    }

    glEnd ();
    
}
