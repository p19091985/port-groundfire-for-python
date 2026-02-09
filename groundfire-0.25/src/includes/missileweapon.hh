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
//   File name : missileweapon.hh
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
#ifndef __MISSILEWEAPON_HH__
#define __MISSILEWEAPON_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "weapon.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cMissileWeapon : public cWeapon
{
public:
    cMissileWeapon (cGame * game, cTank * ownerTank);
    ~cMissileWeapon ();

    static void readSettings (cReadIniFile const & settings);

    bool fire (bool starting, float time);

    void update (float time);

    // Can only take 5 missiles into a round
    void setAmmoForRound (void) 
        {
            _quantityAvailable = _quantity < 5 ? _quantity : 5;
        }

    bool select (void);
   
    void drawGraphic (float x);

private:

    // Settings Variables
    static float OPTION_BlastSize;
    static float OPTION_CooldownTime;
    static float OPTION_Damage;
    static int   OPTION_Cost;

};

#endif // __MISSILEWEAPON_HH__
