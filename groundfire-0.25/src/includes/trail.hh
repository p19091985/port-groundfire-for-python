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
//   File name : trail.hh
//
//          By : Tom Russell
//
//        Date : 24-Nov-02
//
// Description : Handles the shell/missile etc.. cloud trails
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __TRAIL_HH__
#define __TRAIL_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <list>
#include "entity.hh"

#define LAYDISTANCESQUARED 0.04

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

class cTrail : public cEntity
{
public:
    cTrail (cGame * game, float x, float y);
    ~cTrail ();

    static void readSettings (cReadIniFile const & settings);

    void draw        (void);
    bool update      (float time);
    void layTrail    (float x, float y);
    void setInactive () { _active = false; } // Stop laying more trail

private:
    struct sSegment 
    {
        float x;
        float y;
        float fadeAway;
        float angle;
        float length;
    };

    // Settings Variables
    static float OPTION_TrailFadeRate;

    // Member Variables
    list<sSegment *> _trailSegmentList;
    float            _lastX;
    float            _lastY;
    bool             _active;
};

#endif // __TRAIL_HH__
