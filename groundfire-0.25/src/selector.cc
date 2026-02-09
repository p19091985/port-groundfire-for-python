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
//   File name : selector.cc
//
//          By : Tom Russell
//
//        Date : 13-October-03
//
// Description : Handle the selector controls used by the menus
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "selector.hh"
#include "font.hh"
#include <cstring>

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cSelector
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cSelector::cSelector
(
    cMenu * menu, 
    float x,
    float y,
    float width,
    float size
)
        : _menu (menu), _x (x), _y (y), _width (width), _size (size)          
{
    _highlighted   = 0;
    _pressed       = false;
    _currentOption = 0;
    _disabled      = false;

    _normalCol   = sColour (1.0f, 1.0f, 1.0f);
    _selectedCol = sColour (1.0f, 1.0f, 0.0f);
    _disabledCol = sColour (1.0f, 1.0f, 1.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cSelector
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cSelector::~cSelector
(
)
{    
    clearOptions ();
    
    for (unsigned int i = 0; i < _options.size(); i++)
    {
        free (_options[i]);
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : addOption
//
// Description : Adds a new option to the selector
//
////////////////////////////////////////////////////////////////////////////////
void
cSelector::addOption
(
    char * option
)
{
    _options.push_back (strdup (option));
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draws the selector
//
////////////////////////////////////////////////////////////////////////////////
void
cSelector::draw
(
)
{
    // Draw the two arrow buttons either side of the current selection
    drawArrow (_x - _width / 2.0f, _y, true,  _highlighted == 1);
    drawArrow (_x + _width / 2.0f, _y, false, _highlighted == 2);

    if (!_disabled)
    {
        _menu->_font->setShadow (true);
        _menu->_font->setColour (_normalCol.r, _normalCol.g, _normalCol.b);
        _menu->_font->setSize (_size, _size, _size - 0.1f);
    
        _menu->_font->printCentredAt (_x, _y - _size / 2.0f, 
                                      _options[_currentOption]);
        _menu->_font->setShadow (false);
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawArrow
//
// Description : Draws on e of the arrow buttons
//
////////////////////////////////////////////////////////////////////////////////
void
cSelector::drawArrow
(
    float x,
    float y,
    bool  direction,
    bool  highlighted
)
{
    glLoadIdentity ();

    if (_disabled)
    {
        glColor4f (_disabledCol.r, _disabledCol.g, _disabledCol.b, 0.1f);
    }
    else if (highlighted)
    {
        glColor3f (_selectedCol.r, _selectedCol.g, _selectedCol.b);
    }
    else
    {
        glColor3f (_normalCol.r, _normalCol.g, _normalCol.b);
    }
    
    glEnable (GL_BLEND);

    if (direction)
    {
        // Left Arrow
        glBegin (GL_TRIANGLES);
        glVertex3f (x - _size, y, 0.0f);
        glVertex3f (x,         y + _size / 2.0f, 0.0f);
        glVertex3f (x,         y - _size / 2.0f, 0.0f);
        glEnd ();
    }
    else
    {
        // Right Arrow
        glBegin (GL_TRIANGLES);
        glVertex3f (x + _size, y, 0.0f);
        glVertex3f (x,         y + _size / 2.0f, 0.0f);
        glVertex3f (x,         y - _size / 2.0f, 0.0f);
        glEnd ();
    }

    glDisable (GL_BLEND);

}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the selector
//
////////////////////////////////////////////////////////////////////////////////
int
cSelector::update
(
    void
)

{
    float x, y;
    
    if (!_disabled)
    {
        _menu->_interface->getMousePos (x, y);
        
        _highlighted = 0;
        
        if (_y + _size / 2.0f > y && _y - _size / 2.0f < y) 
        {
            if ((_x - _width / 2.0f) - _size < x && 
                (_x - _width / 2.0f)         > x)
            {
                // Mouse is hovering over left button, so highlight it!
                _highlighted = 1;
                
                if (_menu->_interface->getMouseButton (GLFW_MOUSE_BUTTON_LEFT)) 
                {
                    _pressed = true;
                } 
                else if (_pressed)
                {
                    _currentOption--;
                    if (_currentOption == -1) 
                    {
                        _currentOption = _options.size () - 1;
                    }
                    _pressed = false;
                    return (-1); // decrementing
                }
            }
            else if ((_x + _width / 2.0f)         < x && 
                     (_x + _width / 2.0f) + _size > x)
            {
                // Mouse is hovering over right button, so highlight it!
                _highlighted = 2;
                
                if (_menu->_interface->getMouseButton (GLFW_MOUSE_BUTTON_LEFT)) 
                {
                    _pressed = true;
                } 
                else if (_pressed)
                {
                    _currentOption++;
                    if (_currentOption == (int)_options.size()) 
                    {
                        _currentOption = 0;
                    }
                    _pressed = false;
                    return (1); // incrementing!
                }
            }
            else 
            {
                _pressed = false;
            }
        }
        else
        {
            _pressed = false;
        }
    }

    return (0);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : clearOptions
//
// Description : Flushs all the stored options
//
////////////////////////////////////////////////////////////////////////////////
void 
cSelector::clearOptions
(
    void
)

{
    _currentOption = 0;

    for (unsigned int i = 0; i < _options.size(); i++)
    {
        free (_options[i]);
    }    

    _options.clear ();
}
