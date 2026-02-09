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
//   File name : controlsfile.cc
//
//          By : Tom Russell
//
//        Date : 20-Jan-04
//
// Description : Handles the reading and writing of the file that stores the 
//               current controller mappings.
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <stdlib.h>
#include <cstring>

#include "controlsfile.hh"
#ifdef DEBUG
#include <windows.h>
#endif

// The names of the controls in Groundfire
char *cmdNames[NUM_OF_CONTROLS] = 
{
    "Fire",
    "WeaponUp",
    "WeaponDown",
    "JumpJets",
    "Shield",
    "TankLeft",
    "TankRight",
    "GunLeft",
    "GunRight",
    "GunUp",
    "GunDown"
};

// The names of the layouts
char *layoutNames[10] = 
{
    "Keyboard1",
    "Keyboard2",
    "JoyLayout1",
    "JoyLayout2",
    "JoyLayout3",
    "JoyLayout4",
    "JoyLayout5",
    "JoyLayout6",
    "JoyLayout7",
    "JoyLayout8"
};

// The names of the joysticks (not very imaginative I'm afraid).
char *joysticks[8] =
{
    "Joystick1",
    "Joystick2",
    "Joystick3",
    "Joystick4",
    "Joystick5",
    "Joystick6",
    "Joystick7",
    "Joystick8"
};
  
////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cControlsFile
//
// Description : Contructor
//
////////////////////////////////////////////////////////////////////////////////
cControlsFile::cControlsFile
(
    cControls * controls,
    char      * fileName
)
: _controls (controls)
{
    _fileName = strdup (fileName);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cControlFile
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cControlsFile::~cControlsFile
(
)
{
    free (_fileName);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readFile
//
// Description : Reads the controls file. Returns whether or not it was 
//               successful.
//
////////////////////////////////////////////////////////////////////////////////
bool
cControlsFile::readFile
(
)
{
    _file = fopen (_fileName, "r");

    if (!_file)
    {

#ifdef DEBUG
        OutputDebugString ("Failed to open controls file\n");
#endif

        return (false);
    }

#ifdef DEBUG
    OutputDebugString ("Opened file for reading...\n");
#endif

    skipWhiteSpace ();

    char layout[80];
    
    // read the first section
    if (1 != fscanf (_file, "[ %s ]", layout))
    {
        fclose (_file);
        return (false);
    }

#ifdef DEBUG
    {
        char buffer[80];
        sprintf (buffer, "Reading layout : %s\n", layout);
        OutputDebugString (buffer);
    }
#endif

    // Should be the joystick mapping section
    if (0 != strcmp (layout, "Joysticks"))
    {
        fclose (_file);
        return (false);
    }

    skipWhiteSpace ();

    char first[80];
    int  value;

    // read the joystick mappings
    while (2 == fscanf (_file, "%s = %d", first, &value))
    {
        int layoutMap = -1;
        for (int i = 0; i < 8; i++)
        {
            if (0 == strcmp (first, joysticks[i]))
            {
                layoutMap = i;
                break;
            }
        }
        
        if (layoutMap != -1)
        {

#ifdef DEBUG
            {
                char buffer[80];
                sprintf (buffer, "Set Joy '%s' to layout '%d'\n", first, value);
                OutputDebugString (buffer);
            }
#endif

            // Set this controller to the specified layout
            _controls->setLayout (layoutMap + 2, value + 1);
        }
        else
        {
            fclose (_file);
            return (false);
        }
        
        skipWhiteSpace ();
    }

    // Now read the layouts
    while (1 == fscanf (_file, "%s ]", layout))
    {
        int layoutNum = -1;

        for (int i = 0; i < 10; i++)
        {
            if (0 == strcmp (layoutNames[i], layout))
            {
                layoutNum = i;
                break;
            }
        }
        
#ifdef DEBUG
        {
            char buffer[80];
            sprintf (buffer, "Reading layout %d\n", layoutNum);
            OutputDebugString (buffer);
        }
#endif

        skipWhiteSpace ();

        if (layoutNum != -1)
        {
            if (!readLayout(layoutNum))
            {
                fclose (_file);
                return (false);
            }
        }    
    }

    // All done!

    fclose (_file);
    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : readLayout
//
// Description : read a controller layout from the controls file
//
////////////////////////////////////////////////////////////////////////////////
bool
cControlsFile::readLayout
(
    int layout
)
{
    char first[80];
    int  value;

    while (2 == fscanf (_file, "%s = %d", first, &value))
    {
        int cmd = -1;
        for (int i = 0; i < NUM_OF_CONTROLS; i++)
        {
            if (0 == strcmp (first, cmdNames[i]))
            {
                cmd = i;
                break;
            }
        }
        
        if (cmd != -1)
        {
#ifdef DEBUG
            {
                char buffer[80];
                sprintf (buffer, "setting '%s' to %d\n", first, value);
                OutputDebugString (buffer);
            }   
#endif       

            skipWhiteSpace ();  

            // Set Control
            _controls->setControl (layout, cmd, value);
        }
        else
        {
            return (false);
        }
    }

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : writeFile
//
// Description : Write the controls file
//
////////////////////////////////////////////////////////////////////////////////
bool
cControlsFile::writeFile
(   
)
{
    _file = fopen (_fileName, "w");

    if (!_file)
    {
        return (false);
    }

    fprintf (_file, "[ Joysticks ]\n\n");

    for (int i = 0; i < 8; i++) 
    {
        fprintf (_file, "%s = %d\n",
                 joysticks[i],
                 _controls->getLayout (i + 2) - 1);
    }

    for (int i = 0; i < 10; i++)
    {
     
        fprintf (_file, "\n[ %s ]\n\n", layoutNames[i]);
        
        for (int j = 0; j < NUM_OF_CONTROLS; j++)
        {
            fprintf (_file, "%s = %d\n",
                     cmdNames[j], 
                     _controls->getControl (i, j));
        }
    }

    fclose (_file);

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : skipWhiteSpace
//
// Description : Reads all the whitespaces, positioning the file stream at the 
//               next none-whitespace character.
//
////////////////////////////////////////////////////////////////////////////////
void
cControlsFile::skipWhiteSpace
(
)
{
    for (;;) 
    {    
        char c = fgetc (_file);

        if (c != ' ' && c != '\n' && c != '\t')
        {
            ungetc (c, _file);
            break;
        }

        if (c == EOF) 
        {
            break;
        }
    }
}
