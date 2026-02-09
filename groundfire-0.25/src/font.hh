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
//   File name : font.hh
//
//          By : Tom Russell
//
//        Date : 08-Dec-02
//
// Description : Handles the texture font which is used to draw all the writing
//               in Groundfire.
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __FONT_HH__
#define __FONT_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "interface.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eFont {};

class cFont
{
public:
    cFont (cInterface * interface, int texNum);
    ~cFont ();

    // Set the size of the font and the spacing between characters
    void  setSize (float xSize, float ySize, float xSpacing) 
        {
            _xSize    = xSize;
            _ySize    = ySize;
            _xSpacing = xSpacing;
        }

    // Set the current text colout
    void  setColour (float r, float g, float b) 
        {
            _colour.r = r;
            _colour.g = g;
            _colour.b = b;
        }

    void  printf (float x, float y, const char * format, ...);

    void  printCentredAt (float xCentre, float y, const char * format, ...); 

    // Enable/Disable certain text properties
    void  setProportional (bool proportional) { _proportional = proportional; }
    void  setShadow       (bool shadow)       { _shadow = shadow; }

    // Set the angle to draw the text at
    void  setOrientation  (float orientation) { _orientation = orientation; }

    float findStringLength (char * string);

private:
    void  printString (float x, float y, char * string, bool shadow);

    cInterface * _interface;
    int          _texNum;

    float        _xSize;
    float        _ySize;
    float        _xSpacing;
    bool         _proportional;
    bool         _shadow;
    float        _orientation;

    sColour      _colour;

    // The array of character widths for the proportional font.
    char          _widths[128];

};

#endif // __FONT_HH__
