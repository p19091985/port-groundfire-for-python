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
//   File name : weapon.hh
//
//          By : Tom Russell
//
//        Date : 25-Apr-03
//
// Description : Interface class for all the different weapons
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __WEAPON_HH__
#define __WEAPON_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cTank;
    
#include "game.hh"

class cWeapon
{
public:
    cWeapon (cGame * game, 
             cTank * ownerTank);
    virtual ~cWeapon ();

    virtual bool fire (bool starting, float time) = 0;
    virtual void update (float time)              = 0;
    virtual bool select (void)                    = 0;
    virtual void drawGraphic (float x)            = 0;

    // These functions do nothing by default but can be overwritten by certain
    // weapons that wish to use them.
    virtual void setAmmoForRound (void) { /* Do nothing */ }
    virtual void unselect        (void) { /* Do nothing */ }

    bool readyToFire () const { return (_cooldown <= 0.0f); }

    int  getAmmo () const { return (_quantity); }

    // Add to supply
    void addAmount (int amount) { _quantity += amount; }

    int  getCost (void) const { return (_cost); }
    void setCost (int cost)   { _cost = cost; }

protected:
    // Quick function for setting the texture.
    void texture (int textureNumber) 
    {
        _game->getInterface ()->setTexture (textureNumber);
    }

    void drawIcon (float x, int iconNumber);

    cGame * _game;
    cTank * _ownerTank;

    // FUTURE : These two member functions will be used in the future to do 
    //          precise syncronising of shots over a network or demo playback.
    bool    _firing;
    float   _lastShotTime;

    float   _cooldownTime;

    int     _quantity;
    int     _quantityAvailable;
    float   _cooldown;

    int     _cost;
};

#endif // __WEAPON_HH__
