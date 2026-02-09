////////////////////////////////////////////////////////////////////////////////
//
//               Groundfire C++ Verification Harness
//
////////////////////////////////////////////////////////////////////////////////
//
// Description : Main entry point for cross-language verification.
//               Instantiates Game with Headless Interface, runs a deterministic
//               simulation, and outputs state as JSON.
//
////////////////////////////////////////////////////////////////////////////////

#include "game.hh"
#include "tank.hh"
#include "player.hh"
#include "common.hh"
#include "landscape.hh"
#include <iostream>
#include <iomanip>
#include <vector>

void print_json_state(cGame& game, int tick) {
    // Traverse players/tanks
    // We need to access private members? 
    // Usually game.hh exposes getPlayer(i).
    // Let's assume we can get players.
    
    // Simplest JSON structure:
    // { "tick": N, "tanks": [ { "id": 0, "x": 1.23, "y": 4.56, "hp": 100 } ] }
    
    std::cout << "{ \"tick\": " << tick << ", \"tanks\": [";
    
    int pCount = game.getNumOfPlayers();
    bool first = true;
    for (int i = 0; i < pCount; ++i) {
        cPlayer* p = game.getPlayers()[i];
        if (p) {
            cTank* t = p->getTank();
            float x, y;
            t->getPosition(x, y); // Assuming getPosition(float&, float&)
            
            if (!first) std::cout << ", ";
            std::cout << "{ \"id\": " << i 
                      << ", \"x\": " << std::fixed << std::setprecision(6) << x
                      << ", \"y\": " << std::fixed << std::setprecision(6) << y
                      << ", \"hp\": " << t->getHealth() // Assuming accessor
                      << " }";
            first = false;
        }
    }
    std::cout << "] }" << std::endl;
}

int main(int argc, char** argv) {
    // 1. Instantiate Game (Uses Headless Interface)
    try {
        cGame game(true);
        // game.setHeadless(true); // Redundant now
        
        // 2. Setup Scenario
        // Add 1 Player
        // Need to check signature of addPlayer.
        // Python: add_player(controller, name, colour)
        // C++: void addPlayer (int controller, char * name, sColour colour);
        sColour red(1.0f, 0.0f, 0.0f);
        game.addPlayer(0, (char*)"TestPlayer", red);
        
        // Start Round
        // We need to force state to ROUND_STARTING or ROUND_IN_ACTION
        // game.changeState(ROUND_STARTING)?
        // Accessing private _gameState might be hard if no public setter.
        // But the loop handles transitions.
        
        // NOTE: Groundfire usually starts in MAIN_MENU.
        // We need to navigate menus or force start.
        // If we can't force start easily, we might just test Menu state?
        // But we want Physics parity.
        
        // Hack: Force Game State to ROUND_STARTING to simulate physics
        game.initLandscape();
        game.setGameState(ROUND_STARTING);
        
        // Ensure players are set up for round
        // cGame::startRound (called by loopOnce when countdown finishes) expects players to have tanks.
        // Tanks are always there.
        // But we need to ensure positions are deterministic.
        // Let's seed RNG.
        srand(12345);
        
        // Initialize player for new round manually?
        // Set tank position to avoid garbage coordinates causing OOB collision access
        cPlayer* p = game.getPlayers()[0];
        if (p) {
            cTank* t = p->getTank();
            t->setPosition(0.0f, 5.0f); // Center, Air
        }
        
        // Run loop for 500 ticks.
        
        // Run loop for 500 ticks.
        
        for (int i=0; i<500; i++)
        {
            printf("Loop %d Start\n", i);
            bool running = game.loopOnce();
            printf("Loop %d End. Running: %d\n", i, running);
            if (!running) break;
            
            // printf("Printing JSON\n");
            print_json_state(game, i);
            // printf("JSON Done\n");
            fflush(stdout); // Flush to ensure we see output
        }
        
    } catch (const char * e) {
        std::cerr << "CRASHED with exception: " << e << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "CRASHED" << std::endl;
        return 1;
    }
    
    return 0;
}
