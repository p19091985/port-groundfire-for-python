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
//   File name : sounds.cc
//
//          By : Tom Russell
//
//        Date : 19-Feb-04
//
// Description : Handles the sound interface (openAL)
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef NOSOUND

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "sounds.hh"
#include "report.hh"

#ifdef CHECKMEMORY 
#include <windows.h>
#include <stdio.h>
#endif

// The source position and velocity and currently static. It might be possible 
// to create some effects later by manipulating these.
ALfloat sourcePos[] = { 0.0, 0.0, 0.0 };
ALfloat sourceVel[] = { 0.0, 0.0, 0.0 };

#ifdef CHECKMEMORY 
int cSound::cSoundSource::soundSourcesCount = 0;
#endif

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cSound
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cSound::cSound
(
    int numOfSounds
)
        : _numOfSounds (numOfSounds), _buffers (0)
{
    alutInit (0, 0);
    alGetError();

    // Create a sound buffer for each of the sounds in the game.
    _buffers = new ALuint[numOfSounds];

    alGenBuffers (numOfSounds, _buffers);

    // Did that work?
    if (alGetError () != AL_NO_ERROR)
    {
        report ("ERROR: Could not initialise sound");

        delete[] _buffers;
        throw eSound ();
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cSound
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cSound::~cSound
(
)
{
    if (_buffers)
    {
        alDeleteBuffers (_numOfSounds, _buffers);

        delete[] _buffers;
    }

    alutExit ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : loadSound
//
// Description : loads the specified sound file into the specified buffer
//
////////////////////////////////////////////////////////////////////////////////
void
cSound::loadSound
(
    int    bufferNum,
    char * fileName
)
{
    ALenum      format;
    ALsizei     size = 0;
    ALvoid    * data;
    ALsizei     freq;
    ALboolean   loop;

    alutLoadWAVFile ((ALbyte *)fileName, 
                     &format, &data, &size, &freq, &loop);

    if (size <= 0)
    {
        // The wav file did not load
        debug ("WARNING: Could not load sound file : '%s'", fileName);
    }

    alBufferData    (_buffers[bufferNum], format, data, size, freq);
    alutUnloadWAV   (format, data, size, freq);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cSoundSource
//
// Description : Constructor for soundsources
//
////////////////////////////////////////////////////////////////////////////////

cSound::cSoundSource::cSoundSource
(
    cSound * sound,
    int      soundToPlay,
    bool     looping
)
{
    alGenSources (1, &_soundSource);

    // Setup all the source parameters, these are mostly fixed. Only the buffer
    // and whether its a looping sound can currently be set.
    alSourcei  (_soundSource, AL_BUFFER,   sound->_buffers[soundToPlay]);
    alSourcef  (_soundSource, AL_PITCH,    1.0f                        );
    alSourcef  (_soundSource, AL_GAIN,     1.0f                        );
    alSourcefv (_soundSource, AL_POSITION, sourcePos                   );
    alSourcefv (_soundSource, AL_VELOCITY, sourceVel                   );
    alSourcei  (_soundSource, AL_LOOPING,  looping                     );

    // Start it playing!
    alSourcePlay (_soundSource);

#ifdef CHECKMEMORY
    soundSourcesCount++;

    {
        char buf[128];
        
        sprintf (buf, "cSoundSource (%d exist)\n", soundSourcesCount);
        
        OutputDebugString (buf);
    }
#endif
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cSoundSource
//
// Description : Destructor for sound sources
//
////////////////////////////////////////////////////////////////////////////////

cSound::cSoundSource::~cSoundSource
(
)
{
#ifdef CHECKMEMORY
    soundSourcesCount--;

    {
        char buf[128];
        
        sprintf (buf, "~cSoundSource (%d remaining)\n", soundSourcesCount);
        
        OutputDebugString (buf);
    }
#endif

    // Stop the source playing
    alSourceStop (_soundSource);

    alDeleteSources (1, &_soundSource);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : isSourcePlaying
//
// Description : Returns whether the source is still playing or not
//
////////////////////////////////////////////////////////////////////////////////
bool
cSound::cSoundSource::isSourcePlaying
(
)
{
    ALint value;
    
    alGetSourcei (_soundSource, AL_SOURCE_STATE, &value);
    
    return (AL_PLAYING == value);
}

#endif // NOSOUND
