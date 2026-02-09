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
//   File name : buttons.hh
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
#ifndef __BUTTONS_HH__
#define __BUTTONS_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eButton;

class cButton
{
public:
    cButton (cMenu * menu, float x, float y, float size);

    virtual ~cButton ();

    virtual bool update () = 0;
    virtual void draw   () = 0;

    void enable (bool enable) 
        {
            _disabled = !enable;
            _pressed  = false;
        }

protected:   
    cMenu * _menu;
    float   _x;
    float   _y;
    float   _size;

    sColour _normalCol;
    sColour _selectedCol; 
    sColour _disabledCol;
 
    bool    _highlighted;
    bool    _pressed; 
    bool    _disabled;
};

////////////////////////////////////////////////////////////////////////////////

class cTextButton : public cButton
{
public:
   cTextButton (cMenu * menu, float x, float y, float size, char * text);
   ~cTextButton ();
   
   bool update ();
   void draw ();
   
private:
    char    _text[64]; // The text for the button
};

////////////////////////////////////////////////////////////////////////////////

class cGfxButton : public cButton
{
public:
    cGfxButton (cMenu * menu, float x, float y, float size, int texture);
    
    ~cGfxButton ();
    
    bool update ();
    void draw ();
    
private:
    int _texture;
};

#endif // __BUTTONS_HH__
