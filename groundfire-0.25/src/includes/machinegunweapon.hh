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
//   File name : machinegunweapon.hh
//
//          By : Tom Russell
//
//        Date : 04-Apr-04
//
// Description : Handles the nuclear weapons of a tank
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __MACHINEGUNWEAPON_HH__
#define __MACHINEGUNWEAPON_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "weapon.hh"
#include "sounds.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cMachineGunWeapon : public cWeapon
{
public:
    cMachineGunWeapon (cGame * game, cTank * ownerTank);
    ~cMachineGunWeapon ();

    static void readSettings (cReadIniFile const & settings);

    bool fire (bool starting, float time);
    void update (float time);

    // Can only take 50 Machine gun rounds into a round
    void setAmmoForRound (void) 
        {
            _quantityAvailable = _quantity < 50 ? _quantity : 50;
        }

    bool select      (void);
    void unselect    (void);
    void drawGraphic (float x);

private:
    // Settings Variables
    static float OPTION_CooldownTime;
    static float OPTION_Damage; 
    static float OPTION_Speed;
    static int   OPTION_Cost;

#ifndef NOSOUND
    cSound::cSoundSource * _gunSound;
#endif

};

#endif // __MACHINEGUNWEAPON_HH__
