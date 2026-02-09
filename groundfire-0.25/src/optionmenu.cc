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
//   File name : optionmenu.cc
//
//          By : Tom Russell
//
//        Date : 02-April-03
//
// Description : Handles the option menu
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "optionmenu.hh"
#include "font.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cOptionMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cOptionMenu::cOptionMenu 
(
    cGame * game
)
: cMenu (game)
{
    // Create the resolution selector
    _resolutions = new cSelector (this, 3.0f, 1.0f, 4.0f, 0.6f);

    // Populate the selector with the supported resolution options.
    _resolutions->addOption ("640 x 480");
    _resolutions->addOption ("800 x 600");
    _resolutions->addOption ("1024 x 768");
    _resolutions->addOption ("1280 x 960");
    _resolutions->addOption ("1280 x 1024");
    _resolutions->addOption ("1600 x 1200");

    // Create the window/fullscreen selector
    _screenMode = new cSelector (this, 3.0f, 0.0f, 4.0f, 0.6f);

    _screenMode->addOption ("Fullscreen");
    _screenMode->addOption ("Windowed");

    int width;
    int height;

    if (!_game->getInterface ()->getWindowSettings (width, height))
    {
        // We are currently windowed, so set the selector to this
        _screenMode->setOption (1);
    }

    // Set the resolution selector to be the current width and height of the 
    // window. Use the height to determine this. If we are a none standard 
    // resolution, we will default to 640x480 wide.
    switch (height)
    {
    default:
    case 480:
        _resolutions->setOption (0);
        break;

    case 600:
        _resolutions->setOption (1);
        break;

    case 768:
        _resolutions->setOption (2);
        break;

    case 960:
        _resolutions->setOption (3);
        break;

    case 1024:
        _resolutions->setOption (4);
        break;

    case 1200:
        _resolutions->setOption (5);
        break;
    }

    // Add the rest of the buttons
    _defineControls = new cTextButton (this, 0.0f, -1.0f, 0.6f,
                                       "Set Controls");

    _applyButton = new cTextButton (this, 0.0f, -5.0f, 0.7f, 
                                    "Apply");

    _backButton = new cTextButton (this, 0.0f, -6.0f, 0.7f, 
                                   "Back");
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cOptionMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cOptionMenu::~cOptionMenu 
(
)
{
    delete _resolutions;
    delete _screenMode;

    delete _defineControls;
    delete _applyButton;
    delete _backButton;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cOptionMenu::update
(
    double time
)
{
    updateBackground (time);

    _resolutions->update ();
    _screenMode->update ();

    if (_defineControls->update ())
    {
        return (CONTROLLERS_MENU);
    }

    // The user has clicked the Apply button
    if (_applyButton->update ())
    {
        bool fullscreen = !_screenMode->getOption ();

        // Tell the interface object about the new screen mode.
        switch (_resolutions->getOption ()) 
        {
        case _640BY480:                
            _interface->changeWindow (640, 480, fullscreen);
            break;

        case _800BY600:
            _interface->changeWindow (800, 600, fullscreen);
            break;

        case _1024BY768:
            _interface->changeWindow (1024, 768, fullscreen);
            break;

        case _1280BY960:
            _interface->changeWindow (1280, 960, fullscreen);
            break;

        case _1280BY1024:
            _interface->changeWindow (1280, 1024, fullscreen);
            break;

        case _1600BY1200:
            _interface->changeWindow (1600, 1200, fullscreen);
            break;
        }
    }

    if (_backButton->update ())
    {
        return (MAIN_MENU);
    }

    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the options menu
//
////////////////////////////////////////////////////////////////////////////////
void
cOptionMenu::draw
(
)
{
    drawBackground ();

    glEnable (GL_BLEND);
  
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    glBegin (GL_QUADS);

    // Black boxes
    glVertex3f   (-7.0f, -3.0f, 0.0f);
    glVertex3f   ( 7.0f, -3.0f, 0.0f);
    glVertex3f   ( 7.0f,  3.0f, 0.0f);
    glVertex3f   (-7.0f,  3.0f, 0.0f);

    glVertex3f   (-7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -4.4f, 0.0f);
    glVertex3f   (-7.0f, -4.4f, 0.0f);

    // Brown boxes
    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    glVertex3f   (-4.0f, -5.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.4f, 0.0f);
    glVertex3f   ( 4.0f, -4.6f, 0.0f);
    glVertex3f   (-4.0f, -4.6f, 0.0f);

    glVertex3f   (-4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.6f, 0.0f);
    glVertex3f   (-4.0f, -5.6f, 0.0f);

    glVertex3f   (-6.0f, 0.6f, 0.0f);
    glVertex3f   ( 6.0f, 0.6f, 0.0f);
    glVertex3f   ( 6.0f, 1.4f, 0.0f);
    glVertex3f   (-6.0f, 1.4f, 0.0f);

    glVertex3f   (-6.0f, -0.4f, 0.0f);
    glVertex3f   ( 6.0f, -0.4f, 0.0f);
    glVertex3f   ( 6.0f,  0.4f, 0.0f);
    glVertex3f   (-6.0f,  0.4f, 0.0f);

    glVertex3f   (-6.0f, -1.4f, 0.0f);
    glVertex3f   ( 6.0f, -1.4f, 0.0f);
    glVertex3f   ( 6.0f, -0.6f, 0.0f);
    glVertex3f   (-6.0f, -0.6f, 0.0f);

    glEnd ();

    glDisable (GL_BLEND);

    _font->setSize (0.6f, 0.6f, 0.5f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    _font->printCentredAt (0.0f, 6.5f, "Options");

    _font->setColour (0.0f, 1.0f, 1.0f);
    _font->setSize (0.6f, 0.6f, 0.5f);

    _font->printCentredAt (-3.0f,  0.7f, "Resolution:");
    _font->printCentredAt (-3.0f, -0.3f, "Screen Mode:");

    _resolutions->draw ();
    _screenMode->draw ();

    _defineControls->draw ();
    _applyButton->draw ();
    _backButton->draw ();
}
