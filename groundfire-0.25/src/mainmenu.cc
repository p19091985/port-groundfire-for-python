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
//   File name : mainmenu.cc
//
//          By : Tom Russell
//
//        Date : 19-Mar-03
//
// Description : Handles the title screen menu.
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "mainmenu.hh"
#include "font.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cMainMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cMainMenu::cMainMenu 
(
    cGame * game
)
: cMenu (game)
{
    _startButton = new cTextButton (this, 0.0f, -4.0f, 0.7f, 
                                    "Start Game");

    _optionsButton = new cTextButton (this, 0.0f, -5.0f, 0.7f, 
                                      "Options");

    _quitButton = new cTextButton (this, 0.0f, -6.0f, 0.7f, 
                                   "Quit");   
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cMainMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cMainMenu::~cMainMenu 
(
)
{
    delete _startButton;
    delete _optionsButton;
    delete _quitButton;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : update the menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cMainMenu::update
(
    double time
)
{
    updateBackground (time);
    
    // Each button leads to a different menu
    
    if (_startButton->update ())
    {
        return (SELECT_PLAYERS_MENU);    
    }

    if (_optionsButton->update ())
    {
        return (OPTION_MENU);
    }

    if (_quitButton->update ())
    {
        return (QUIT_MENU);
    }

    // nothing was pressed.
    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : draw the menu
//
////////////////////////////////////////////////////////////////////////////////
void
cMainMenu::draw
(
)
{
    drawBackground ();

    glEnable (GL_BLEND);
    
    // Draw the Groundfire logo in the centre of the screen
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

    // Draw the menu box around the buttons
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    glBegin (GL_QUADS);

    glVertex3f   (-7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -3.4f, 0.0f);
    glVertex3f   (-7.0f, -3.4f, 0.0f);

    // Draw the button backgrounds
    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    glVertex3f   (-4.0f, -4.4f, 0.0f);
    glVertex3f   ( 4.0f, -4.4f, 0.0f);
    glVertex3f   ( 4.0f, -3.6f, 0.0f);
    glVertex3f   (-4.0f, -3.6f, 0.0f);

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

    // Add the other text that appears on the menu
    _font->setSize (0.4f, 0.4f, 0.35f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    _font->setShadow (true);
    _font->printCentredAt (0.0f, -0.0f, VERSION);
    _font->printCentredAt (0.0f, -0.5f, "www.groundfire.net");
    _font->printCentredAt (0.0f, -2.5f, "Copyright Tom Russell 2004");
    _font->printCentredAt (0.0f, -2.9f, "All Rights Reserved");
    _font->setShadow (false);

    // Draw the buttons
    _startButton->draw ();
    _optionsButton->draw ();
    _quitButton->draw ();
}
