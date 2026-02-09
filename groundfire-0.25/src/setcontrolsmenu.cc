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
//   File name : setcontrolsmenu.cc
//
//          By : Tom Russell
//
//        Date : 14-Dec-03
//
// Description : Handles the set controls menu
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "setcontrolsmenu.hh"
#include "font.hh"

char *controlStrings[NUM_OF_CONTROLS] = { "Fire Weapon",
                                          "Change Weapon Up",
                                          "Change Weapon Down",
                                          "Use Jump Jets",
                                          "Use Shield",
                                          "Move Tank Left",
                                          "Move Tank Right",
                                          "Rotate Gun Left",
                                          "Rotate Gun Right",
                                          "Increase Gun Power",
                                          "Decrease Gun Power" };

// For the joystick Axis, certain command must be used in pairs, for example:
// if joystick left is set to 'move left' then joystick right is automatically
// set to 'move right'. The next table identifys which controls are linked
// together.

char linkedControls[NUM_OF_CONTROLS] = 
{
    -1,  // Fire
    2,   // Change Weapon Up
    1,   // Change Weapon Down
    -1,  // Jump jet
    -1,  // Shield
    6,   // Move left
    5,   // Move Right
    8,   // Rotate Left
    7,   // Rotate Right
    10,  // Increase Power
    9    // Decrease Power
};

// Names of all the special (non-ascii) keys on a normal keyboard. This is so
// we can display which one has been selected.

char *specialKeys[62] = 
{
    "Escape",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
    "F13", "F14", "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23",
    "F24", "F25",
    "Up", "Down", "Left", "Right",
    "Left Shift", "Right Shift", "Left Control", "Right Control",
    "Left Alt", "Right Alt", "Tab", "Enter", "Backspace", "Insert", "Delete",
    "Page Up", "Page Down", "Home", "End", 
    "Keypad 0", "Keypad 1", "Keypad 2", "Keypad 3", "Keypad 4", "Keypad 5",
    "Keypad 6", "Keypad 7", "Keypad 8", "Keypad 9", "Keypad /", "Keypad *",
    "Keypad -", "Keypad +", "Keypad .", "Keypad =", "Keypad Enter"
};

