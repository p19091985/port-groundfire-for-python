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
//   File name : winnermenu.cc
//
//          By : Tom Russell
//
//        Date : 28-Feb-04
//
// Description : Handles the 'We have a winner' screen
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "winnermenu.hh"
#include "tank.hh"
#include "controls.hh"
#include "common.hh"
#include "font.hh"

#include <math.h>

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cWinnerMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cWinnerMenu::cWinnerMenu
(
    cGame * game
)
        : cMenu (game),
          _players (game->getPlayers ())
{
    int highestScore = -1;

    // Work out who won (Note: might be more than one tank)
    for (int i = 0; i < _game->getNumOfPlayers (); i++)
    {
        if (_players[i]->_score > highestScore)
        {
            highestScore = _players[i]->_score;
            _winners.clear ();
            _winners.push_back (_players[i]);
            _draw        = false;
        }
        else if (_players[i]->_score == highestScore)
        {
            _draw = true;
            _winners.push_back (_players[i]);
        }
    }

    _spinning = 0.0f;

    if (_game->areHumanPlayers ())
    {
        // Don't allow users to skip this screen until a certain time delay.
        _timeTillActive = 2.0f;
    }
    else
    {
        // No human players so wait a bit longer.
        _timeTillActive = 4.0f;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cWinnerMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cWinnerMenu::~cWinnerMenu
(
)
{
    // That's all. Kill all players ready for the next game.
    _game->deletePlayers ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Updates the winner menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cWinnerMenu::update
(
    double time
)
{
    updateBackground (time);

    if (_timeTillActive <= 0.0f)
    {
        if (!_game->areHumanPlayers ())
        {
            return (MAIN_MENU);
        }

        for (int i = 0; i < _game->getNumOfPlayers (); i++)
        {
            double when;

            if ((_game->getPlayers ())[i]->getCommand (CMD_FIRE, when))
            {
                return (MAIN_MENU);
            }
        }
    }
    else
    {
        _timeTillActive -= time;
    }

    // Update the spinning 'winner' sign.
    _spinning -= time * 4.0f;

    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the winner menu
//
////////////////////////////////////////////////////////////////////////////////
void
cWinnerMenu::draw
(
)
{
    drawBackground ();

    _font->setSize (0.6f, 0.6f, 0.5f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    _font->setShadow (true);
    _font->printCentredAt (0.0f, 6.5f, "Final Result");
    
    if (_draw)
    {
        _font->printCentredAt (0.0f, 5.5f, "It's a tie!");
    }
    else
    {
        _font->printCentredAt (0.0f, 5.5f, "We have a winner!");
    }

    int numOfWinners = _winners.size ();

    int row = 0;
    int col = 0;

    // Work out where to position the tank graphics if we have more than one 
    // winner.
    int cols = ((numOfWinners - 1) / 4);
    float colStart = -((numOfWinners < 5 ? numOfWinners : 4) - 1) * 2.0f;

    for (int i = 0 ; i < numOfWinners; i++) 
    {
        float r, g, b;

        cTank * tank = _winners[i]->getTank();

        glLoadIdentity ();

        float x = colStart + row * 4.0f;
        float y = (cols * 2.0f) - col * 4.0f ;

        glTranslatef (x, y, -6.0f);

        tank->getColour (r, g, b);

        glColor3f (r, g, b);

        row++;
        if (row > 3)
        {
            row = 0;
            col++;
            int remainingWinners = numOfWinners - (col * 4);
            colStart = -((remainingWinners < 5 ? remainingWinners : 4) - 1) 
                * 2.0f;
        }

        glBegin (GL_QUADS);
        glVertex3f (-1.5f,  -0.75f, 0.0f);
        glVertex3f (-0.75f,  0.75f, 0.0f);
        glVertex3f ( 0.75f,  0.75f, 0.0f);
        glVertex3f ( 1.5f,  -0.75f, 0.0f);
        glEnd ();

        // Write the player's name under the tank graphic.
        _font->setSize (0.4f, 0.4f, 0.35f);
        _font->setColour (1.0f, 1.0f, 1.0f);
        _font->printCentredAt (x, y - 1.2f, "%s", _winners[i]->getName ());

        // Draw a spinning 'Winner!'
        _font->setSize (0.6f, 0.6f, 0.5f);
        _font->setColour (1.0f, 1.0f, 1.0f);
        _font->setProportional (false);

        drawSpinningLetter (x, y - 0.4f, _spinning - 0.0f, 'W');
        drawSpinningLetter (x, y - 0.4f, _spinning - 0.2f, 'i');
        drawSpinningLetter (x, y - 0.4f, _spinning - 0.4f, 'n');
        drawSpinningLetter (x, y - 0.4f, _spinning - 0.6f, 'n');
        drawSpinningLetter (x, y - 0.4f, _spinning - 0.8f, 'e');
        drawSpinningLetter (x, y - 0.4f, _spinning - 1.0f, 'r');
        drawSpinningLetter (x, y - 0.4f, _spinning - 1.2f, '!');

        _font->setOrientation (0.0f);
        _font->setProportional (true);
    }

    _font->setShadow (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawSpinningLetter
//
// Description : Draws one letter around a tank
//
////////////////////////////////////////////////////////////////////////////////
void
cWinnerMenu::drawSpinningLetter
(
    float x,
    float y,
    float angle,
    char  charToDraw
)
{
    _font->setOrientation ((angle / PI) * 180.0f - 90.0f);
    _font->printf (x + cos (angle) * 1.8f,
                   y + sin (angle) * 1.8f,
                   "%c", charToDraw);    
}
