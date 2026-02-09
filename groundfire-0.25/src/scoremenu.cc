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
//   File name : scoremenu.cc
//
//          By : Tom Russell
//
//        Date : 01-Jun-03
//
// Description : Handles the scoring menu
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "scoremenu.hh"
#include "tank.hh"
#include "controls.hh"
#include "font.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cScoreMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cScoreMenu::cScoreMenu
(
    cGame * game
)
: cMenu (game)
{
    cPlayer ** players = _game->getPlayers ();
    _numOfPlayers = 0;

    // Build up a list of the tanks depending on their current score
    for (int i = 0; i < 8; i++)
    {
        if (players[i] != NULL) 
        {
            addPlayerToOrderedList (players[i]);
            _numOfPlayers++;
        }
    }

    // Display menu for at least this long.
    if (_game->areHumanPlayers ())
    {
        _timeTillActive = 2.0f;
    }
    else
    {
        // No human players to move to next screen so we wait this long and 
        // then progress automatically.
        _timeTillActive = 4.0f;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cScoreMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cScoreMenu::~cScoreMenu
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cScoreMenu::update
(
    double time
)
{
    updateBackground (time);

    // Don't allow user input until timer has expired
    if (_timeTillActive <= 0.0f)
    {
        if (!_game->areHumanPlayers ())
        {
            // There are no human players so exit the menu once it has become 
            // active.
            if (_game->getNumOfRounds () == _game->getCurrentRound ())
            {
                // We've finished! Go to the winner menu!
                return (WINNER_MENU);
            }

            // ...otherwise, on to the shop
            return  (SHOP_MENU);
        }

        for (int i = 0; i < _numOfPlayers; i++)
        {
            double when; // Not needed

            if (_orderedPlayers[i]->getCommand (CMD_FIRE, when))
            {
                if (_game->getNumOfRounds () == _game->getCurrentRound ())
                {
                    // We've finished! Go to the winner menu!
                    return (WINNER_MENU);
                }
                
                // Before exiting, mark the leader tank
                
                if (_orderedPlayers[0]->_score > _orderedPlayers[1]->_score)
                {
                    // Only one tank in first place, so it's the leader!
                    _orderedPlayers[0]->_leader = true;
                }
                else
                {
                    // 1st place is shared, so no-one is the leader!
                    _orderedPlayers[0]->_leader = false;
                }
                
                for (int j = 1; j < _numOfPlayers; j++)
                {
                    _orderedPlayers[j]->_leader = false;
                }
                
                return (SHOP_MENU);
            }
        }
    }
    else
    {
        _timeTillActive -= time;
    }

    return (CURRENT_STATE);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the menu
//
////////////////////////////////////////////////////////////////////////////////
void
cScoreMenu::draw
(
)
{
    drawBackground ();

    glEnable (GL_BLEND);
  
    // Draw the dark grey boxes behind the menu
    glColor4f (0.0f, 0.0f, 0.0f, 0.5f);

    for (int i = 0; i < _numOfPlayers; i++)
    {

        glBegin (GL_QUADS);
        
        glVertex3f   (-8.0f, 6.0f - (i * 1.6f), 0.0f);
        glVertex3f   (-4.8f, 6.0f - (i * 1.6f), 0.0f);
        glVertex3f   (-4.8f, 4.7f - (i * 1.6f), 0.0f);
        glVertex3f   (-8.0f, 4.7f - (i * 1.6f), 0.0f);

        glVertex3f   (-4.5f, 6.0f - (i * 1.6f), 0.0f);
        glVertex3f   ( 4.5f, 6.0f - (i * 1.6f), 0.0f);
        glVertex3f   ( 4.5f, 4.7f - (i * 1.6f), 0.0f);
        glVertex3f   (-4.5f, 4.7f - (i * 1.6f), 0.0f); 

        glVertex3f   ( 4.8f, 6.0f - (i * 1.6f), 0.0f);
        glVertex3f   ( 9.0f, 6.0f - (i * 1.6f), 0.0f);
        glVertex3f   ( 9.0f, 4.7f - (i * 1.6f), 0.0f);
        glVertex3f   ( 4.8f, 4.7f - (i * 1.6f), 0.0f); 
        
        glEnd ();
    }

    glDisable (GL_BLEND);

    _font->setShadow (true);
    _font->setSize (0.5f, 0.5f, 0.4f);
    _font->setColour (0.9f, 0.9f, 0.9f);
    
    // Write the position for each tank
    for (int i = 0; i < _numOfPlayers; i++)
    {
        if (i > 0 && 
            _orderedPlayers[i]->_score ==  _orderedPlayers[i - 1]->_score)
        {
            _font->printCentredAt (-9.0f, 5.1f - (i * 1.6f), " = ");
        }
        else
        {
            switch (i)
            {
            case 0:                
                _font->printCentredAt (-9.0f, 5.1f - (i * 1.6f), "1st");
                break;
                
            case 1:
                _font->printCentredAt (-9.0f, 5.1f - (i * 1.6f), "2nd");
                break;
            
            case 2:
                _font->printCentredAt (-9.0f, 5.1f - (i * 1.6f), "3rd");
                break;
            
            default:
                _font->printCentredAt (-9.0f, 5.1f - (i * 1.6f), "%dth", i + 1);
                break;
            }
        }
    }
    
    // write the column headings
    _font->setSize   (0.5f, 0.5f, 0.4f);
    _font->printCentredAt (-6.3f, 6.5f, "Player");
    _font->printCentredAt ( 0.0f, 6.5f, "Scoring for Round");
    _font->printCentredAt ( 6.9f, 6.5f, "Total Score");

    // Draw the Scores for each player
    for (int i = 0; i < _numOfPlayers; i++)
    {
        drawScoreForPlayer (_orderedPlayers[i], 6.0f - (i * 1.6f));
    }
    _font->setShadow (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawScoreForPlayer
//
// Description : Draw the scoring for the specified player
//
////////////////////////////////////////////////////////////////////////////////
void
cScoreMenu::drawScoreForPlayer
(
    cPlayer * player,
    float     yPos    // How far down the screen to draw the scores.
)
{
    cPlayer * leader = NULL;

    cTank * tank = player->getTank ();

    glLoadIdentity ();

    float r, g, b;

    tank->getColour (r, g, b);

    // Draw a graphic of the tank
    glColor3f (r, g, b);

    glBegin (GL_QUADS);

    glVertex3f   (-7.0f, yPos - 0.8f, 0.0f);
    glVertex3f   (-6.7f, yPos - 0.2f, 0.0f);
    glVertex3f   (-6.1f, yPos - 0.2f, 0.0f);
    glVertex3f   (-5.8f, yPos - 0.8f, 0.0f);

    glEnd ();
    
    // Draw the row of defeated tanks 
   
    float xPos = 0.0f;
    
    for (int i = 0; i < player->_defeatedPlayersCount; i++)
    {
        glEnable (GL_TEXTURE_2D);

        _game->getInterface ()->setTexture (4);

        player->_defeatedPlayers[i]->getTank ()->getColour (r, g, b);

        glColor3f (r, g, b);
        
        glBegin (GL_QUADS);
        
        glTexCoord2f (0.0f, 0.0f);
        glVertex3f (-4.0f + xPos, yPos - 0.9f, 0.0f);
        glTexCoord2f (0.0f, 1.0f);
        glVertex3f (-3.7f + xPos, yPos - 0.3f, 0.0f);
        glTexCoord2f (1.0f, 1.0f);
        glVertex3f (-3.1f + xPos, yPos - 0.3f, 0.0f);
        glTexCoord2f (1.0f, 0.0f);
        glVertex3f (-2.8f + xPos, yPos - 0.9f, 0.0f);
        
        glEnd ();

        glDisable (GL_TEXTURE_2D);

        if (player->_defeatedPlayers[i]->_leader) 
        {
            leader = player->_defeatedPlayers[i];
        }
        
        xPos += 1.3f;
    }

    // If we killed the current leader, Draw a flag with the leader's colour
    if (leader != NULL)
    {
        glColor3f (0.5f, 0.5f, 0.5f);

        glBegin (GL_QUADS);

        // Flag pole first
        glVertex3f (-3.7f  + xPos, yPos - 0.9f, 0.0f);           
        glVertex3f (-3.7f  + xPos, yPos - 0.3f, 0.0f);
        glVertex3f (-3.6f + xPos, yPos - 0.3f, 0.0f);
        glVertex3f (-3.6f + xPos, yPos - 0.9f, 0.0f);  

        // Then the flag itself...

        leader->getTank ()->getColour (r, g, b);

        glColor3f (r, g, b);
        glVertex3f (-3.6f + xPos, yPos - 0.75f, 0.0f);   

        glColor3f (1.0f, 1.0f, 1.0f);        
        glVertex3f (-3.6f + xPos, yPos - 0.3f, 0.0f);

        glColor3f (r, g, b);
        glVertex3f (-2.9f  + xPos, yPos - 0.3f, 0.0f);

        glColor3f (1.0f, 1.0f, 1.0f); 
        glVertex3f (-2.9f  + xPos, yPos - 0.75f, 0.0f);

        glEnd ();   
    }
    
    // Write the player's name under the tank graphic.
    _font->setSize (0.3f, 0.3f, 0.2f);
    _font->printCentredAt (-6.4f, yPos - 1.15f, "%s", player->getName ());
    
    // Write the player's total score so far.
    _font->setSize (0.5f, 0.5f, 0.4f);
    _font->printCentredAt  (6.9f, yPos - 0.9f, "%d", player->_score);

}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : addPlayerToOrderedList
//
// Description : Add the player to a list sorted by the highest score first.
//
////////////////////////////////////////////////////////////////////////////////
void
cScoreMenu::addPlayerToOrderedList
(
    cPlayer * player
)
{
    int insertPosition = 0;

    for (int i = 0; i < _numOfPlayers; i++) 
    {
        if (player->_score > _orderedPlayers[i]->_score) 
        {
            for (int j = _numOfPlayers; j > i; j--)
            {
                _orderedPlayers[j] = _orderedPlayers[j - 1];
            }

            insertPosition = i;
            break;
        }

        insertPosition = i + 1;
    }

    _orderedPlayers[insertPosition] = player;
}
