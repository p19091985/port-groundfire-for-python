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
//   File name : trail.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <math.h>

#include "trail.hh"
#include "game.hh"
#include "common.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cTrail::OPTION_TrailFadeRate;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cTrail
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cTrail::cTrail
(
    cGame * game,
    float startX,
    float startY
)
        : cEntity (game)
{
    _lastX = startX;
    _lastY = startY;

    // Trails start active (i.e. new bits of trail are still being laid)
    _active = true;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cTrail
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cTrail::~cTrail
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the ini file options for trails
//
////////////////////////////////////////////////////////////////////////////////
void 
cTrail::readSettings
(
    cReadIniFile const & settings
)
{
    // Controls how quickly the trails fade away
    OPTION_TrailFadeRate
        = settings.getFloat ("Effects", "TrailFadeRate", 0.2f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the trails
//
////////////////////////////////////////////////////////////////////////////////
void
cTrail::draw
(
    void
)
{  
    glEnable (GL_TEXTURE_2D);
    glEnable (GL_BLEND);

    glTexEnvf (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    glDisable(GL_DEPTH_TEST);	

    texture (1);

    list<sSegment *>::iterator iterator;

    // Draw each trail segment
    for (iterator  = _trailSegmentList.begin ();
         iterator != _trailSegmentList.end ();
         iterator++)
    {    
        glLoadIdentity (); 

        glTranslatef ((*iterator)->x, (*iterator)->y, -6.0f);
        glColor4f (1.0f, 1.0f, 1.0f, (*iterator)->fadeAway);

        glRotatef ((*iterator)->angle, 0.0f, 0.0f, 1.0f);
        
        glBegin (GL_QUADS);

        glTexCoord2f (0.0f, 0.0f); 
        glVertex3f (-0.1f, -0.2f - (*iterator)->length, 0.0f);

        glTexCoord2f (1.0f, 0.0f); 
        glVertex3f ( 0.1f, -0.2f - (*iterator)->length, 0.0f);

        glTexCoord2f (1.0f, 1.0f); 
        glVertex3f ( 0.1f,  0.2f, 0.0f);

        glTexCoord2f (0.0f, 1.0f); 
        glVertex3f (-0.1f,  0.2f, 0.0f);

        glEnd ();
    }

    glEnable  (GL_DEPTH_TEST);
    glDisable (GL_BLEND);
    glDisable (GL_TEXTURE_2D);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the trail. This consists of fading each trail segment.
//
////////////////////////////////////////////////////////////////////////////////
bool
cTrail::update
(
    float time
)
{
    list<sSegment *>::iterator iterator;

    // Fade each segment
    for (iterator  = _trailSegmentList.begin ();
         iterator != _trailSegmentList.end ();)
    {
        (*iterator)->fadeAway -= OPTION_TrailFadeRate * time;

        if((*iterator)->fadeAway < 0.0f) 
        {
            delete (*iterator);
            iterator = _trailSegmentList.erase (iterator);
        }
        else
        {
            iterator++;
        }
    }

    if (!_active && _trailSegmentList.empty ()) 
    {
        // No more trail segemnts. Delete the trail object.
        delete this;
        return (false);
    }

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : layTrail
//
// Description : Lay a new trail segment
//
////////////////////////////////////////////////////////////////////////////////
void
cTrail::layTrail
(
    float x,
    float y
)
{
    float xDiff = x - _lastX;
    float yDiff = y - _lastY;
    float distanceSquared = sqr (xDiff) + sqr (yDiff);

    // New trail is only put down once we have moved a certain distance from 
    // where the last piece of trail was placed. This algorithm could be
    // slightly improved because when a shell is fired at an almost vertical
    // angle, it leaves a bizzare angular bend at it highest point. 

    // A better way might be laying a new trail after a certain change in angle
    // has occured in the object doing the laying.

    while (distanceSquared > LAYDISTANCESQUARED)
    {
        _lastX += xDiff * (0.2 / sqrt(distanceSquared));
        _lastY += yDiff * (0.2 / sqrt(distanceSquared));

        // Create the new segment
        sSegment * newSeg = new sSegment;

        newSeg->x        = _lastX;
        newSeg->y        = _lastY;
        newSeg->fadeAway = 0.8f;
        newSeg->length   = 0.2f;
        if (xDiff > 0.0f)
        {
            newSeg->angle = 
                -acos (yDiff / sqrt(distanceSquared)) * (180.0f / PI);
        }
        else if (xDiff < 0.0f)
        {
            newSeg->angle = 
                acos (yDiff / sqrt(distanceSquared)) * (180.0f / PI);
        }
        else
        {
            newSeg->angle = 0.0f;
        }
        
        // Shove it on the list
        _trailSegmentList.push_back (newSeg);

        xDiff = x - _lastX;
        yDiff = y - _lastY;
        distanceSquared = sqr (xDiff) + sqr (yDiff);
    }  
}
