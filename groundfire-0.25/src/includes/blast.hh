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
//   File name : blast.hh
//
//          By : Tom Russell
//
//        Date : 23-Nov-02
//
// Description : Handles the blast entities. The blasts entities are the
//               fuzzy circles that get drawn when a shell/missile/nuke/etc...
//               explodes.
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __BLAST_HH__
#define __BLAST_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "entity.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cBlast : public cEntity
{
public:
    cBlast  (cGame * game, float x, float y, float size, 
             float fadeAway, bool  whiteOut);
    ~cBlast ();

    static void readSettings (cReadIniFile const & settings);

    void draw (void);
    bool update (float time);

private:
    // Settings Variables

    // The rate at which the blast graphics fade from white to transparent
    // in fade ammount per second.
    static float OPTION_BlastFadeRate;
    // The rate at which the screen whiteout fades away. 
    static float OPTION_WhiteoutFadeRate;

    // Member Variables
    float _size;          // The size of the blast
    float _fadeAway;      // The fade ammount of the blast
    bool  _whiteOut;      // Whether a white out is currently occurring
    float _whiteOutLevel; // The fade ammount of the screen white out
};

#endif // __BLAST_HH__
