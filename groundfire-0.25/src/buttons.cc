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
//   File name : buttons.cc
//
//          By : Tom Russell
//
//        Date : 25-September-03
//
// Description : Handles the menu buttons (i.e. the clickable text in the menus)
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "buttons.hh"
#include "font.hh"
#include <cstring>

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cButton
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cButton::cButton 
(
    cMenu * menu, 
    float x,
    float y,
    float size
)
        : _menu (menu), _x (x), _y (y), _size (size)
{
    _highlighted = false;
    _pressed     = false;
    _disabled    = false;

    // The colours for the buttons various states are currently hard-wired in.
    // This might be changed in the future.
    _normalCol   = sColour (1.0f, 1.0f, 1.0f); // White
    _selectedCol = sColour (1.0f, 1.0f, 0.0f); // Yellow
    _disabledCol = sColour (0.1f, 0.1f, 0.1f); // Grey/Black
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cButton
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cButton::~cButton
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cTextButton
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cTextButton::cTextButton
(
    cMenu * menu, 
    float x,
    float y,
    float size,
    char * text
)
        : cButton (menu, x, y, size)
{
    strcpy (_text, text);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cTextButton
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cTextButton::~cTextButton
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the button
//
////////////////////////////////////////////////////////////////////////////////
void
cTextButton::draw
(
)
{
    // Set the colour to use for the button depending on its current state: 
    // disabled, highlighted or normal.
    if (_disabled) 
    {
        _menu->_font->setColour (_disabledCol.r,
                                 _disabledCol.g,
                                 _disabledCol.b);
    }
    else if (_highlighted) 
    {
        _menu->_font->setColour (_selectedCol.r,
                                 _selectedCol.g,
                                 _selectedCol.b);
    }
    else
    {
        _menu->_font->setColour (_normalCol.r,
                                 _normalCol.g,
                                 _normalCol.b);
    }

    // To make the buttons stand out more, give a drop-shadow to non-disabled 
    // buttons
    if (!_disabled)
    {
        _menu->_font->setShadow (true);
    }
    
    _menu->_font->setSize (_size, _size, _size - 0.1f);
    _menu->_font->printCentredAt (_x, _y - _size / 2.0f, _text);
    _menu->_font->setShadow (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : update the button. Returns whether the buttons has been
//               clicked by the user.
//
////////////////////////////////////////////////////////////////////////////////
bool
cTextButton::update
(
)
{
    // Disabled buttons are static so we don't need to update them
    if (!_disabled)
    {
        float x, y;
        
        _menu->_interface->getMousePos (x, y);
        
        _highlighted = false;
        
        // Is the mouse currently hovering over the button?
        if (_y + _size / 2.0f > y && _y - _size / 2.0f < y) 
        {
            // We need to find the length of the string so we can tell if the 
            // mouse is over it. We need to tell it how big the font is first.
            _menu->_font->setSize (_size, _size, _size - 0.1f);
            
            float length = _menu->_font->findStringLength (_text);
            
            if (_x + (length / 2.0f) > x && _x - (length / 2.0f) < x)
            {
                // Mouse is hovering over button, so highlight it!
                _highlighted = true;
                
                // Is the mouse button being pressed?
                if (_menu->_interface->getMouseButton (GLFW_MOUSE_BUTTON_LEFT)) 
                {
                    // Note: We don't return true yet, instead we note that 
                    //       the button has been pressed and wait for the user
                    //       to stop pressing the button. This is so that we 
                    //       don't load a new menu and instantly press another
                    //       button that might appear below the mouse cursor!
                    _pressed = true;
                } 
                else if (_pressed)
                {                    
                    // The pressed flag is set and the mouse button is not 
                    // held down. This means the user has just lifted their 
                    // finger. NOW we return true to tell the caller that the 
                    // button has been pressed..
                    return (true);
                }
            }
            else
            {
                // If we're not over the button anymore, reset the 'pressed'
                // flag. This prevents the button being triggered if the user 
                // clicks and holds over a button and then moves the mouse 
                // miles away and releases the mouse button.
                _pressed = false;
            }
        }
        else
        {
            // see the above comment.
            _pressed = false;
        }
    }
    
    // The button wasn't selected this time.
    return (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cGfxButton
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////

cGfxButton::cGfxButton
(
    cMenu * menu,
    float   x,
    float   y,
    float   size,
    int     texture
)
   : cButton (menu, x, y, size), 
     _texture (texture)
{
    _disabledCol = sColour (1.0f, 1.0f, 1.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cGfxButton
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cGfxButton::~cGfxButton
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : update the button. Returns whether the buttons has been
//               clicked by the user.
//
////////////////////////////////////////////////////////////////////////////////
bool
cGfxButton::update
(
)
{
    // Disabled buttons are static so we don't need to update them
    if (!_disabled)
    {
        float x, y;
        
        _menu->_interface->getMousePos (x, y);
        
        _highlighted = false;
        
        float halfSize = _size / 2;

        // Is the mouse currently hovering over the button?
        if (   _y + halfSize > y && _y - halfSize < y 
            && _x + halfSize > x && _x - halfSize < x) 
        {
            // Mouse is hovering over button, so highlight it!
            _highlighted = true;
                
            // Is the mouse button being pressed?
            if (_menu->_interface->getMouseButton (GLFW_MOUSE_BUTTON_LEFT)) 
            {
                // Note: We don't return true yet, instead we note that 
                //       the button has been pressed and wait for the user
                //       to stop pressing the button. This is so that we 
                //       don't load a new menu and instantly press another
                //       button that might appear below the mouse cursor!
                _pressed = true;
            } 
            else if (_pressed)
            {                    
                // The pressed flag is set and the mouse button is not 
                // held down. This means the user has just lifted their 
                // finger. NOW we return true to tell the caller that the 
                // button has been pressed..
                return (true);
            }
        }
        else
        {
            // If we're not over the button anymore, reset the 'pressed'
            // flag. This prevents the button being triggered if the user 
            // clicks and holds over a button and then moves the mouse 
            // miles away and releases the mouse button.
            _pressed = false;
        }
    }
    
    // The button wasn't selected this time.
    return (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the graphics button
//
////////////////////////////////////////////////////////////////////////////////
void
cGfxButton::draw
(
)
{
    glLoadIdentity ();

    // Set the colour to use for the button depending on its current state: 
    // disabled, highlighted or normal.
    if (_disabled) 
    {
        glColor4f (_disabledCol.r, _disabledCol.g, _disabledCol.b, 0.2f);
    }
    else if (_highlighted) 
    {
        glColor4f (_selectedCol.r, _selectedCol.g, _selectedCol.b, 1.0f);
    }
    else
    {
        glColor4f (_normalCol.r, _normalCol.g, _normalCol.b, 1.0f);
    }

    glEnable (GL_TEXTURE_2D);
    glEnable (GL_BLEND);
    glDisable(GL_DEPTH_TEST);

    _menu->_interface->setTexture (_texture);

    float halfSize = _size / 2.0f;

    glBegin (GL_QUADS);

    glTexCoord2f (0.0f, 0.0f);
    glVertex3f   (_x - halfSize, _y - halfSize, 0.0f);
    
    glTexCoord2f (0.0f, 1.0f);
    glVertex3f   (_x - halfSize, _y + halfSize, 0.0f);

    glTexCoord2f (1.0f, 1.0f);
    glVertex3f   (_x + halfSize, _y + halfSize, 0.0f);
    
    glTexCoord2f (1.0f, 0.0f);
    glVertex3f   (_x + halfSize, _y - halfSize, 0.0f);
    
    glEnd ();

    // Revert to the normal settings.
    glEnable(GL_DEPTH_TEST);
    glDisable (GL_BLEND);
    glDisable (GL_TEXTURE_2D); 
}
