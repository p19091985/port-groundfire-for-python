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
//   File name : quake.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "quake.hh"
#include "game.hh"
#include "landscape.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cQuake::OPTION_QuakeDuration;
float cQuake::OPTION_QuakeDropRate;
float cQuake::OPTION_TimeTillFirstQuake;
float cQuake::OPTION_TimeBetweenQuakes;
float cQuake::OPTION_ShakeAmplitude;
float cQuake::OPTION_ShakeFrequency;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cQuake
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cQuake::cQuake
(
    cGame * game
)
        : cEntity (game)
{
    _earthquake          = false;
    _earthquakeCountdown = OPTION_TimeTillFirstQuake;

    _x = 0.0f;

#ifndef NOSOUND
    _rumble = NULL;
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cQuake
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cQuake::~cQuake
(
)
{
#ifndef NOSOUND
    if (_rumble)
    {
        delete _rumble;
    }
#endif

    if (_earthquake)
    {
        // recentre the viewport 
        (_game->getInterface ())->offsetViewport (0.0f, 0.0f);    
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the settings for the quake parameters
//
////////////////////////////////////////////////////////////////////////////////
void 
cQuake::readSettings
(
    cReadIniFile const & settings
)
{
    // The number of seconds the quake lasts for
    OPTION_QuakeDuration
        = settings.getFloat ("Quake", "QuakeDuration", 5.0f);

    // How quickly the terrain drops during an earthquake
    OPTION_QuakeDropRate
        = settings.getFloat ("Quake", "QuakeDropRate", 0.2f);

    // The number of seconds before the first earthquake happends
    OPTION_TimeTillFirstQuake
        = settings.getFloat ("Quake", "TimeTillFirstQuake", 90.0f);

    // The number of seconds between consecutive earthquakes
    OPTION_TimeBetweenQuakes
        = settings.getFloat ("Quake", "TimeBetweenQuakes", 30.0f);

    // The ammount by which the screen is shook
    OPTION_ShakeAmplitude
        = settings.getFloat ("Quake", "ShakeAmplitude", 0.05f);

    // The speed of the shaking
    OPTION_ShakeFrequency
        = settings.getFloat ("Quake", "ShakeFrequency", 50.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the earthquake (earthquakes are invisible)
//
////////////////////////////////////////////////////////////////////////////////
void
cQuake::draw
(
    void
)
{
    // do nuttin'
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the earthquake entity
//
////////////////////////////////////////////////////////////////////////////////
bool
cQuake::update
(
    float time
)
{
    _earthquakeCountdown -= time;

    if (_earthquake)
    {
        // The terrain collapses while an earthquake is in process.
        (_game->getLandscape ())->dropTerrain (time * OPTION_QuakeDropRate);

        // Displace the screen by '_x' units in the x-axis. 
        _x = sin ((OPTION_QuakeDuration - _earthquakeCountdown) 
                  * OPTION_ShakeFrequency) * OPTION_ShakeAmplitude;

        (_game->getInterface ())->offsetViewport (_x, 0.0f);

        if (_earthquakeCountdown < 0.0f)
        {
            // Stop the quake and set the countdown until the next quake.
            _earthquake          = false;
            _earthquakeCountdown = OPTION_TimeBetweenQuakes;

            // Reset the viewport displacement
            (_game->getInterface ())->offsetViewport (0.0f, 0.0f);

#ifndef NOSOUND
            // Stop the looping rumble sound by killing its cSoundSource object
            delete _rumble;
            _rumble = NULL;
#endif
        }
    }
    else if (_earthquakeCountdown < 0.0f)
    {
        // Start the quake and set the countdown until the quake ends.
        _earthquake          = true;
        _earthquakeCountdown = OPTION_QuakeDuration;

#ifndef NOSOUND
        // Play the looping earthquake sound
        _rumble = new cSound::cSoundSource (_game->getSound (), 2, true);
#endif
    }

    return (true);
}
