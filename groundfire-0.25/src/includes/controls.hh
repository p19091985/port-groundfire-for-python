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
//   File name : controls.hh
//
//          By : Tom Russell
//
//        Date : 21-Jan-04
//
// Description :
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __CONTROLS_HH__
#define __CONTROLS_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "interface.hh"
#include "player.hh"

#define NUM_OF_CONTROLS 11

// Labels for the two types of input device
enum device_t
{
    KEYBOARD_DEVICE,
    JOYSTICK_DEVICE
};

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
// none

struct layout_s
{
    device_t deviceType;
    int      command[NUM_OF_CONTROLS];
};

class cControls
{
public:
    cControls (cInterface * interface);
    ~cControls ();

    bool getCommand (int controller, command_t command);

    // Assigns a layout to a controller
    void setLayout (int controller, int layoutNum)
        {
            _controllerLayout[controller] = layoutNum;
        }

    // Gets the current layout of a controller
    int  getLayout (int controller) 
        {
            return (_controllerLayout[controller]);
        }

    // Sets a control on a layout
    void setControl (int layout, int command, int controlID)
        {
            _layout[layout].command[command] = controlID;
        }

    // Gets a control on a layout
    int getControl (int layout, int command)
        {
            return (_layout[layout].command[command]);
        }

    void resetToDefault (int layout);

private:
    cInterface * _interface;

    int      _controllerLayout[10];
    layout_s _layout[10];
};

#endif // __CONTROLS_HH__
