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
//   File name : player.hh
//
//          By : Tom Russell
//
//        Date : 24-March-04
//
// Description : Interface class for a player
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __PLAYER_HH__
#define __PLAYER_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "tank.hh"
#include <string>

class cGame;

// Labels for each of the in-game commands
enum command_t
{
    CMD_FIRE,
    CMD_WEAPONUP,
    CMD_WEAPONDOWN,
    CMD_JUMPJETS,
    CMD_SHIELD,
    CMD_TANKLEFT,
    CMD_TANKRIGHT,
    CMD_GUNLEFT,
    CMD_GUNRIGHT,
    CMD_GUNUP,
    CMD_GUNDOWN
};

class cPlayer
{
    // These classes need to access our scoring variables
    friend class cTank;
    friend class cScoreMenu;
    friend class cShopMenu;
    friend class cWinnerMenu;
    friend class cAIPlayer;
    
public:
    cPlayer (cGame * game, int number);
    virtual ~cPlayer ();

    // Get the state of a command for a player
    virtual bool getCommand (command_t command, double & startTime) = 0;

    // Returns the player's tank entity
    cTank * getTank () { return (&_tank); }
    
    // Not all types of players have controllers so return -1 by default
    virtual int getController () const { return (-1); }
    
    virtual void recordShot (float x, float y, int hitTank)
        {
            // Do nothing
        }

    virtual void recordFired (void) 
        {
            // Do nothing
        }

    // Setup player for a new round
    virtual void newRound ();

    // do things at the end of a round
    void endRound ();

    virtual void update ()
        {
            // Do nothing
        }

    void defeat (cPlayer * deadPlayer);

    void setName (const std::string & name)
        {
            _name = name;
        }

    const char * getName () 
        {
            return (_name.c_str ());
        }
    
protected:
    cTank       _tank;       // The tank this player controls
    int         _number;     // The player's designated number

private:
    // A list of player's we've defeated this round
    cPlayer   * _defeatedPlayers [8];
    int         _defeatedPlayersCount;

    std::string _name;       // Player's name
    int         _score;      // Player's current score
    int         _money;      // Player's current wealth
    bool        _leader;     // Is this player currently the leader?

};

#endif // __PLAYER_HH__
