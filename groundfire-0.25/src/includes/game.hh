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
//   File name : game.hh
//
//          By : Tom Russell
//
//        Date : 07-Sep-02
//
// Description : The main framework of the game. This module keeps track of the 
//               current state the game is in and also stores the list of 
//               entities currently active in the game.
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __GAME_HH__
#define __GAME_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <list>
#include <string>

#include "interface.hh"
#include "inifile.hh"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eGame {};

////////////////////////////////////////////////////////////////////////////////
// Declared Classes
////////////////////////////////////////////////////////////////////////////////
class cMenu;
class cEntity;

class cControls;
class cControlsFile;
class cPlayer;
class cFont;
class cLandscape;

#ifndef NOSOUND
class cSound;
#endif

////////////////////////////////////////////////////////////////////////////////
// Constants and Enums
////////////////////////////////////////////////////////////////////////////////
#define VERSION "v0.25"

// Define all the states that the game can be in
enum enumGameState
{
    CURRENT_STATE, // This is not an actual state. It just means: stay in the 
                   // current state.

    // Menu states
    MAIN_MENU,
    OPTION_MENU,
    CONTROLLERS_MENU,
    SET_CONTROLS_MENU,
    QUIT_MENU,
    SELECT_PLAYERS_MENU,

    // In-round states
    ROUND_STARTING,
    ROUND_IN_ACTION,
    ROUND_FINISHING,
    PAUSE_MENU,

    // Between round menus
    ROUND_SCORE,
    SHOP_MENU,
    WINNER_MENU,

    // Special state for when the game wants to quit
    EXITED
};

class cGame
{
public:
    cGame (bool headless = false);
    ~cGame ();

    bool loopOnce (void);
    
    void addEntity (cEntity * entity) { _entityList.push_back (entity); }
    
    // Helpful functions to return pointers to objects
    enumGameState    getGameState    (void) const { return (_gameState);      }
    cLandscape    *  getLandscape    (void) const { return (_landscape);      }
    cInterface    *  getInterface    (void)       { return (&_interface);     }
    cReadIniFile  *  getSettings     (void)       { return (&_settings);      }
    cControls     *  getControls     (void) const { return (_controls);       }
    cControlsFile *  getControlsFile (void) const { return (_controlsFile);   }
    cFont         *  getFont         (void) const { return (_font);           }
    cPlayer       ** getPlayers      (void)       { return (_players);        }
    cMenu         *  getCurrentMenu  (void) const { return (_currentMenu);    }
#ifndef NOSOUND
    cSound        *  getSound        (void) const { return (_sound);          }
#endif
    float            getTime         (void)       { return (_time);           }
    int              getNumOfPlayers (void) const { return (_numberOfPlayers);}
    int              getNumOfRounds  (void) const { return (_numberOfRounds); }
    int              getCurrentRound (void) const { return (_currentRound);   }
    bool             areHumanPlayers (void) const { return (_humanPlayers);   }

    void             recordTankDeath (void);
    void             addPlayer       (int                 controller,
                                      const std::string & name,
                                      const sColour     & colour);
    void             deletePlayers   (void);

    void setNumOfRounds (int numOfRounds) { _numberOfRounds = numOfRounds; }

    void setActiveController (int activeController)
        {
            _activeController = activeController;
        }

    void explosion (float x, float y, 
                    float size, float damage, 
                    int hitTank, 
                    int soundToPlay, bool whiteOut,
                    cPlayer * owner);

    void setGameState(enumGameState s) { _gameState = s; if (s == 7) _stateCountdown = 3.0f; }
    void initLandscape();
    void setHeadless(bool h) { _headless = h; }
    bool isHeadless() const { return _headless; }

private:

    void loadResources ();

    void loadTexture (char * filename, int textureNum) 
        {
            if (!_interface.loadTexture (filename, textureNum))
            {
                throw eGame ();
            }
        }
    
    void gameLoop (double elapsedTime);
    void menuLoop (double elapsedTime);

    void startRound (void);
    void endRound   (void);

    // Various objects owned by the game object
    cReadIniFile _settings;

    cInterface   _interface;
    cLandscape * _landscape;
    cFont      * _font;
#ifndef NOSOUND
    cSound     * _sound;
#endif

    cControls     * _controls;
    cControlsFile * _controlsFile;

    // Keep track of the players
    int           _numberOfPlayers;
    int           _numberOfActiveTanks;
    cPlayer     * _players[8]; // Up to 8 players at once!

    // The list of all the entity objects that exist at any time
    list<cEntity *> _entityList;

    // should we display the Frames per second during the game?
    bool            _showFPS;
    bool            _headless;

    // Variables for measuring time
    double          _lastTick;
    float           _time;               // The current time from start of round
    int             _frameMeasureCount;
    float           _frameMeasureTime;
    float           _currentFPS;

    // The current game state
    enumGameState   _gameState;
    int             _currentRound;
    int             _numberOfRounds;

    // Are there any human players in the current game?
    bool            _humanPlayers;

    // A timer for counting until a state change occurs
    float           _stateCountdown;

    // A pointer to the current menu (whatever one it may be)
    cMenu         * _currentMenu;

    // This is needed for redefining controls for a certain layout.
    int             _activeController;
};

#endif // __GAME_HH__
