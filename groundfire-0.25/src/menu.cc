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
//   File name : menu.cc
//
//          By : Tom Russell
//
//        Date : 12-Mar-03
//
// Description : Interface class for all the different menus
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"

float cMenu::_backgroundScroll = 0.0f;

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMenu::cMenu 
(
    cGame * game
)
: _game (game)
{    
    // Store pointers to these objects so we don't need to keep fetching them 
    // from the game object.
    _font      = game->getFont ();
    _interface = game->getInterface ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMenu::~cMenu 
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawBackground
//
// Description : Draw the textured background seen on all the menus
//
////////////////////////////////////////////////////////////////////////////////
void 
cMenu::drawBackground
(
    void
)
{
    glEnable (GL_TEXTURE_2D);

    glTexEnvf (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    glDisable(GL_DEPTH_TEST);	

    glLoadIdentity ();

    // This is the current background colour
    glColor3f (0.4f, 0.7f, 0.9f);

    _game->getInterface ()->setTexture (6);

    // To get the background to scroll, we alter the texture coordinates
    glBegin (GL_QUADS);
    glTexCoord2f (_backgroundScroll,         _backgroundScroll); 
    glVertex3f   (-10.0f, -7.5f, 0.0f);
    glTexCoord2f (10.0f + _backgroundScroll, _backgroundScroll);
    glVertex3f   ( 10.0f, -7.5f, 0.0f);
    glTexCoord2f (10.0f + _backgroundScroll, 7.5f + _backgroundScroll); 
    glVertex3f   ( 10.0f,  7.5f, 0.0f);
    glTexCoord2f (_backgroundScroll,         7.5f + _backgroundScroll); 
    glVertex3f   (-10.0f,  7.5f, 0.0f);
    glEnd ();

    glEnable (GL_DEPTH_TEST);

    glDisable (GL_TEXTURE_2D);
}