// The (probable) names of the axes.
char *axes[8] = 
{
    "Joystick/Pad Right",
    "Joystick/Pad Left",
    "Joystick/Pad Up",
    "Joystick/Pad Down",
    "Axis 3 (-)",
    "Axis 3 (+)",
    "Axis 4 (-)",
    "Axis 4 (+)"
}; 

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cSetControlsMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cSetControlsMenu::cSetControlsMenu
(
    cGame * game,
    int     layout
)
        : cMenu (game), _layout (layout)
{
    _controls = game->getControls ();

    // Create the buttons to change each control
    for (int i = 0; i < NUM_OF_CONTROLS; i++) 
    {
        _controlButtons[i] = new cTextButton (this, 
                                              -3.0f, 5.0f - i * 0.8f, 0.5f,
                                              controlStrings[i]);    

        _controlKey[i] = _controls->getControl (_layout, i);
    }

    _resetToDefaultsButton = new cTextButton (this, 
                                              0.0f, -5.0f, 0.7f, 
                                              "Reset To Defaults");

    _doneButton            = new cTextButton (this, 
                                              0.0f, -6.0f, 0.7f, 
                                              "Done");

    _waitingForKey = -1;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cSetControlsMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cSetControlsMenu::~cSetControlsMenu
(
)
{
    for (int i = 0; i < NUM_OF_CONTROLS; i++) 
    {
        _controls->setControl (_layout, i, _controlKey[i]);

        delete _controlButtons[i];
    }

    delete _doneButton;
    delete _resetToDefaultsButton;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cSetControlsMenu::update
(
    double time
)
{
    updateBackground (time);


    for (int i = 0; i < NUM_OF_CONTROLS; i++)
    {
        if (_controlButtons[i]->update ())
        {
            // One of the change control buttons has been pressed. We now 
            // switch to 'waiting for input' mode. Disable all other buttons 
            // and listen for a key press/joystick input.
             
            // Mark which control we are changing
            _waitingForKey = i;

            for (int j = 0; j < NUM_OF_CONTROLS; j++) 
            {
                _controlButtons[j]->enable (false);
            }
        }
    }

    // Are we waiting for the user to specify a new key/axis for this control?
    if (_waitingForKey != -1)
    {    
        // If we are changing a keyboard layout, listen for the key press
        if (_layout < 2) 
        {
            // Get Keyboard button
            for (int i = 0; i < 318; i++)
            {
                if (GLFW_PRESS == _interface->getKey(i))
                {
                    _controlKey[_waitingForKey] = i;
                    _waitingForKey = -1;
                    
                    for (int j = 0; j < NUM_OF_CONTROLS; j++) 
                    {
                        _controlButtons[j]->enable (true);
                    }
                    break;
                }
            }
        }
        else
        {
            // We are changing a joystick layout so listen for a button/axis 
            // movement.
            for (int i = 2; i < _interface->numOfControllers (); i++)
            {
                int count;
                const unsigned char* buttons = glfwGetJoystickButtons(i - 2, &count);

                // Check the buttons
                for (int j = 0; j < count && j < 10; j++)
                {
                    if (buttons[j] == GLFW_PRESS)
                    {
                        if (_controlKey[_waitingForKey] >= 100 &&
                            linkedControls[_waitingForKey] != -1)
                        {
                            _controlKey[linkedControls[_waitingForKey]] = -1;    
                        }

                        _controlKey[_waitingForKey] = j;
                        _waitingForKey = -1;

                        for (int k = 0; k < NUM_OF_CONTROLS; k++) 
                        {
                            _controlButtons[k]->enable (true);
                        }
                        break;
                    }                    
                }

                if (_waitingForKey == -1)
                {
                    break;
                }
                
                // Check the axes
                int axisCount;
                const float* axesPtr = glfwGetJoystickAxes(i - 2, &axisCount);

                for (int j = 0; j < axisCount && j < 4; j++)
                {
                    // An axis is considered active if it is over half way in 
                    // a direction. This only applies to analogue axes. Digital
                    // axes can only be -1, 0, or 1
                    if (axesPtr[j] > 0.5)
                    {
                        // Axis controls are identified by numbers starting 
                        // from 100+
                        _controlKey[_waitingForKey] = 100 + (j * 2);
                        if (linkedControls[_waitingForKey] != -1)
                        {
                            _controlKey[linkedControls[_waitingForKey]] 
                                = 101 + (j * 2);    
                        }
                        _waitingForKey = -1;

                        // Re-enable all the other buttons
                        for (int k = 0; k < NUM_OF_CONTROLS; k++) 
                        {
                            _controlButtons[k]->enable (true);
                        }
                        break;
                    }
                    else if (axesPtr[j] < -0.5)
                    {
                        _controlKey[_waitingForKey] = 101 + (j * 2);
                        if (linkedControls[_waitingForKey] != -1)
                        {
                            _controlKey[linkedControls[_waitingForKey]] 
                                = 100 + (j * 2);
                        }
                        _waitingForKey = -1;

                        // Re-enable all the other buttons
                        for (int k = 0; k < NUM_OF_CONTROLS; k++) 
                        {
                            _controlButtons[k]->enable (true);
                        }
                        break;
                    }
                }

                if (_waitingForKey == -1)
                {
                    break;
                }
            }
        }
    }

    if (_doneButton->update ())
    {
        return (CONTROLLERS_MENU);
    }

    if (_resetToDefaultsButton->update ())
    {
        // Restore all keys to their defaults
        _controls->resetToDefault (_layout);

        for (int i = 0; i < NUM_OF_CONTROLS; i++) 
        {   
            _controlKey[i] = _controls->getControl (_layout, i);
        }
    }

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
cSetControlsMenu::draw
(
)

{
    drawBackground ();

    glEnable (GL_BLEND);
  
    // Draw the dark boxes behind the text
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    glBegin (GL_QUADS);

    glVertex3f   (-7.0f, -4.0f, 0.0f);
    glVertex3f   ( 7.0f, -4.0f, 0.0f);
    glVertex3f   ( 7.0f,  6.0f, 0.0f);
    glVertex3f   (-7.0f,  6.0f, 0.0f);

    glVertex3f   (-7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -4.4f, 0.0f);
    glVertex3f   (-7.0f, -4.4f, 0.0f);

    glEnd ();

    // Draw the dark brown boxes
    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    for (int i = 0; i < NUM_OF_CONTROLS; i++)
    {
        glBegin (GL_QUADS);
        
        glVertex3f   (-6.0f, 5.3f - (0.8f * i), 0.0f);
        glVertex3f   ( 0.0f, 5.3f - (0.8f * i), 0.0f);
        glVertex3f   ( 0.0f, 4.6f - (0.8f * i), 0.0f);
        glVertex3f   (-6.0f, 4.6f - (0.8f * i), 0.0f);
        
        glVertex3f   ( 0.1f, 5.3f - (0.8f * i), 0.0f);
        glVertex3f   ( 6.0f, 5.3f - (0.8f * i), 0.0f);
        glVertex3f   ( 6.0f, 4.6f - (0.8f * i), 0.0f);
        glVertex3f   ( 0.1f, 4.6f - (0.8f * i), 0.0f);
        
        glEnd ();    
    } 

    glBegin (GL_QUADS);

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
    
    _font->setSize (0.6f, 0.6f, 0.5f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    if (_layout < 2) 
    {
        _font->printCentredAt (0.0f, 6.5f, "Editing Keyboard Layout %i", 
                               _layout + 1);
    }
    else
    {
        _font->printCentredAt (0.0f, 6.5f, "Editing Joystick Layout %i", 
                               _layout - 1);
    }

    if (_waitingForKey != -1) 
    {
        _font->setSize (0.6f, 0.6f, 0.5f);
        _font->setColour (0.5f, 0.5f, 0.5f);

        _font->printCentredAt (0.0f, -4.0f, 
                               "Press Button for '%s'", 
                               controlStrings[_waitingForKey]);
    }

    _font->setSize (0.5f, 0.5f, 0.4f);
    _font->setColour (0.0f, 1.0f, 1.0f);

    // Print the current controls
    for (int i = 0; i < NUM_OF_CONTROLS; i++)
    {
        if (_layout < 2)
        {
            // Keyboard
            if (_controlKey[i] > 256)
            {
                _font->printCentredAt (3.0f, 4.7f - i * 0.8f, "%s", 
                                       specialKeys[_controlKey[i] - 257]);
            }
            else if (_controlKey[i] > 32)
            {
                _font->printCentredAt (3.0f, 4.7f - i * 0.8f, "'%c'", 
                                       (char)_controlKey[i]);
            }
            else if (_controlKey[i] == 32)
            {
                _font->printCentredAt (3.0f, 4.7f - i * 0.8f, "Space");
            }
        }
        else
        {
            // Joystick
            if (_controlKey[i] == -1) 
            {
                _font->printCentredAt (3.0f, 4.7f - i * 0.8f, "<Undefined>");
            }
            else if (_controlKey[i] < 100)
            {
                // Button
                _font->printCentredAt (3.0f, 4.7f - i * 0.8f, "Joy Button %i", 
                                       _controlKey[i] + 1);
            }
            else
            {
                // Axis
                _font->printCentredAt (3.0f, 4.7f - i * 0.8f,
                                       axes[_controlKey[i] - 100]);
            }
            
        }
    }

    for (int i = 0; i < NUM_OF_CONTROLS; i++)
    {
        _controlButtons[i]->draw ();
    }

    _doneButton->draw ();
    _resetToDefaultsButton->draw ();
}
