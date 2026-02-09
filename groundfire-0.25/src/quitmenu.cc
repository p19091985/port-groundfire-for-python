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
//   File name : quitmenu.cc
//
//          By : Tom Russell
//
//        Date : 31-Mar-03
//
// Description : Handles the quit menu
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "quitmenu.hh"
#include "font.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cQuitMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cQuitMenu::cQuitMenu 
(
    cGame * game
)
: cMenu (game)
{
    _yes = new cTextButton (this, 0.0f, -5.0f, 0.7f, 
                            "Yes");

    _no = new cTextButton (this, 0.0f, -6.0f, 0.7f, 
                           "No");
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cQuitMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cQuitMenu::~cQuitMenu 
(
)
{
    delete _yes;
    delete _no;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cQuitMenu::update
(
    double time
)
{
    updateBackground (time);

    if (_yes->update ())
    {
        return (EXITED);
    }

    if (_no->update ()) 
    {
        return (MAIN_MENU);
    }

    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draws the menu
//
////////////////////////////////////////////////////////////////////////////////
void
cQuitMenu::draw
(
)
{
    drawBackground ();

    glEnable (GL_BLEND);

    // Draw the Groundfire logo
    glEnable (GL_TEXTURE_2D);

    (_game->getInterface())->setTexture (9);

    glColor4f (1.0f, 1.0f, 1.0f, 1.0f);

    glBegin (GL_QUADS);

    glTexCoord2f (0.0f, 0.0f); glVertex3f ( -8.0f, 0.0f, 0.0f);
    glTexCoord2f (1.0f, 0.0f); glVertex3f (  8.0f, 0.0f, 0.0f);
    glTexCoord2f (1.0f, 1.0f); glVertex3f (  8.0f, 4.0f, 0.0f);
    glTexCoord2f (0.0f, 1.0f); glVertex3f ( -8.0f, 4.0f, 0.0f);

    glEnd ();

    glDisable (GL_TEXTURE_2D);

    // draw the menu background box
    glBegin (GL_QUADS);

    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    glVertex3f   (-7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -3.4f, 0.0f);
    glVertex3f   (-7.0f, -3.4f, 0.0f);

    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    glVertex3f   (-4.0f, -5.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.4f, 0.0f);
    glVertex3f   ( 4.0f, -4.6f, 0.0f);
    glVertex3f   (-4.0f, -4.6f, 0.0f);

    glVertex3f   (-4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.6f, 0.0f);
    glVertex3f   (-4.0f, -5.6f, 0.0f);

    glEnd ();

    glDisable (GL_BLEND);

    _font->setSize   (0.7f, 0.7f, 0.6f);
            
    _font->setColour (1.0f, 1.0f, 1.0f);
    _font->printCentredAt (0.0f, -4.35f, "Are you sure?");

    _yes->draw ();
    _no->draw ();
}
