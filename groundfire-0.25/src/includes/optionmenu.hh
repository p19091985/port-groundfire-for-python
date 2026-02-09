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
//   File name : optionmenu.hh
//
//          By : Tom Russell
//
//        Date : 02-April-03
//
// Description : Handles the option menu
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __OPTIONMENU_HH__
#define __OPTIONMENU_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "menu.hh"
#include "buttons.hh"
#include "selector.hh"

// Give names to the resolution options  
enum
{
    _640BY480   = 0,
    _800BY600   = 1,
    _1024BY768  = 2,
    _1280BY960  = 3,
    _1280BY1024 = 4,
    _1600BY1200 = 5
};

class cOptionMenu : public cMenu
{ 
public:
    cOptionMenu (cGame * game);
    virtual ~cOptionMenu ();

    enumGameState update (double time);
    void          draw   ();

private:
    cSelector * _resolutions;
    cSelector * _screenMode;

    cTextButton * _defineControls;
    cTextButton * _applyButton;
    cTextButton * _backButton;

};

#endif // __OPTIONMENU_HH__
