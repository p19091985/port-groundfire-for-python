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
//   File name : selector.hh
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
#ifndef __SELECTOR_HH__
#define __SELECTOR_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <vector>
#include "menu.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eSelectorMenu;

class cSelector
{
public:
    cSelector (cMenu * menu, 
               float x, float y, float width, float size);
    ~cSelector ();

    int  update ();
    void draw   ();

    void addOption (char * option);
    int  getOption () const     { return (_currentOption); }
    void setOption (int option) { _currentOption = option; }
 
    // Alter the colours of the various states of the selector
    void setColours (sColour normalCol, 
                     sColour selectedCol,
                     sColour disabledCol) 
        {
            _normalCol   = normalCol;
            _selectedCol = selectedCol;
            _disabledCol  = disabledCol;
        }

    void enable (bool enable) 
        {
            _disabled = !enable;
        }

    void clearOptions (void);

protected:   
    void drawArrow (float x, float y, bool direction, bool highlighted);

    cMenu * _menu;

    float   _x;
    float   _y;
    float   _width;
    float   _size;
    
    int     _highlighted;
    bool    _disabled;

    sColour _normalCol;
    sColour _selectedCol;
    sColour _disabledCol;

    int            _currentOption;
    vector<char *> _options;

    bool    _pressed; 
};

#endif // __SELECTOR_HH__
