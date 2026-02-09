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
//   File name : game.cc
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

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "game.hh"

#include "tank.hh"
#include "font.hh"
#include "mainmenu.hh"
#include "quitmenu.hh"
#include "optionmenu.hh"
#include "controllermenu.hh"
#include "setcontrolsmenu.hh"
#include "landscape.hh"
#include "playermenu.hh"
#include "winnermenu.hh"
#include "scoremenu.hh"
#include "shopmenu.hh"
#include "sounds.hh"
#include "quake.hh"
#include "missile.hh"
#include "missileweapon.hh"
#include "shellweapon.hh"
#include "nukeweapon.hh"
#include "trail.hh"
#include "blast.hh"
#include "humanplayer.hh"
#include "aiplayer.hh"
#include "soundentity.hh"
#include "mirv.hh"
#include "mirvweapon.hh"
#include "machinegunweapon.hh"
#include "common.hh"

#include <GLFW/glfw3.h>
#include <stdlib.h>

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cGame
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cGame::cGame
(
    bool headless
) 
        : _settings ("conf/options.ini"),
          // Create the interface object
          _interface (_settings.getInt ("Graphics", "ScreenWidth",  640),
                      _settings.getInt ("Graphics", "ScreenHeight", 480),
                      _settings.getInt ("Graphics", "Fullscreen",   0))
{
    _headless = headless;

    // load the textures and sounds
    if (!_headless) {
        loadResources ();
    } else {
        _font = NULL;
#ifndef NOSOUND
        _sound = NULL;
#endif
    }

    // These variables are used to determine the time elapsed between frames 
    // and thus, the framerate.
    _frameMeasureCount = 20;
    _frameMeasureTime  = 0.0f;
    _currentFPS        = 0.0f;

    // Should we display the frame rate during the game?
    _showFPS = _settings.getInt ("Graphics", "ShowFPS", 0);

    // Read Settings for classes
    cShellWeapon::readSettings (_settings);
    cNukeWeapon::readSettings (_settings);
    cMissile::readSettings (_settings);
    cQuake::readSettings (_settings);
    cMissileWeapon::readSettings (_settings);
    // _headless = false; // REMOVED: Overwriting parameter
    cTrail::readSettings (_settings);
    cBlast::readSettings (_settings);
    cMirv::readSettings (_settings);
    cMirvWeapon::readSettings (_settings);
    cMachineGunWeapon::readSettings (_settings);

    // Clear the players array 
    _numberOfPlayers = 0;

    for (int i = 0; i < 8; i++)
    {
        _players[i] = NULL;
    }

    _humanPlayers = false;

    _landscape   = NULL; 

    // Initialise the state of the game. We start on the main menu
    _gameState   = MAIN_MENU;
    _currentMenu = new cMainMenu (this);
    _interface.enableMouse (true);

    // Create the controls object to deal with the mapping between the game 
    // controls and the controller devices.
    _controls     = new cControls (&_interface);
    _controlsFile = new cControlsFile (_controls, "conf/controls.ini");
    _controlsFile->readFile ();

/*
    // This Code is here to allow testing of the various menus without having 
    // to go through the rest of the game first. It creates some tanks, sets up
    // some values and launches straight into one of the menus.
    {
        addTank (0);  
        _tank[0]->doPreRound ();
        _tank[0]->_score = 9009;
        _tank[0]->_money = 150;
        addTank (1);  
        _tank[1]->doPreRound ();
        _tank[1]->_score = 9001;
        _tank[1]->_money = 150;
        addTank (2);  
        _tank[2]->doPreRound ();
        _tank[2]->_score = 9001;
        _tank[2]->_money = 150;
        addTank (2);  
        _tank[3]->doPreRound ();
        _tank[3]->_score = 9000;
        _tank[3]->_money = 150;
        addTank (2);  
        _tank[4]->doPreRound ();
        _tank[4]->_score = 9001;
        _tank[4]->_money = 150;
        addTank (2);  
        _tank[5]->doPreRound ();
        _tank[5]->_score = 9001;
        _tank[5]->_money = 150;
        addTank (2);  
        _tank[6]->doPreRound ();
        _tank[6]->_score = 9001;
        _tank[6]->_money = 150;
        addTank (2);  
        _tank[7]->doPreRound ();
        _tank[7]->_score = 9001;
        _tank[7]->_money = 150;

        _tank[3]->_leader = true;
        _tank[0]->defeated (_tank[4]);
        _tank[0]->defeated (_tank[3]);
        _tank[5]->defeated (_tank[5]);

    }

    _gameState   = SHOP_MENU;
    _currentMenu = new cShopMenu (this);
*/

    // Finally, reset the timer.
    glfwSetTime (0.0);
    _lastTick = 0.0;
    _stateCountdown = 0.0f;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cGame
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cGame::~cGame
(
    void
) 
{
    if (_gameState == ROUND_STARTING ||
        _gameState == ROUND_IN_ACTION ||
        _gameState == ROUND_FINISHING ||
        _gameState == PAUSE_MENU)
    {
        endRound ();        
    }

    deletePlayers ();

    if (_controls)
    {
        delete _controls;
    }

    if (_controlsFile)
    {
        delete _controlsFile;
    }

    if (_currentMenu) 
    {
        delete _currentMenu;
    }
    
    if (_font) 
    {
        delete _font;
    }

#ifndef NOSOUND
    if (_sound) 
    {
        delete _sound;
    }
#endif

}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : loadResources
//
// Description : Load the external resources used by the game.
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::loadResources
(
)
{
    // specify the number of textures
    _interface.defineTextures (12);

    // Load each of the textures used by the game
    loadTexture ("data/blast.tga",       0);
    loadTexture ("data/trail.tga",       1);
    loadTexture ("data/exhaust.tga",     2);
    loadTexture ("data/damage.tga",      4);
    loadTexture ("data/smoke.tga",       5);
    loadTexture ("data/menuback.tga",    6);
    loadTexture ("data/weaponicons.tga", 7);
    loadTexture ("data/arrow.tga",       8);
    loadTexture ("data/logo.tga",        9);
    loadTexture ("data/addbutton.tga",   10);
    loadTexture ("data/removebutton.tga",11);

    // Create the font object used to render the text to the screen.
    _font = new cFont (&_interface, 3);

#ifndef NOSOUND
    // Initialise the sound system (openAL)
    _sound = new cSound (10);

    // Load all the Wav files used by the game
    _sound->loadSound (0, "data/fireshell.wav");
    _sound->loadSound (1, "data/shelldeath.wav");
    _sound->loadSound (2, "data/quake.wav");
    _sound->loadSound (3, "data/jumpjets.wav");
    _sound->loadSound (4, "data/missile.wav");
    _sound->loadSound (5, "data/launchmissile.wav");
    _sound->loadSound (6, "data/missiledeath.wav");
    _sound->loadSound (7, "data/nuke.wav");
    _sound->loadSound (8, "data/machinegun.wav");
    _sound->loadSound (9, "data/metal.wav");

#endif
}


////////////////////////////////////////////////////////////////////////////////
//
// Function    : loopOnce
//
// Description : Does one iteration of the game (i.e. Update & Draw). Returns 
//               'false' when the program is exiting.
//
////////////////////////////////////////////////////////////////////////////////
bool
cGame::loopOnce
(
    void
)
{
    // Calculate the time that has passed since the last iteration
    double currentTick = glfwGetTime ();
    double elapsedTime = currentTick - _lastTick;
    if (elapsedTime > 0.1) elapsedTime = 0.1; // Cap to prevent logic explosion
    printf("Loop dt: %f, Total: %f\n", elapsedTime, currentTick);
    _lastTick = currentTick;

    _time = currentTick;
    
    // Start the frame
    if (!_headless) _interface.startDraw ();
    
    // printf("Game Loop State: %d\n", _gameState);
    if (_controls == NULL) printf("CONTROLS IS NULL!\n");

    switch (_gameState)
    {       
    case MAIN_MENU:
    case OPTION_MENU:
    case CONTROLLERS_MENU:
    case SET_CONTROLS_MENU:
    case QUIT_MENU:
    case SELECT_PLAYERS_MENU:
    case SHOP_MENU:
    case ROUND_SCORE:
    case WINNER_MENU:
        // All the menu states are handled in their own function.
        menuLoop (elapsedTime);
        break;
        
    case ROUND_STARTING:
        printf("ROUND_STARTING: countdown %f\n", _stateCountdown);
        gameLoop (elapsedTime);
        
        // While the round is starting, draw the round number in the centre of 
        // the screen.
        if (!_headless)
        {
            _font->setShadow (true);
            _font->setSize   (0.6f, 0.6f, 0.5f);
            _font->setColour (1.0f, 1.0f, 1.0f);
            _font->printCentredAt (0.0f,  0.5f, "Round %d", _currentRound);
            _font->printCentredAt (0.0f, -0.5f, "Get Ready");
            _font->setShadow (false);
        }
        
        // Countdown until the round begins
        _stateCountdown -= elapsedTime;
        if (_stateCountdown < 0.0f) 
        {
            _gameState = ROUND_IN_ACTION;
        }
        break;
        
    case ROUND_FINISHING:
        // When all but one tank is dead (or ALL tanks are dead), we start 
        // counting down for the round to end.
        gameLoop (elapsedTime);
        _stateCountdown -= elapsedTime;
        if (_stateCountdown < 0.0f) 
        {
            // That's it, round over! Go to the scoring menu.
            endRound ();
            _gameState = ROUND_SCORE;
            _currentMenu = new cScoreMenu (this);
            _interface.enableMouse (true);
        }            
        break;
        
    case ROUND_IN_ACTION:
        gameLoop (elapsedTime);
        break;
        
    case PAUSE_MENU:
        // The pause menu is not currently implemented.
        break;
        
    case EXITED:
        // A special state that tells this loop to terminate the program.
        return (false);
        
    default:
        break;
    }
    
    // If we have been told to display the Frames per second, we should draw it
    // now in the bottom left corner.
    // If we have been told to display the Frames per second, we should draw it
    // now in the bottom left corner.
    if (_showFPS && !_headless)
    {
        // To get a better estimate of the average FPS, only update the FPS
        // every 20 frames.
        if (_frameMeasureCount == 0) 
        {
            // This is the 20th frame so calculate a new FPS
            _currentFPS = 20.0f / _frameMeasureTime;
            _frameMeasureTime  = 0.0f;
            _frameMeasureCount = 20;
        }
        else
        {
            // This is not the 20th frame so don't calculate a new FPS
            _frameMeasureTime += elapsedTime;
            _frameMeasureCount--;
        }
        
        _font->setSize   (0.3f, 0.3f, 0.25f);
        _font->setColour (0.5f, 1.0f, 0.2f);
        
        _font->printf (-10.0f, -7.3f, "%.1f FPS", _currentFPS);
    }
    
    // End the frame
    _interface.endDraw ();
    
    // 'true' means we haven't finished.
    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : gameLoop
//
// Description : implements the part of the loop that occurs while a round is 
//               in progress. (i.e. updating the entities.)
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::gameLoop
(
    double elapsedTime
)

{
    list<cEntity *>::iterator iterator;

    // First we update everything. Landscape first and then the entities.
    
    // printf("Updating Landscape\n");
    _landscape->update ((float)elapsedTime);

    for (iterator  = _entityList.begin ();
         iterator != _entityList.end ();)
    {
        // printf("Updating Entity %p\n", *iterator);
        // If an entities update function returns 'false', that entity has died
        // and should be removed from the list of entities. 
        if (!(*iterator)->update ((float)elapsedTime))
        {
            iterator = _entityList.erase (iterator);
        }
        else
        {
            ++iterator;
        }
    }

    // Now we draw everything. First the landscape and then the entities.

    if (!_headless)
    {
        _landscape->draw ();
    
        for (iterator  = _entityList.begin ();
             iterator != _entityList.end ();
             iterator++)
        {
            (*iterator)->draw ();
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : menuLoop
//
// Description : Updates and Draws the current menu. Also, handles the state
//               changes while in a menu.
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::menuLoop
(
    double elapsedTime
)

{
    // update and draw the current menu.
    enumGameState changeState = _currentMenu->update (elapsedTime);

    _currentMenu->draw ();

    // 'CURRENT_STATE' means we haven't changed state, otherwise we need to
    // change the state.
    if (changeState != CURRENT_STATE)
    {
        // Delete the current menu and set the new state
        _gameState = changeState;
        delete _currentMenu;
        _currentMenu = NULL;

        // Create a new menu (or go to the game) depending on what the new state
        // is.
        switch (_gameState)
        {
        case MAIN_MENU:
            _currentMenu = new cMainMenu (this);
            break;

        case OPTION_MENU:
            _currentMenu = new cOptionMenu (this);
            break;

        case CONTROLLERS_MENU:
            _currentMenu = new cControllerMenu (this);
            break;

        case SET_CONTROLS_MENU:
            _currentMenu = new cSetControlsMenu (this, _activeController);
            break;

        case QUIT_MENU:
            _currentMenu = new cQuitMenu (this);
            break;

        case SELECT_PLAYERS_MENU:
            _currentRound = 0;
            _currentMenu = new cPlayerMenu (this);
            break;

        case SHOP_MENU:
            _currentMenu = new cShopMenu (this);
            break;

        case WINNER_MENU:
            _currentMenu = new cWinnerMenu (this);
            break;

        case ROUND_STARTING:
            // We are starting a new round. Disable the mouse, set the
            // countdown and increment the round number.
            _interface.enableMouse (false);
            _stateCountdown = 2.0f;
            _currentRound++;
            startRound ();
            break;

        case EXITED:
            // We are quiting the program.
            break;

        default:
            break;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : startRound
//
// Description : Do any initialisations needed before the start of a new round.
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::startRound
(
)
{
    // Create a new landscape for the round.
    _landscape = new cLandscape (&_settings, _lastTick);
    
    // Tell all the players we're starting a new round
    for (int i = 0; i < _numberOfPlayers; i++)
    {
        _players[i]->newRound ();
    }

    // Call the 'doPreRound' function for any entities that have survived from 
    // the previous round. Usually this means the tanks.
    list<cEntity *>::iterator iterator;

    for (iterator  = _entityList.begin ();
         iterator != _entityList.end ();
         iterator++)
    {
        (*iterator)->doPreRound ();
    }

    // Work out how many tanks will feature in this round.
    _numberOfActiveTanks = 0;

    int tankOrder[8];

    for (int i = 0; i < _numberOfPlayers; i++)
    {
        if (_players[i]->getTank ()->alive ()) 
        {
            tankOrder[_numberOfActiveTanks] = i;

            _numberOfActiveTanks++;
        }
    }

    // Choose a random location on the landscape to position each tank. This 
    // makes it a bit fairer, because any tank can appear anywhere. The tanks 
    // are always equally spaced out.

    // This first part jiggles the order across the screen that the tanks will 
    // be positioned.
    for (int i = 0; i < 20; i++) 
    {
        int firstTank  = rand () % _numberOfActiveTanks;
        int secondTank = rand () % _numberOfActiveTanks;

        if (firstTank != secondTank)
        {
            // Swap the tanks over. Yep, this does do a swap in case you were 
            // wondering.
            tankOrder[firstTank]  ^= tankOrder[secondTank];
            tankOrder[secondTank] ^= tankOrder[firstTank];
            tankOrder[firstTank]  ^= tankOrder[secondTank];
        }
    }

    // Finally, tell each tank where it is located.
    for (int i = 0; i < _numberOfActiveTanks; i++) 
    {
        if (_players[tankOrder[i]]->getTank ()->alive ())
        {

            _players[tankOrder[i]]->getTank ()->setPositionOnGround (
                -10.0 + (10.0 / _numberOfActiveTanks) 
                + (i * (20.0 / _numberOfActiveTanks)));
        }
    }

    // Create an earthquake entity for this round.
    cQuake * earthquake = new cQuake (this);
    // insert at the front of the list so that it always gets updated first.
    _entityList.push_front (earthquake);

    // Finally, reset the clock for this round.
    glfwSetTime (0.0);
    _lastTick = 0.0;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : endRound
//
// Description : Do some tidying up at the end of a round.
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::endRound
(
)
{
    // Tell all players the round has ended so they can calculate the score
    for (int i = 0; i < _numberOfPlayers; i++)
    {
        _players[i]->endRound ();
    }
    
    // Call the doPostRound for all active entities, in most cases, this means 
    // they will self destruct.
    list<cEntity *>::iterator iterator;
    
    for (iterator  = _entityList.begin ();
         iterator != _entityList.end ();)
    {
        if (!(*iterator)->doPostRound ())
        {
            iterator = _entityList.erase (iterator);
        }
        else
        {
            ++iterator;
        }
    }

    // Remove the landscape, it's job is done!
    delete _landscape;
    _landscape = NULL;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : recordTankDeath
//
// Description : Everytime a tank dies this function is called. It's used to 
//               determine when it's time to end the round.
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::recordTankDeath 
(
)
{ 
     _numberOfActiveTanks--; 

    if ( _numberOfActiveTanks < 2 && _gameState == ROUND_IN_ACTION)
    {
        // Only one tank left, start a 5 second countdown to the end of the 
        // round.
        _gameState = ROUND_FINISHING;
        _stateCountdown = 5.0f;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : addPlayer
//
// Description : Creates a new player. The controller number for the player is
//               passed as an argument. If the controller specified is '-1' an 
//               AI player is created. 
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::addPlayer
(
    int                 controller,
    const std::string & name,
    const sColour     & colour
)
{
    if (controller == -1)
    {
        // Create an AI player
        _players[_numberOfPlayers] = new cAIPlayer (this, _numberOfPlayers);
    }
    else
    {
        // Create a human player

        _players[_numberOfPlayers] = new cHumanPlayer (this, _numberOfPlayers, 
                                                       controller, _controls);

        // We know there's at least one human player in the game.
        _humanPlayers = true;
    }

    _players[_numberOfPlayers]->getTank ()->setColour (colour);
    _players[_numberOfPlayers]->setName (name);
       
    // Add the player's tank entity to the list of entities
    addEntity (_players[_numberOfPlayers]->getTank ());

    _numberOfPlayers++;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : deletePlayers
//
// Description : Kills all the players and removes the entityList. Only do this 
//               when the entity list is empty (except for the tanks.)
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::deletePlayers
(
)
{
    for (int i = 0 ; i < 8; i++) 
    {
        if (_players[i] != NULL)
        {
            delete _players[i];
            
            _players[i] = NULL;
        }
    }

    _numberOfPlayers = 0;

    _entityList.clear ();

    // There are no players any more so there are no human players.
    _humanPlayers = false;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : explosion
//
// Description : Create an explosion at the coordinates specified
//
//
////////////////////////////////////////////////////////////////////////////////
void
cGame::explosion 
(
    float     x,
    float     y,
    float     size,
    float     damage,
    int       hitTank,
    int       soundToPlay,
    bool      whiteOut,
    cPlayer * owner
)
{
    // Blow a hole in the terrain
    _landscape->makeHole (x, y, size); 

    // Create a blast entity over the hole
    cBlast * blast = new cBlast (this, x, y, size, 0.8f, whiteOut);
    addEntity (blast);

    // Play the explosion sound
    cSoundEntity * blastSound = new cSoundEntity (this, soundToPlay, false);
    addEntity (blastSound);
    
    for (int i = 0; i < 8 && _players[i] != NULL; i++)
    {
        cTank * tank = _players[i]->getTank ();
        
        if (i == hitTank)
        {
            // Do maximum damage to hit tank
            if (tank->doDamage (damage))
            {
                // The tank was destroyed, credit the kill to the player that 
                // created this explosion.
                owner->defeat (_players[i]);
            }
        }
        else
        {
            float tankX;
            float tankY;

            // Apply splash (none-direct) damage to this tank

            float hitRange = tank->getCentre (tankX, tankY);
            
            float squaredDistance = sqr (tankX - x) + sqr (tankY - y);
            
            float maxDistance = sqr (size + hitRange);

            // Check if tank was near enough to the blast to take damage
            if (squaredDistance < maxDistance) 
            {
                // Tank was in range so it will take some damage.
                if (tank->doDamage 
                    (damage * (1 - (squaredDistance / maxDistance))))
                {
                    // The tank was destroyed, credit the kill to the player
                    // that created this explosion.
                    owner->defeat (_players[i]);
                }
            }
        }
    }
}

void cGame::initLandscape() { printf("Init Landscape\n"); _landscape = new cLandscape(&_settings, _lastTick); printf("Landscape Done\n"); }
