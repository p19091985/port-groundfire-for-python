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
//   File name : controllermenu.cc
//
//          By : Tom Russell
//
//        Date : 09-Nov-03
//
// Description : Handles the controller configuration menu accessible from the
//               options menu.
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "controllermenu.hh"
#include "font.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cControllerMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cControllerMenu::cControllerMenu 
(
    cGame * game
)
: cMenu (game)
{

    // Grab a pointer to the controls object because we'll be using this a
    // lot.
    _controls = game->getControls ();

    // Add the buttons for redefining the keyboard.
    _keyboard[0] = new cTextButton (this, 2.0f, 4.6f, 0.5f, "Edit Layout");
    _keyboard[1] = new cTextButton (this, 2.0f, 3.8f, 0.5f, "Edit Layout");

    // Now add the buttons for the joysticks
    for (int i = 0; i < _interface->numOfControllers () - 2; i++) 
    {
        // Create a selector for the different joystick layout options
        _joystick[i].layout = new cSelector (this, 0.0f, 1.1f - (i * 0.8f),
                                               3.3f, 0.5f);
        
        // Create a button for Editing the joystick layout
        _joystick[i].define = new cTextButton (this, 
                                               4.5f, 1.1f - (i * 0.8f), 0.5f,
                                               "Edit Layout");

        // Add the layout options for the joysticks
        _joystick[i].layout->addOption ("Layout 1");
        _joystick[i].layout->addOption ("Layout 2");
        _joystick[i].layout->addOption ("Layout 3");
        _joystick[i].layout->addOption ("Layout 4");
        _joystick[i].layout->addOption ("Layout 5");
        _joystick[i].layout->addOption ("Layout 6");
        _joystick[i].layout->addOption ("Layout 7");
        _joystick[i].layout->addOption ("Layout 8");

        // Set the layout selector to the current layout for this joystick.
        _joystick[i].layout->setOption (_controls->getLayout (i + 2) - 2);
    }

    _backButton = new cTextButton (this, 0.0f, -6.0f, 0.7f, "Back");
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cControllerMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cControllerMenu::~cControllerMenu 
(
)
{
    delete _backButton;

    delete _keyboard[0];
    delete _keyboard[1];

    for (int i = 0; i < _interface->numOfControllers () - 2; i++)
    {
        _controls->setLayout (i + 2, _joystick[i].layout->getOption () + 2);

        delete _joystick[i].layout;
        delete _joystick[i].define;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the menu. Returns the game state to change to (or 
//               CURRENT_STATE for no change.) 
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cControllerMenu::update
(
    double time // elapsed time since last update
)
{
    updateBackground (time);

    for (int i = 0; i < 2; i++)
    {
        // Check if either of the keyboard layout buttons have been clicked and
        // go to the set controls menu if they have.
        if (_keyboard[i]->update ())
        {
            // Tell the game object which controller we will be editing
            _game->setActiveController (i);

            return (SET_CONTROLS_MENU);
        }
    }
    
    for (int i = 0; i < _interface->numOfControllers () - 2; i++)
    {
        // Update the layout selector.
        _joystick[i].layout->update ();
        
        // Check if a joystick layout button has been clicked and go to the 
        // set controls menu if so.
        if (_joystick[i].define->update ())
        {
            // Which joystick layout are we editing?
            int layout = _joystick[i].layout->getOption ();
           
            // Tell the game object which controller we will be editing
            _game->setActiveController (layout + 2);

            return (SET_CONTROLS_MENU);
        }
    }

    if (_backButton->update ())
    {
        // Write out a new controls file with any of the changed layout
        // options.
        _game->getControlsFile ()->writeFile ();

        return (OPTION_MENU);
    }

    // No change of menu.
    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the menu
//
////////////////////////////////////////////////////////////////////////////////
void
cControllerMenu::draw
(
)

{
    drawBackground ();

    glEnable (GL_BLEND);
  
    // Draw the boxes
    
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    glBegin (GL_QUADS);

    glVertex3f   (-7.0f,  3.2f, 0.0f);
    glVertex3f   ( 7.0f,  3.2f, 0.0f);
    glVertex3f   ( 7.0f,  6.0f, 0.0f);
    glVertex3f   (-7.0f,  6.0f, 0.0f);

    glVertex3f   (-7.0f, -5.2f, 0.0f);
    glVertex3f   ( 7.0f, -5.2f, 0.0f);
    glVertex3f   ( 7.0f,  2.8f, 0.0f);
    glVertex3f   (-7.0f,  2.8f, 0.0f);

    glVertex3f   (-7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -5.4f, 0.0f);
    glVertex3f   (-7.0f, -5.4f, 0.0f);

    glEnd ();

    // Draw the brown boxes under the buttons
    
    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    glBegin (GL_QUADS);

    glVertex3f   (-4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.6f, 0.0f);
    glVertex3f   (-4.0f, -5.6f, 0.0f);

    glVertex3f   (-6.4f, 3.4f, 0.0f);
    glVertex3f   ( 6.4f, 3.4f, 0.0f);
    glVertex3f   ( 6.4f, 4.1f, 0.0f);
    glVertex3f   (-6.4f, 4.1f, 0.0f);

    glVertex3f   (-6.4f, 4.2f, 0.0f);
    glVertex3f   ( 6.4f, 4.2f, 0.0f);
    glVertex3f   ( 6.4f, 4.9f, 0.0f);
    glVertex3f   (-6.4f, 4.9f, 0.0f);

    for (int i = 0; i < 8; i++) 
    {
        glVertex3f   (-6.4f, 0.75f - (i * 0.8f), 0.0f);
        glVertex3f   ( 6.4f, 0.75f - (i * 0.8f), 0.0f);
        glVertex3f   ( 6.4f, 1.45f - (i * 0.8f), 0.0f);
        glVertex3f   (-6.4f, 1.45f - (i * 0.8f), 0.0f);    
    }

    glEnd ();

    glDisable (GL_BLEND);

    // Draw the menu title
    
    _font->setSize (0.6f, 0.6f, 0.5f);
    _font->setColour (1.0f, 1.0f, 1.0f);
    _font->setShadow (true);

    _font->printCentredAt (0.0f, 6.5f, "Set Controls");
    
    _font->setShadow (false);
    _font->setSize (0.4f, 0.4f, 0.3f);
    _font->setColour (0.5f, 0.5f, 0.5f);

    // Write out some of the other text that appears in the menu
    _font->printCentredAt (0.0f, 2.2f, "Joystick");
    _font->printCentredAt (0.0f, 1.8f, "layout number");

    _font->printCentredAt (4.5f, 2.2f, "Change");
    _font->printCentredAt (4.5f, 1.8f, "joystick layout");

    _font->printCentredAt (2.0f, 5.4f, "Change");
    _font->printCentredAt (2.0f, 5.0f, "keyboard layout");

    _font->setSize (0.6f, 0.6f, 0.5f);
    _font->setColour (0.0f, 1.0f, 1.0f);
    _font->printCentredAt (-2.0f, 4.3f, "Keyboard 1");
    _font->printCentredAt (-2.0f, 3.5f, "Keyboard 2");

    // For joysticks that are not connected, write out a message in its place
    _font->setColour (0.5f, 0.5f, 0.5f);
    for (int i = _interface->numOfControllers () - 2; i < 8; i++) 
    {
        _font->printCentredAt (-4.6f, 0.8f - i * 0.8f, "Joystick %d", i + 1);
        _font->printCentredAt ( 2.0f, 0.8f - i * 0.8f, "<<Not Connected>>");
    }

    // Draw the keyboard layout buttons
    _keyboard[0]->draw ();
    _keyboard[1]->draw ();
    
    // Draw the connected joystick buttons/selectors
    for (int i = 0; i < _interface->numOfControllers () - 2; i++)
    {
        _font->setSize (0.6f, 0.6f, 0.5f);
        _font->setColour (0.0f, 1.0f, 1.0f);
        _font->printCentredAt (-4.6f, 0.8f - i * 0.8f, "Joystick %d", i + 1);
        
        _joystick[i].layout->draw ();
        _joystick[i].define->draw ();
    }

    _backButton->draw ();
}
