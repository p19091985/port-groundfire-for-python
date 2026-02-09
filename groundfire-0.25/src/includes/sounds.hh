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
//   File name : sounds.hh
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
#ifndef __SOUNDS_HH__
#define __SOUNDS_HH__

#ifndef NOSOUND

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <AL/alut.h>
#include <AL/al.h>

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eSound {};

class cSound
{
public:
    cSound (int numOfSounds);
    ~cSound ();

    void loadSound (int bufferNum, char * fileName);

    class cSoundSource
    {
    public:
        cSoundSource (cSound * sound, int soundToPlay, bool looping);
        ~cSoundSource ();

        bool isSourcePlaying ();

    private:
        ALuint _soundSource;

#ifdef CHECKMEMORY
        static int soundSourcesCount;
#endif
    };

    friend class cSoundSource;

private:
    int      _numOfSounds;
    ALuint * _buffers;
};

#endif // NOSOUND

#endif // __SOUNDS_HH__
