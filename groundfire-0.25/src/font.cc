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
//   File name : font.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "font.hh"

#include <stdio.h>
#include <stdarg.h>
#include <cstring>

// Currently this is the maximum length of string that can be written in one go.
#define MAX_STRING 256

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cFont
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cFont::cFont
(
    cInterface * interface,
    int          texNum
)
        : _interface (interface),
          _texNum (texNum),
          _colour (1.0, 1.0, 1.0) // Set default colour to white
{
    // Load the font texture.
    if (!interface->loadTexture ("data/fonts.tga", texNum))
    {
        throw eFont ();
    }
    
    // Set the default text settings
    _shadow       = false;
    _proportional = true;
    _orientation  = 0.0f;

    // Populate the 'widths' table for the proportional font 
    // This could probably be read in from an external file instead of
    // hardwiring it here, but this works for now.

    _widths[ 0] =  9; _widths[ 1] =  9; _widths[ 2] = 14; _widths[ 3] = 18;//' '
    _widths[ 4] = 18; _widths[ 5] = 27; _widths[ 6] = 24; _widths[ 7] =  8;//'$'
    _widths[ 8] = 11; _widths[ 9] = 11; _widths[10] = 15; _widths[11] = 18;//'('
    _widths[12] =  9; _widths[13] =  9; _widths[14] =  9; _widths[15] =  8;//','
    _widths[16] = 18; _widths[17] = 18; _widths[18] = 18; _widths[19] = 18;//'0'
    _widths[20] = 18; _widths[21] = 18; _widths[22] = 18; _widths[23] = 18;//'4'
    _widths[24] = 18; _widths[25] = 18; _widths[26] =  9; _widths[27] =  9;//'8'
    _widths[28] = 18; _widths[29] = 18; _widths[30] = 18; _widths[31] = 17;//'<'
    _widths[32] = 20; _widths[33] = 21; _widths[34] = 21; _widths[35] = 21;//'@'
    _widths[36] = 21; _widths[37] = 20; _widths[38] = 18; _widths[39] = 22;//'D'
    _widths[40] = 22; _widths[41] = 11; _widths[42] = 18; _widths[43] = 22;//'H'
    _widths[44] = 18; _widths[45] = 25; _widths[46] = 22; _widths[47] = 22;//'L'
    _widths[48] = 20; _widths[49] = 22; _widths[50] = 21; _widths[51] = 20;//'P'
    _widths[52] = 20; _widths[53] = 22; _widths[54] = 21; _widths[55] = 27;//'T'
    _widths[56] = 21; _widths[57] = 21; _widths[58] = 20; _widths[59] = 11;//'X'
    _widths[60] =  8; _widths[61] = 11; _widths[62] = 18; _widths[63] = 14;//'\'
    _widths[64] =  9; _widths[65] = 18; _widths[66] = 18; _widths[67] = 18;//'`'
    _widths[68] = 18; _widths[69] = 18; _widths[70] = 11; _widths[71] = 18;//'d'
    _widths[72] = 18; _widths[73] =  9; _widths[74] =  9; _widths[75] = 18;//'h'
    _widths[76] =  9; _widths[77] = 27; _widths[78] = 18; _widths[79] = 18;//'l'
    _widths[80] = 18; _widths[81] = 18; _widths[82] = 14; _widths[83] = 17;//'p'
    _widths[84] = 13; _widths[85] = 18; _widths[86] = 17; _widths[87] = 25;//'t'
    _widths[88] = 18; _widths[89] = 17; _widths[90] = 15; _widths[91] = 11;//'x'
    _widths[92] =  8; _widths[93] = 11; _widths[94] = 18; _widths[95] = 17;//'|'
    _widths[96] = 18; _widths[97] = 10; _widths[98] =  8; _widths[99] = 18;
    _widths[100]= 14; _widths[101]= 27; _widths[102]= 18; _widths[103]= 18;
    _widths[104]=  9; _widths[105]= 27; _widths[106]= 20; _widths[107]=  9;
    _widths[108]= 27; _widths[109]= 10; _widths[110]= 20; _widths[111]= 10;
    _widths[112]= 10; _widths[113]=  8; _widths[114]=  8; _widths[115]= 14;
    _widths[116]= 14; _widths[117]= 14; _widths[118]= 14; _widths[119]= 27;
    _widths[120]=  9; _widths[121]= 26; _widths[122]= 17; _widths[123]=  9;
    _widths[124]= 27; _widths[125]= 10; _widths[126]= 15; _widths[127]= 21;

}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cFont
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cFont::~cFont
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : printf
//
// Description : prints a string. Can do formating like the standard printf
//
////////////////////////////////////////////////////////////////////////////////
void 
cFont::printf
(
    float        x,
    float        y,
    const char * format,
    ...
)
{
    va_list args;

    char buffer[MAX_STRING] = {'\0'};

    va_start (args, format);

    // I don't know why the Windows function has a '_' at the front but it does.
#ifdef _WIN32
    _vsnprintf (buffer, MAX_STRING - 1, format, args);
#else
    vsnprintf (buffer, MAX_STRING - 1, format, args);
#endif

    va_end (args);

    // If we're drawing drop shadows, draw it first at a slightly offset 
    // position.
    if (_shadow)
    {
        printString (x - _xSize / 8.0f, y - _ySize / 8.0f, buffer, true);
    }

    // Now draw the actual string.
    printString (x, y, buffer, false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : printString
//
// Description : Does the actual drawing of the string to the screen. This is 
//               called through, printf or PrintCenteredAt, not directly.
//
////////////////////////////////////////////////////////////////////////////////
void 
cFont::printString
(
    float   x,      // Start position of the String
    float   y,      //   "       "     "  "     "
    char  * string, // The string to print
    bool    shadow  // Whether we're drawing the actual string or the shadow
)
{
    glLoadIdentity ();
    
    // setup the matrix for drawing the string.
    glTranslatef (x, y, -7.0f);
    glRotatef (_orientation, 0.0f, 0.0f, 1.0f);
    
    // We need to enable textures and blending but disable depth testing
    // because we always draw to the front.
    glEnable (GL_TEXTURE_2D);
    glEnable (GL_BLEND);
    glDisable(GL_DEPTH_TEST);

    _interface->setTexture (_texNum);

    // If this is the shadow, the colour should be black and slightly 
    // transparent. Otherwise, use the currently set colour.
    if (shadow)
    {
        glColor4f (0.0f, 0.0f, 0.0f, 0.4f);    
    }
    else
    {
        glColor4f (_colour.r, _colour.g, _colour.b, 1.0f);
    }

    glBegin (GL_QUADS);

    float charX = 0.0f;

    // For each character in the string...
    for (unsigned int i = 0; i < strlen (string); i++) 
    {
        // TexX & Y hold the texture coordinates for the character to draw
        float texX = (float)(string[i] % 16) / 16.0f;
        float texY = 1.0f - ((float)((string[i] - 32) / 16) / 16.0f);
        float texWidth;      
        float width;
        
        // Work out the size of the character
        if (_proportional) 
        {
            texY -= 0.5010f;
            texWidth = 0.0625f * 0.8;
            width = _xSize * 0.8; 
        }
        else
        {
            texY -= 0.0010f;
            texWidth = 0.0625f;
            width = _xSize;
        }

        // Draw the Character
        glTexCoord2f (texX,            texY - 0.0625f);
        glVertex3f   (charX,         0.0f,   0.0f);

        glTexCoord2f (texX + texWidth, texY - 0.0625f);
        glVertex3f   (charX + width, 0.0f,   0.0f);

        glTexCoord2f (texX + texWidth, texY);
        glVertex3f   (charX + width, _ySize, 0.0f);

        glTexCoord2f (texX,            texY);
        glVertex3f   (charX,         _ySize, 0.0f);

        // If we are drawing with a proportional font, we need to advance the X
        // position by a variable ammount depending on the character we just
        // drew.
        if (_proportional) 
        {
            charX += (_widths[string[i] - 32] / 24.0f) * _xSpacing;
        }
        else
        {
            charX += _xSpacing;
        }
    }

    glEnd ();

    // Revert to the normal settings.
    glEnable(GL_DEPTH_TEST);
    glDisable (GL_BLEND);
    glDisable (GL_TEXTURE_2D);  
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : printCentredAt
//
// Description : Like printf above, but the coordinates passed in mark the
//               centre of the string not the start. Useful for nicely
//               formatting menus.
//
////////////////////////////////////////////////////////////////////////////////
void
cFont::printCentredAt
(
    float        xCentre,
    float        y,
    const char * format,
    ...
) 
{
    va_list args;

    char buffer[MAX_STRING] = {'\0'};

    va_start (args, format);

#ifdef _WIN32
    _vsnprintf (buffer, MAX_STRING - 1, format, args);
#else
    vsnprintf (buffer, MAX_STRING - 1, format, args);
#endif

    va_end (args);

    // Find the start x coordinate by calculating the length of the string.
    float x = xCentre - (findStringLength (buffer) / 2.0f);

    if (_shadow)
    {
        printString (x - _xSize / 8.0f, y - _ySize / 8.0f, buffer, true);
    }

    printString (x, y, buffer, false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : findStringLength
//
// Description : Returns the length in game units of the string
//
////////////////////////////////////////////////////////////////////////////////
float
cFont::findStringLength
(
    char * string
)
{
    float width = 0.0f;

    if (_proportional) 
    {
        for (unsigned int i = 0 ; i < strlen (string); i++) 
        {
            width += (float)_widths[string[i] - 32];
        }

        width = (width / 24.0f) * _xSpacing;
    }
    else
    {
        width = ((strlen (string) - 1) * _xSpacing + _xSize);
    }

    return (width);
}
