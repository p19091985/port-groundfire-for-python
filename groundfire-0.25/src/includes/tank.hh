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
//   File name : tank.hh
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
#ifndef __TANK_HH__
#define __TANK_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"
#include "sounds.hh"

#define MAX_WEAPONS               5

// Name the states that the tank can be in
enum enumTankState { TANK_ALIVE, TANK_DEAD, TANK_RESIGNED };

// Names of weapons
enum enumWeapons { SHELLS, MACHINEGUN, MIRVS, MISSILES, NUKES };

class cWeapon;
class cPlayer;

class cTank : public cEntity
{
    // These class need to access the tank variables a lot so make them friends
    friend class cShopMenu;
    friend class cAIPlayer;
    friend class cGame;

public:
    cTank (cGame * game, cPlayer * owner, int statsPosition);
    ~cTank ();

    void draw (void);
    bool update (float time);

    // Sets a colour for the tank
    void setColour (const sColour & colour) 
        {
            _colour = colour;
        }

    // Get the colour of the tank
    void getColour (float &r, float &g, float &b) const
        {
            r = _colour.r;
            g = _colour.g;
            b = _colour.b;
        }

    // Get the player associated with this tank.
    cPlayer * getPlayer ()
    {
        return (_player);
    }
   
    void  setPositionOnGround (float x );

    //bool  pointInTank (float x, float y);

    bool  intersectTank (float x1, float y1, float x2, float y2) const;

    float getCentre (float & x, float & y);

    bool  doDamage (float damage);

    void  doPreRound  ();
    bool  doPostRound ();

    bool  isFiring () const { return (_firing); }
    
    bool  readyToFire () const;

    bool  alive () const { return (_state == TANK_ALIVE); }

    void  gunLaunchPosition (float &x, float &y);

    void  gunLaunchVelocity (float &xVel, float &yVel);

    float gunLaunchAngle () const { return (_gunAngle); }

    void  gunLaunchVelocityAtPower (float &xVel, float &yVel, float power);

private:

    void moveTank  (float time, bool boost);
    void updateGun (float time);
    void burn      (float time);

    // Constants
    float _gunAngleMax;
    float _gunAngleMaxChangeSpeed;
    float _gunAngleChangeAcceleration;
    float _gunPowerMax;
    float _gunPowerMin;
    float _gunPowerMaxChangeSpeed;
    float _gunPowerChangeAcceleration;

    float _movementSpeed;
    
    float _tankSize;                  // Size of the tank
    float _tankGravity;               // Strength of gravity in Free fall
    float _tankBoost;                 // Power of jumpjets
    float _groundSmokeReleaseTime;    // Smoke cloud creation rate on ground
    float _airSmokeReleaseTime;       // Smoke cloud creation rate while in air
    float _fuelUsageRate;             // Rate at which jumpjets burn fuel

    float _exhaustTime;               // Time between exhaust clouds being 
                                      // Released while using jumpjets.

    int   _statsPosition;             // X position of the stats for this tank

    float _maxHealth;                 // Health of an undamaged tank (100)

    
    // Variables

    cPlayer * _player;                // The object that controls this tank

    // Variables to control the gun position and power
    float _gunAngle;                  
    float _gunAngleChangeSpeed;
    float _gunPower;
    float _gunPowerChangeSpeed;

    // Timer before another weapon switch is allowed
    float _switchWeaponTime;

    float _tankAngle;         // The angle of the tank (0 = flat)

    // velocity for an airbourne tank
    float _airbourneXvel;
    float _airbourneYvel;

    // Are we on the ground?
    bool  _onGround;

    // The tank's (player's) colour
    sColour _colour;

    // Current amount of health
    float _health;

    // The currently selected weapon.
    int _selectedWeapon;

    // Is the tank using jumpjets?
    bool _boosting;

    // Is the tank firing?
    bool _firing;

#ifndef NOSOUND
    cSound::cSoundSource * _boostingSound;
#endif

    // 'fuel' is the amount of fuel available this round, 'total fuel' is all 
    // the fuel we have purchased.
    float _fuel;
    float _totalFuel;
   
    // Tank's state (Alive/Dead/etc...)
    enumTankState _state;

    // The Weapon objects owned by this tank.
    cWeapon * _weapon[MAX_WEAPONS];
};

#endif // __TANK_HH__
