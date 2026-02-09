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
//   File name : playermenu.cc
//
//          By : Tom Russell
//
//        Date : 26-May-03
//
// Description : Handles the player selection menu
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "playermenu.hh"
#include "tank.hh"
#include "controls.hh"
#include "font.hh"
#include "inifile.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cPlayerMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cPlayerMenu::cPlayerMenu 
(
    cGame * game
)
: cMenu (game)
{
    getPlayerColoursAndNames ();

    // Create the number of rounds selector and populate it with the possible 
    // options.
    _numberOfRounds = new cSelector (this, 2.0f, -4.0f, 2.0f, 0.7f);

    _numberOfRounds->addOption ("5");
    _numberOfRounds->addOption ("10");
    _numberOfRounds->addOption ("15");
    _numberOfRounds->addOption ("20");
    _numberOfRounds->addOption ("25");
    _numberOfRounds->addOption ("30");
    _numberOfRounds->addOption ("35");
    _numberOfRounds->addOption ("40");
    _numberOfRounds->addOption ("45");
    _numberOfRounds->addOption ("50");

    _startButton = new cTextButton (this, 0.0f, -5.0f, 0.7f, "Start!");
    _backButton  = new cTextButton (this, 0.0f, -6.0f, 0.7f, "Back");

    // Create the temporary player array
    for (int i = 0; i < 8; i++) 
    {
        // Set all players non-enabled as default.
        _player[i].enabled = false;

        _player[i].addButton    
            = new cGfxButton (this, -8.5f, 3.5f - i * 0.8f, 0.6f, 10);
   
        _player[i].removeButton 
            = new cGfxButton (this, -7.8f, 3.5f - i * 0.8f, 0.6f, 11);

        // All players start disabled so turn off this button
        _player[i].removeButton->enable (false);

        _player[i].humanAISelector 
            = new cSelector (this, 1.6f, 3.5f - i * 0.8f, 3.0f, 0.5f);

        // Populate with the options
        _player[i].humanAISelector->addOption ("Human");
        _player[i].humanAISelector->addOption ("Computer");

        _player[i].humanAISelector->enable (false);

        _player[i].controller 
            = new cSelector (this, 6.4f, 3.5f - i * 0.8f, 3.2f, 0.5f);

        // Populate with all possible controller options
        _player[i].controller->addOption ("Keyboard1");
        _player[i].controller->addOption ("Keyboard2");
        _player[i].controller->addOption ("Joystick1");
        _player[i].controller->addOption ("Joystick2");
        _player[i].controller->addOption ("Joystick3");
        _player[i].controller->addOption ("Joystick4");
        _player[i].controller->addOption ("Joystick5");
        _player[i].controller->addOption ("Joystick6");
        _player[i].controller->addOption ("Joystick7");
        _player[i].controller->addOption ("Joystick8");

        _player[i].controller->enable (false);
    }

    // Keep track of how many players have been enabled.
    _playersJoined = 0;

    _startButton->enable (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cPlayerMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cPlayerMenu::~cPlayerMenu
(
)
{
    delete _numberOfRounds;
    delete _startButton;
    delete _backButton;

    // Remove the players' controls
    for (int i = 0; i < 8; i++) 
    {
        delete _player[i].addButton;
        delete _player[i].removeButton;
        delete _player[i].humanAISelector;
        delete _player[i].controller;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cPlayerMenu::update
(
    double time
)
{
    updateBackground (time);
    
    _numberOfRounds->update ();

    if (_startButton->update ())
    {
        addPlayers ();

        // We're starting the game! Set the number of rounds
        int rounds = (1 + _numberOfRounds->getOption ()) * 5;

        _game->setNumOfRounds (rounds);

        return (ROUND_STARTING);
    }

    if (_backButton->update ()) 
    {
        // Change of mind, go back to the title screen
        return (MAIN_MENU);
    }

    // Update the controls for each playerin turn.
    for (int i = 0 ; i < 8; i++)
    {
        if (_player[i].addButton->update ())
        {
            // This player has been added
            _player[i].enabled = true;

            _player[i].addButton->enable       (false);
            _player[i].removeButton->enable    (true);
            _player[i].humanAISelector->enable (true);

            if (_player[i].humanAISelector->getOption () == 0)
            {
                // only enable the controller selector if we have 'human' 
                // selected
                _player[i].controller->enable (true);

                // Check that the controller is not in use, and move to an 
                // available one if it is.
                selectAvailableController (i, 1);
            }

            _playersJoined++;

            // Once 2 or more players have joined, we can allow the
            // game to start by enabling the start button.
            if (_playersJoined > 1) 
            {
                _startButton->enable (true);
            }
        }

        if (_player[i].removeButton->update ())
        {    
            // This player has been removed
            _player[i].enabled = false;

            _player[i].addButton->enable       (true);
            _player[i].removeButton->enable    (false);
            _player[i].humanAISelector->enable (false);
            _player[i].controller->enable      (false);   

            _playersJoined--;

            // we can't start the game with less than two players so disable 
            // the start button if that's the case.
            if (_playersJoined < 2)
            {
                _startButton->enable (false);
            }
        }

        if (_player[i].humanAISelector->update ())
        {
            // Option was changed.
            switch (_player[i].humanAISelector->getOption ())
            {
            case 0: // Human Controlled
                _player[i].controller->enable (true);    
                selectAvailableController (i, 1);
                break;

            case 1: // Computer Controlled
                _player[i].controller->enable (false);    
                break;
            }

        }

        int direction;

        // Has the controller been changed? Note: the single '=' is intentional.
        if ((direction = _player[i].controller->update ()))
        {
            // A different controller was selected, make sure its available and
            // if not, move on to the next available one.
            selectAvailableController (i, direction);
        }
    }
    
    // Check each controller to see if fire has been pressed.
    for (int i = 0; i < (_game->getInterface ())->numOfControllers (); i++) 
    {
        if ((_game->getControls ())->getCommand (i, CMD_FIRE))
        {
            bool found = false;
            
            // Make sure this controller is not already assigned to a tank
            for (int j = 0 ; j < 8; j++) 
            {                    
                if (   _player[j].enabled
                    && _player[j].humanAISelector->getOption () == 0
                    && _player[j].controller->getOption () == i)
                {
                    found = true;
                    break;
                }
            }
            
            if (!found)
            {
                // This controller is not being used so we can add
                // a new tank! (assuming there's one available.)
                if (_playersJoined < 8) 
                {                      
                    for (int j = 0; j < 8; j++) 
                    {
                        if (!_player[j].enabled)
                        {
                            // We've found an available player slot. Add the 
                            // new player and set them to this controller.
                            _player[j].enabled = true;

                            _player[j].addButton->enable (false);
                            _player[j].removeButton->enable (true);
                            _player[j].humanAISelector->enable (true);
                            _player[j].humanAISelector->setOption (0);
                            _player[j].controller->enable (true);
                            _player[j].controller->setOption (i);
                            break;
                        }
                    }
                    _playersJoined++;

                    // Once 2 or more players have joined, we can allow the
                    // game to start by enabling the start button.
                    if (_playersJoined > 1) 
                    {
                        _startButton->enable (true);
                    }
                }
            }
        }
    }
    
    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the player menu
//
////////////////////////////////////////////////////////////////////////////////
void
cPlayerMenu::draw
(
)
{
    drawBackground ();
    
    // Draw the menu title
    _font->setShadow (true);
    _font->setSize   (0.6f, 0.6f, 0.5f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    _font->printCentredAt (0.0f, 6.5f, "Select Players");

    _font->setSize   (0.4f, 0.4f, 0.35f);
    _font->printCentredAt (0.0f, 5.5f,
                           "Add a player by clicking on a '+' icon or press the"
                           " 'Fire' Button on any Controller");

    // Draw the transparent boxes for each tank entry

    glLoadIdentity ();

    glEnable (GL_BLEND);
  
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    // Draw the transparent boxes for the other options
    glBegin (GL_QUADS);

    glVertex3f   (-7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -6.6f, 0.0f);
    glVertex3f   ( 7.0f, -3.4f, 0.0f);
    glVertex3f   (-7.0f, -3.4f, 0.0f);

    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    glVertex3f   (-4.0f, -4.4f, 0.0f);
    glVertex3f   ( 4.0f, -4.4f, 0.0f);
    glVertex3f   ( 4.0f, -3.6f, 0.0f);
    glVertex3f   (-4.0f, -3.6f, 0.0f);

    glVertex3f   (-4.0f, -5.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.4f, 0.0f);
    glVertex3f   ( 4.0f, -4.6f, 0.0f);
    glVertex3f   (-4.0f, -4.6f, 0.0f);

    glVertex3f   (-4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -6.4f, 0.0f);
    glVertex3f   ( 4.0f, -5.6f, 0.0f);
    glVertex3f   (-4.0f, -5.6f, 0.0f);

    glEnd ();

    glBegin (GL_QUADS);

    // Draw the dark transparent box around the player table
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    glVertex3f   (-9.0f, -2.6f, 0.0f);
    glVertex3f   ( 9.0f, -2.6f, 0.0f);
    glVertex3f   ( 9.0f,  4.7f, 0.0f);
    glVertex3f   (-9.0f,  4.7f, 0.0f);

    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    for (int i = 0; i < 8; i++) 
    {
        if (_player[i].enabled)
        {
            // Draw the brown row line for this player
            glColor4f (0.6f, 0.3f, 0.0f, 0.5f);
           
            glVertex3f   (-8.8f, 3.20f - i * 0.8f, 0.0f);
            glVertex3f   ( 8.8f, 3.20f - i * 0.8f, 0.0f);
            glVertex3f   ( 8.8f, 3.80f - i * 0.8f, 0.0f);
            glVertex3f   (-8.8f, 3.80f - i * 0.8f, 0.0f);

            // This player is active so set the tank's colour normal
            glColor3f (_player[i].colour.r,
                       _player[i].colour.g,
                       _player[i].colour.b);
        }
        else
        {
            // If this player is not active, draw the tank very dark
            glColor3f (_player[i].colour.r / 4.0f,
                       _player[i].colour.g / 4.0f,
                       _player[i].colour.b / 4.0f);
        }

        // Draw the tank graphic for this player
        glVertex3f   (-7.0f, 3.7f - i * 0.8f, 0.0f);
        glVertex3f   (-6.6f, 3.7f - i * 0.8f, 0.0f);
        glVertex3f   (-6.4f, 3.3f - i * 0.8f, 0.0f);
        glVertex3f   (-7.2f, 3.3f - i * 0.8f, 0.0f);
    }

    glEnd ();

    glDisable (GL_BLEND);
      
    // Write the players' names
    _font->setSize   (0.5f, 0.5f, 0.4f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    for (int i = 0; i < 8; i++) 
    {
        // Only name the enabled players
        if (_player[i].enabled)
        {
            _font->printf (-6.0f, 3.30f - i * 0.8f, _player[i].name.c_str ());
        } 
    }

    // Write the column headers above the players
    _font->setSize   (0.3f, 0.3f, 0.25f);
    _font->setColour (0.0f, 1.0f, 1.0f);
    _font->printCentredAt (-8.0f, 4.3f , "Add/Remove");
    _font->printCentredAt (-8.0f, 4.0f , "Player");
    _font->printCentredAt (-4.0f, 4.1f , "Name");
    _font->printCentredAt ( 1.6f, 4.1f , "Controlled by");
    _font->printCentredAt ( 6.3f, 4.1f , "Controller");
    
    // Write the rounds text next to the rounds selector
    _font->setSize   (0.7f, 0.7f, 0.6f);
    _font->setColour (1.0f, 1.0f, 1.0f);
    _font->printCentredAt (-2.0f, -4.35f, "Rounds :");
    _font->setShadow (false);

    // Draw all the controls in the player rows
    for (int i = 0 ; i < 8; i++)
    {
        _player[i].addButton->draw ();
        _player[i].removeButton->draw ();
        _player[i].humanAISelector->draw ();
        _player[i].controller->draw ();
    }

    // Draw the general controls
    _numberOfRounds->draw ();
    _startButton->draw ();
    _backButton->draw ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getPlayerColours
//
// Description : Read the player colours from the settings and set the 
//               default names.
//
////////////////////////////////////////////////////////////////////////////////
void
cPlayerMenu::getPlayerColoursAndNames
(
)
{
    cReadIniFile * settings = _game->getSettings ();

    _player[0].name = "Player 1";
    _player[0].colour.r = settings->getFloat ("Colours", "Tank1red",   0.0f);
    _player[0].colour.g = settings->getFloat ("Colours", "Tank1green", 0.0f);
    _player[0].colour.b = settings->getFloat ("Colours", "Tank1blue",  0.0f);

    _player[1].name = "Player 2";
    _player[1].colour.r = settings->getFloat ("Colours", "Tank2red",   0.0f);
    _player[1].colour.g = settings->getFloat ("Colours", "Tank2green", 0.0f);
    _player[1].colour.b = settings->getFloat ("Colours", "Tank2blue",  0.0f);

    _player[2].name = "Player 3";
    _player[2].colour.r = settings->getFloat ("Colours", "Tank3red",   0.0f);
    _player[2].colour.g = settings->getFloat ("Colours", "Tank3green", 0.0f);
    _player[2].colour.b = settings->getFloat ("Colours", "Tank3blue",  0.0f);
    
    _player[3].name = "Player 4";
    _player[3].colour.r = settings->getFloat ("Colours", "Tank4red",   0.0f);
    _player[3].colour.g = settings->getFloat ("Colours", "Tank4green", 0.0f);
    _player[3].colour.b = settings->getFloat ("Colours", "Tank4blue",  0.0f);

    _player[4].name = "Player 5";
    _player[4].colour.r = settings->getFloat ("Colours", "Tank5red",   0.0f);
    _player[4].colour.g = settings->getFloat ("Colours", "Tank5green", 0.0f);
    _player[4].colour.b = settings->getFloat ("Colours", "Tank5blue",  0.0f);

    _player[5].name = "Player 6";
    _player[5].colour.r = settings->getFloat ("Colours", "Tank6red",   0.0f);
    _player[5].colour.g = settings->getFloat ("Colours", "Tank6green", 0.0f);
    _player[5].colour.b = settings->getFloat ("Colours", "Tank6blue",  0.0f);

    _player[6].name = "Player 7";
    _player[6].colour.r = settings->getFloat ("Colours", "Tank7red",   0.0f);
    _player[6].colour.g = settings->getFloat ("Colours", "Tank7green", 0.0f);
    _player[6].colour.b = settings->getFloat ("Colours", "Tank7blue",  0.0f);

    _player[7].name = "Player 8";
    _player[7].colour.r = settings->getFloat ("Colours", "Tank8red",   0.0f);
    _player[7].colour.g = settings->getFloat ("Colours", "Tank8green", 0.0f);
    _player[7].colour.b = settings->getFloat ("Colours", "Tank8blue",  0.0f);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : selectAvailableController
//
// Description : move to an available controller
//
////////////////////////////////////////////////////////////////////////////////
void
cPlayerMenu::selectAvailableController
(
    int player,   // The number of the player that wants a controller
    int direction // The direction to scroll through the controllers
)

{
    // Each controller can only be used by one player, so make sure we don't 
    // select an already taken one

    int controller = _player[player].controller->getOption ();

    // Keep looping until we fine an available controller
    for (;;)
    {
        int currentController = controller;

        for (int i = 0; i < 8; i++)
        {
            if (   i != player
                && _player[i].enabled 
                && _player[i].humanAISelector->getOption () == 0
                && _player[i].controller->getOption () == currentController)
            {
                // Darn. This controller is used by another player, move to the
                // next controller and check that instead.
                currentController += direction;

                // Controllers are numbered 0-9. Wrap to this range
                if (currentController == -1)
                {
                    currentController = 9;
                }
                else if (currentController == 10)
                {
                    currentController = 0;
                }

                // We have a new controller to check, so we need to start the 
                // checking loop again.
                break;
            }
        }

        if (controller != currentController)
        {
            // update controller and check this one instead
            controller = currentController;
        }
        else
        {
            // no other player was using this controller, so it is valid!
            break;
        }
    }

    // We should now have a valid controller! Set the selector to show it
    _player[player].controller->setOption (controller);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : addPlayers
//
// Description : Tell the game module to create the players ready for the game
//
////////////////////////////////////////////////////////////////////////////////
void
cPlayerMenu::addPlayers
(
) 
{
    for (int i = 0; i < 8; i++) 
    {
        if (_player[i].enabled)
        {
            int controller;

            if (_player[i].humanAISelector->getOption () == 0)
            {
                // Human player, read the controller
                controller = _player[i].controller->getOption ();
            }
            else
            {
                // We tell the game module we're creating an AI player by 
                // setting its controller to -1.
                controller = -1;

            }
            
            // Pass all this information to the game module
            _game->addPlayer (controller, 
                              _player[i].name.c_str (),
                              _player[i].colour);
        }
    }
}
