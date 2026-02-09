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
//   File name : controls.cc
//
//          By : Tom Russell
//
//        Date : 21-Jan-04
//
// Description : Handles the mapping between the game's commands and the various
//               input controllers.
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "controls.hh"

// Define the default keymaps for the two keyboard controls and for joysticks.
// These will be used if nothing can be read from the file or if the user
// selects 'Reset to defaults' 
int defaultCommands[3][NUM_OF_CONTROLS] = 
{
    { 32,  79,  85,  73,  75,  74,  76,  65,  68,  87,  83  },
    { 302, 311, 309, 310, 307, 306, 308, 285, 286, 283, 284 },
    { 0,   2,   1,   3,   4,   6,   7,   101, 100, 102, 103 }
};

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cControls
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cControls::cControls
(
    cInterface * interface
)
: _interface (interface)
{
    // The first two layouts are always for the keyboard 
    _layout[0].deviceType = KEYBOARD_DEVICE;
    _layout[1].deviceType = KEYBOARD_DEVICE;

    // Copy in the default control mappings for the two keyboard layouts
    for (int j = 0; j < NUM_OF_CONTROLS; j++)
    {
        _layout[0].command[j] = defaultCommands[0][j];
        _layout[1].command[j] = defaultCommands[1][j];
    }

    // Set the first two controllers to use the keyboard. These are always 
    // available (who doesn't have a keyboard?!)
    _controllerLayout[0] = 0;
    _controllerLayout[1] = 1;

    for (int i = 2; i < 10; i++)
    {
        _layout[i].deviceType = JOYSTICK_DEVICE;
        _controllerLayout[i]  = 2;

        for (int j = 0; j < NUM_OF_CONTROLS; j++)
        {
            _layout[i].command[j] = defaultCommands[2][j];
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cControls
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cControls::~cControls
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getCommand
//
// Description :
//
////////////////////////////////////////////////////////////////////////////////
bool
cControls::getCommand
(
    int       controller,
    command_t command
)
{
    int layout = _controllerLayout[controller];
    
    switch (_layout[layout].deviceType)
    {
    case KEYBOARD_DEVICE:
        return (_interface->getKey (_layout[layout].command[command]));
        
    case JOYSTICK_DEVICE:
        if (_layout[layout].command[command] >= 100)
        {
            int axis      = (_layout[layout].command[command] - 100) / 2;
            int direction = (_layout[layout].command[command] - 100) % 2;
            
            float axisReading = _interface->getJoystickAxis 
                (
                    controller - 2,
                    axis
                );
            
            if ((direction == 0 && axisReading >=  0.5) ||
                (direction == 1 && axisReading <= -0.5))
            {
                return (true);
            }
        }
        else
        {
            return (_interface->getJoystickButton (controller - 2, 
                                             _layout[layout].command[command]));
        }
        break;
    }
    
    return (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : resetToDefault
//
// Description :
//
////////////////////////////////////////////////////////////////////////////////
void
cControls::resetToDefault
(
    int layout
)
{
    int defaults = layout < 2 ? layout : 2;

    for (int i = 0; i < NUM_OF_CONTROLS; i++) 
    {
        _layout[layout].command[i] = defaultCommands[defaults][i];
    }    
}
