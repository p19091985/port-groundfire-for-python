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
//   File name : quake.hh
//
//          By : Tom Russell
//
//        Date : 24-Feb-04
//
// Description : Handles the earthquakes that happen each round.
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __QUAKE_HH__
#define __QUAKE_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"
#include "sounds.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cQuake : public cEntity
{
public:
    cQuake (cGame * game);
    ~cQuake ();

    void draw (void);
    bool update (float time);

    static void readSettings (cReadIniFile const & settings);

private:
    // Settings Variables
    static float OPTION_QuakeDuration;
    static float OPTION_QuakeDropRate;
    static float OPTION_TimeTillFirstQuake;
    static float OPTION_TimeBetweenQuakes;
    static float OPTION_ShakeAmplitude;
    static float OPTION_ShakeFrequency;

    // Member Variables
    bool  _earthquake;          // Is an earthquake happening?
    float _earthquakeCountdown; // Time till next quake or end of quake.

#ifndef NOSOUND
    cSound::cSoundSource * _rumble;
#endif
};

#endif // __QUAKE_HH__
