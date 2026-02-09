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
//   File name : weapon.cc
//
//          By : Tom Russell
//
//        Date : 25-Apr-03
//
// Description : Interface class for all the different weapons
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "weapon.hh"

#include "tank.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cWeapon
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cWeapon::cWeapon
(
    cGame * game, 
    cTank * ownerTank
)
        : _game      (game),
          _ownerTank (ownerTank)
{
    _cost = 0;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cWeapon
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cWeapon::~cWeapon
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawIcon
//
// Description : Draw an icon for the currently selected weapon
//
////////////////////////////////////////////////////////////////////////////////
void
cWeapon::drawIcon
(
    float x,         // The x position to place the icon.
    int   iconNumber // The icon number (used to select it from the texture)
)
{
    int row    = iconNumber / 4;
    int column = iconNumber % 4;

    glEnable    (GL_TEXTURE_2D);
    glEnable    (GL_BLEND);
    glBlendFunc (GL_SRC_ALPHA, GL_ONE);

    texture (7);
    
    glColor4f (1.0f, 1.0f, 1.0f, 1.0f);
    
    glBegin (GL_QUADS);

    glTexCoord2f (column * 0.25f,         1.00f - (row * 0.25f));
    glVertex3f (x,         7.0f, 0.0f);

    glTexCoord2f (column * 0.25f,         0.75f - (row * 0.25f));
    glVertex3f (x,         6.7f, 0.0f);

    glTexCoord2f (column * 0.25f + 0.25f, 0.75f - (row * 0.25f));
    glVertex3f (x + 0.3f,  6.7f, 0.0f);

    glTexCoord2f (column * 0.25f + 0.25f, 1.00f - (row * 0.25f));
    glVertex3f (x + 0.3f,  7.0f, 0.0f);
    glEnd ();

    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glDisable   (GL_BLEND);
    glDisable   (GL_TEXTURE_2D);
}
