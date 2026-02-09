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
//   File name : blast.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "blast.hh"
#include "game.hh"

////////////////////////////////////////////////////////////////////////////////
// Define Static Member Variables
////////////////////////////////////////////////////////////////////////////////

float cBlast::OPTION_BlastFadeRate;
float cBlast::OPTION_WhiteoutFadeRate;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cBlast
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cBlast::cBlast
(
    cGame * game,
    float x,
    float y,
    float size,
    float fadeAway,
    bool  whiteOut
)
        : cEntity (game),
          _size (size),
          _fadeAway (fadeAway),
          _whiteOut (whiteOut)
{
    _x = x;
    _y = y;

    // If we are whiting out the screen along with the blast, we need to set 
    // the whiteout level to 1.0 (fully white.)
    _whiteOutLevel = 1.0f;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cBlast
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cBlast::~cBlast
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readSettings
//
// Description : Read the user defined parameters from the settings file.
//
////////////////////////////////////////////////////////////////////////////////
void 
cBlast::readSettings
(
    cReadIniFile const & settings
)
{
    OPTION_BlastFadeRate
        = settings.getFloat ("Effects", "BlastFadeRate", 0.1f);

    OPTION_WhiteoutFadeRate
        = settings.getFloat ("Effects", "WhiteoutFadeRate", 0.6f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : draws this entity
//
////////////////////////////////////////////////////////////////////////////////
void
cBlast::draw
(
    void
)
{
    glEnable (GL_TEXTURE_2D);

    glTexEnvf (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    glEnable (GL_BLEND);
    
    // Blasts should always appear in front of everything else. Disabling 
    // depth testing is a quick and easy way of accomplishing this.
    glDisable(GL_DEPTH_TEST);	

    glLoadIdentity ();

    glTranslatef (_x, _y, -7.0f);

    // Set the blast colour. Specifically, specify how faded-out the blast is.
    glColor4f (1.0f, 1.0f, 1.0f, _fadeAway);

    // Select the blast texture.
    texture (0);

    // Make the actual size of the blast, slightly bigger than the size
    // specified. This is to compensate for the faded edges of the blast
    // texture which tend to make the blast look slightly too small for the
    // hole it creates.
    float blastSize = _size * 1.1;

    glBegin (GL_QUADS);
    glTexCoord2f (0.0f, 0.0f); glVertex3f (-blastSize, -blastSize, 0.0f);
    glTexCoord2f (1.0f, 0.0f); glVertex3f ( blastSize, -blastSize, 0.0f);
    glTexCoord2f (1.0f, 1.0f); glVertex3f ( blastSize,  blastSize, 0.0f);
    glTexCoord2f (0.0f, 1.0f); glVertex3f (-blastSize,  blastSize, 0.0f);
    glEnd ();

    glDisable (GL_TEXTURE_2D);

    // Nukes, and potentially other weapons, cause the screen to flash white
    // when they explode. We simulate this by drawing a white rectangle
    // covering the whole screen and quickly fading it from opaque to
    // transparent.
    if (_whiteOut) 
    {    
        glColor4f (1.0f, 1.0f, 1.0f, _whiteOutLevel); 

        glLoadIdentity ();

        glBegin (GL_QUADS);
        glVertex3f (-10.0f, -7.5f, 0.0f);
        glVertex3f ( 10.0f, -7.5f, 0.0f);
        glVertex3f ( 10.0f,  7.5f, 0.0f);
        glVertex3f (-10.0f,  7.5f, 0.0f);
        glEnd ();    
    }

    // Reset the drawing parameters that we altered.
    glEnable(GL_DEPTH_TEST);
    glDisable (GL_BLEND);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update this entity. Returning false means the entity has died.
//
////////////////////////////////////////////////////////////////////////////////
bool
cBlast::update
(
    float time // ammount of time that has expired since last update.
)
{
    // Fade the blast out at the user-defined rate.
    _fadeAway -= time * OPTION_BlastFadeRate;

    if (_whiteOut)
    {
        // Reduce the white out level and disable it when the level goes
        // below zero (totally transparent.)
        
        _whiteOutLevel -= time * OPTION_WhiteoutFadeRate;
        if (_whiteOutLevel < 0.0f)
        {
            _whiteOut = false;
        }
    }

    // Check if the blast has faded to nothing yet.
    if (_fadeAway < 0.0f)
    {
        // delete the blast.
        
        // Note: There is a small bug here. If the whiteout has not finished 
        //       fading out yet, it will be killed along with the blast.
        //       Normally this isn't a problem because the white-out fades out
        //       much quicker than the blast itself. However, if the user
        //       modifies the settings, this problem can occur.

        delete this;
        return (false);
    }

    // Still alive
    return (true);
}
