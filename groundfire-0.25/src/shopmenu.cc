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
//   File name : shopmenu.cc
//
//          By : Tom Russell
//
//        Date : 01-Jul-03
//
// Description : Handles the shopping menu which appears between rounds
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "shopmenu.hh"

#include "tank.hh"
#include "weapon.hh"
#include "controls.hh"
#include "font.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cShopMenu
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cShopMenu::cShopMenu
(
    cGame * game
)
: cMenu (game)
{
    for (int i = 0; i < 8; i++) 
    {
        // Start everyone with a small delay incase someone was pressing fire 
        // upon entry to the shopping screen.
        _playerSelectPos[i]   = 0;
        _playerSelectDelay[i] = 0.4f;
        _playerDone[i]        = false;
    }

    // 'linelit' is to prevent us drawing too many transparent bars across one 
    // option.
    for (int i = 0; i < 10; i++) 
    {
        _lineLit[i] = false;
    }

    _jumpjetsCost = game->getSettings ()->getInt ("Price", "Jumpjets", 50);

}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cShopMenu
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cShopMenu::~cShopMenu
(
)
{
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : Update the shopping menu
//
////////////////////////////////////////////////////////////////////////////////
enumGameState
cShopMenu::update
(
    double time
)
{
    updateBackground (time);

    cPlayer ** players = _game->getPlayers ();

    bool stillPlayersInShop = false;

    for (int i = 0; i < 8; i++) 
    {
        if (players[i] != NULL && _playerDone[i] == false)
        {            
            stillPlayersInShop = true;

            // Slow down the rate at which the user can scroll down the list by
            // pausing for a short delay after every move
            if (_playerSelectDelay[i] < 0.0f) 
            {
                players[i]->update ();

                double when; // Not used here

                if (players[i]->getCommand (CMD_GUNUP, when))
                {
                    _playerSelectPos[i]--;

                    if (_playerSelectPos[i] == -1) 
                    {
                        _playerSelectPos[i] = 10;
                    }

                    _playerSelectDelay[i] = 0.2f;
                }
                else if (players[i]->getCommand (CMD_GUNDOWN, when))
                {
                    _playerSelectPos[i]++;
                    
                    if (_playerSelectPos[i] == 11) 
                    {
                        _playerSelectPos[i] = 0;
                    }

                    _playerSelectDelay[i] = 0.2f;
                }
                else if (players[i]->getCommand (CMD_FIRE, when))
                {
                    // This tank is trying to purchase a weapon!
                    cTank * tank = players[i]->getTank ();

                    switch (_playerSelectPos[i])
                    {
                    case 0: // Machine Gun
                        if (   players[i]->_money 
                            >= tank->_weapon[MACHINEGUN]->getCost ())
                        {
                            players[i]->_money -= 
                                tank->_weapon[MACHINEGUN]->getCost ();

                            tank->_weapon[MACHINEGUN]->addAmount (50);
                        }
                        break;

                    case 1: // Jump Jets 
                        // Check funds
                        if (players[i]->_money >= _jumpjetsCost)
                        {
                            players[i]->_money -= _jumpjetsCost;
                            tank->_totalFuel += 1.0f;
                        }
                        break;

                    case 2: // Mirvs
                        //check funds
                        if (   players[i]->_money 
                            >= tank->_weapon[MIRVS]->getCost ())
                        {
                            players[i]->_money -= 
                                tank->_weapon[MIRVS]->getCost ();

                            tank->_weapon[MIRVS]->addAmount (1);
                        }
                        break;
                        
                    case 3: // Missiles 
                        // check funds
                        if (   players[i]->_money
                            >= tank->_weapon[MISSILES]->getCost ())
                        {
                            // missiles come in packs of 5
                            players[i]->_money -= 
                                tank->_weapon[MISSILES]->getCost ();

                            tank->_weapon[MISSILES]->addAmount (5); 
                        }
                        break;
                        
                    case 4: // Nukes
                        //check funds
                        if (   players[i]->_money 
                            >= tank->_weapon[NUKES]->getCost ())
                        {
                            players[i]->_money -= 
                                tank->_weapon[NUKES]->getCost ();

                            tank->_weapon[NUKES]->addAmount (1);
                        }
                        break;
                        
                        // These aren't implemented yet!
                    case 5: // Rolling Mines
                    case 6: // Airstrike
                    case 7: // Death's Head
                    case 8: // Hover Coil
                    case 9: // Corbomite
                        break;

                        // We've finished 
                    case 10:
                        _playerDone[i] = true;
                        break;
                        
                    default:
                        break;
                    }

                    // The delay here is quite important. We don't want anyone 
                    // to accidentally buying multiple times
                    _playerSelectDelay[i] = 0.2f;    
                }
            }
            else
            {
                _playerSelectDelay[i] -= time;
            }

            _lineLit[_playerSelectPos[i]] = true;
        }
    }

    // Has everyone finished shopping?
    if (stillPlayersInShop)
    {
        return (CURRENT_STATE);
    }
    else
    {
        return (ROUND_STARTING);
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : Draw the menu
//
////////////////////////////////////////////////////////////////////////////////
void
cShopMenu::draw
(
)
{
    drawBackground ();

    glEnable (GL_BLEND);
  
    glColor4f (0.6f, 0.3f, 0.0f, 0.5f);

    cPlayer ** players = _game->getPlayers ();

    for (int i = 0; i < 8; i++)
    {
        if (players[i] != NULL && _playerDone[i] == false)
        {
            glBegin (GL_QUADS);
            
            glColor4f (0.3f, 0.1f, 0.1f, 0.5f);

            // Draw the vertical bars for each tank. The tabs showing the 
            // current funds appear at either the top or bottom on alternate 
            // tanks.

            if (i % 2 == 0)
            {
                glVertex3f   (-9.4f + (i * 1.5f),  5.6f, 0.0f);
                glVertex3f   (-9.4f + (i * 1.5f),  4.9f, 0.0f);
                glVertex3f   (-6.6f + (i * 1.5f),  4.9f, 0.0f);
                glVertex3f   (-6.6f + (i * 1.5f),  5.6f, 0.0f);

                glVertex3f   (-9.4f + (i * 1.5f), -5.3f, 0.0f);
                glVertex3f   (-9.4f + (i * 1.5f),  4.9f, 0.0f);
                glVertex3f   (-8.1f + (i * 1.5f),  4.9f, 0.0f);
                glVertex3f   (-8.1f + (i * 1.5f), -5.3f, 0.0f);

            }
            else
            {
                glVertex3f   (-10.9f + (i * 1.5f), -5.5f, 0.0f);
                glVertex3f   (-10.9f + (i * 1.5f), -6.2f, 0.0f);
                glVertex3f   (-8.1f  + (i * 1.5f), -6.2f, 0.0f);
                glVertex3f   (-8.1f  + (i * 1.5f), -5.5f, 0.0f);

                glVertex3f   (-9.4f + (i * 1.5f), -5.5f, 0.0f);
                glVertex3f   (-9.4f + (i * 1.5f),  4.7f, 0.0f);
                glVertex3f   (-8.1f + (i * 1.5f),  4.7f, 0.0f);
                glVertex3f   (-8.1f + (i * 1.5f), -5.5f, 0.0f);
            }
            
            // if the weapons line the tank is on is already lit, don't light 
            // it again. This prevents it becoming saturated.
            if (_lineLit[_playerSelectPos[i]] == true)
            {
                float v = _playerSelectPos[i] * 0.8f;

                glColor4f (1.0f, 1.0f, 1.0f, 0.1f);
                glVertex3f   (-9.4f, 3.8f - v, 0.0f);
                glVertex3f   (-9.4f, 4.6f - v, 0.0f);
                glVertex3f   ( 9.4f, 4.6f - v, 0.0f);
                glVertex3f   ( 9.4f, 3.8f - v, 0.0f);

                _lineLit[_playerSelectPos[i]] = false;
            }
            
            glEnd ();
        }
    }

    glDisable (GL_BLEND);

    _font->setSize (0.3f, 0.3f, 0.25f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    for (int i = 0; i < 8; i++) 
    {
        if (players[i] != NULL && _playerDone[i] == false)
        {
            float r, g, b;

            cTank * tank = players[i]->getTank ();

            tank->getColour (r, g, b);

            // Draw a graphic of each tank
            glColor3f (r, g, b);

            float v = _playerSelectPos[i] * 0.8f;

            glLoadIdentity ();

            glBegin (GL_QUADS);

            glVertex3f   (-9.35f + (i * 1.5f), 3.9f - v, 0.0f);
            glVertex3f   (-9.05f + (i * 1.5f), 4.5f - v, 0.0f);
            glVertex3f   (-8.45f + (i * 1.5f), 4.5f - v, 0.0f);
            glVertex3f   (-8.15f + (i * 1.5f), 3.9f - v, 0.0f);

            glEnd ();    

            // Below the tank graphic, draw an indicator of the current amount 
            // of the weapon we are currently lined up with. This is either a 
            // bar (for jumpjets) or a number representing the current 
            // inventory (e.g. nukes)

            switch (_playerSelectPos[i])
            {
            case 0: // Machine Gun
                drawBars (-9.4f + (i * 1.5f), 3.7f - v, 
                          tank->_weapon[MACHINEGUN]->getAmmo () / 50.0f);
                break;

            case 1: // Jump Jets
                drawBars (-9.4f + (i * 1.5f), 3.7f - v, tank->_totalFuel);
                break;

            case 2: // Mirvs
                _font->printCentredAt (-8.75 + (i * 1.5f), 3.5f - v, "x%d", 
                                       tank->_weapon[MIRVS]->getAmmo ());
                break;

            case 3: // Missiles
                _font->printCentredAt (-8.75 + (i * 1.5f), 3.5f - v, "x%d", 
                                       tank->_weapon[MISSILES]->getAmmo ());
                break;

            case 4: // Nukes
                _font->printCentredAt (-8.75 + (i * 1.5f), 3.5f - v, "x%d", 
                                       tank->_weapon[NUKES]->getAmmo ());
                break;

            case 5: // Rolling Mines
            case 6: // Airstrike
            case 7: // Death's Head
            case 8: // Hover Coil
            case 9: // Corbomite
                break;

            default:
                break;
            }
        }
    }

    _font->setShadow (true);
    // Write the number of the round we're about to start.
    _font->setSize (0.6f, 0.6f, 0.5f);
    _font->setColour (1.0f, 1.0f, 1.0f);

    _font->printCentredAt (0.0f, 6.5f, "Round %d of %d", 
                           _game->getCurrentRound () + 1, 
                           _game->getNumOfRounds ());

    _font->setSize (0.4f, 0.4f, 0.3f);
    _font->setColour (0.9f, 0.9f, 0.9f);
    
    int nukeCost       = players[0]->getTank ()->_weapon[NUKES]->getCost ();
    int missileCost    = players[0]->getTank ()->_weapon[MISSILES]->getCost ();
    int mirvCost       = players[0]->getTank ()->_weapon[MIRVS]->getCost ();
    int machineGunCost = players[0]->getTank ()->_weapon[MACHINEGUN]->getCost();

    // Write the weapon names for each row.

    _font->printCentredAt (4.0f,  5.0f, "Cost");
    _font->printCentredAt (7.0f,  5.0f, "Item");

    _font->printCentredAt (7.0f,  4.0f, "Machine Gun");
    _font->printCentredAt (4.0f,  4.0f, "$%d", machineGunCost);
    _font->printCentredAt (7.0f,  3.2f, "Jump Jet");
    _font->printCentredAt (4.0f,  3.2f, "$%d", _jumpjetsCost);
    _font->printCentredAt (7.0f,  2.4f, "Mirvs");
    _font->printCentredAt (4.0f,  2.4f, "$%d", mirvCost);
    _font->printCentredAt (7.0f,  1.6f, "Missiles");
    _font->printCentredAt (4.0f,  1.6f, "$%d", missileCost);
    _font->printCentredAt (7.0f,  0.8f, "Nukes");
    _font->printCentredAt (4.0f,  0.8f, "$%d", nukeCost);
    _font->setColour (0.3f, 0.3f, 0.3f);
    _font->printCentredAt (7.0f,  0.0f, "Rolling Mines");
    _font->printCentredAt (4.0f,  0.0f, "$50");
    _font->printCentredAt (7.0f, -0.8f, "Airstrike");
    _font->printCentredAt (4.0f, -0.8f, "$100");
    _font->printCentredAt (7.0f, -1.6f, "Death's Head");
    _font->printCentredAt (4.0f, -1.6f, "$200");
    _font->printCentredAt (7.0f, -2.4f, "Hover Coil");
    _font->printCentredAt (4.0f, -2.4f, "$150");
    _font->printCentredAt (7.0f, -3.2f, "Corbomite");
    _font->printCentredAt (4.0f, -3.2f, "$20");

    _font->setColour (0.9f, 0.9f, 0.9f);
    _font->printCentredAt (7.0f, -4.0f, "Done!");

    _font->setSize (0.35f, 0.35f, 0.275f);

    // Write the amount of money everybody has
    for (int i = 0; i < 8; i++)
    {
        if (players[i] != NULL && _playerDone[i] == false)
        {
            if (i % 2 == 0) 
            {
                _font->printCentredAt (-8.0f + (i * 1.5f), 5.1f, 
                               "$%d", players[i]->_money);
            }
            else
            {
                _font->printCentredAt (-9.5f + (i * 1.5f), -6.0f, 
                               "$%d", players[i]->_money);    
            }
        }
    }
    _font->setShadow (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawBars
//
// Description : Draw the bars representing inventory (of things like jumpjet 
//               fuel)
//
////////////////////////////////////////////////////////////////////////////////
void
cShopMenu::drawBars
(
    float x,
    float y,
    float numberOfBars
)
{
    glColor3f (1.0f, 1.0f, 1.0f);

    for (int i = 0; numberOfBars > 0.0f; i++)
    {
        float lengthOfBar;

        if (numberOfBars > 1.0f)
        {
            lengthOfBar = 1.3f;
        }
        else
        {
            lengthOfBar = 1.3f * numberOfBars;
        }
        numberOfBars -= 1.0f;

        glBegin (GL_QUADS);

        glVertex3f   (x,               y - (0.2f * i) + 0.15f, 0.0f);
        glVertex3f   (x,               y - (0.2f * i),         0.0f);
        glVertex3f   (x + lengthOfBar, y - (0.2f * i),         0.0f);
        glVertex3f   (x + lengthOfBar, y - (0.2f * i) + 0.15f, 0.0f);

        glEnd ();  
    } 
}
