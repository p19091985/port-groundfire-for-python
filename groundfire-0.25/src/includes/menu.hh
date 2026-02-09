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
//   File name : menu.hh
//
//          By : Tom Russell
//
//        Date : 12-March-03
//
// Description : Interface class for all the different menus
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __MENU_HH__
#define __MENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "game.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eMenu;

#define BACKGROUND_SCROLL_SPEED 0.1

class cMenu
{
    // Make the common menu items friends of menus so they can easily access
    // their object pointer
    friend class cButton;
    friend class cTextButton;
    friend class cGfxButton;
    friend class cSelector;

public:
    cMenu (cGame * game);
    virtual ~cMenu ();

    virtual enumGameState update (double time) = 0;
    virtual void          draw   () = 0;

    // update the scrolling background
    void updateBackground (double time) 
        {
            _backgroundScroll += time * BACKGROUND_SCROLL_SPEED;

            if (_backgroundScroll > 1.0f)
            {
                _backgroundScroll -= 1.0f;
            }
        }

    void drawBackground (void);
    
protected:
    // The backgroundscroll variable is static. This means it keeps its value
    // across menus, thus you don't notice a jump in the background when a new 
    // menu appears. 
    static float _backgroundScroll;

    // Pointers to objects used a lot by all menus 
    cGame      * _game;
    cFont      * _font;
    cInterface * _interface;

};

#endif // __MENU_HH__
