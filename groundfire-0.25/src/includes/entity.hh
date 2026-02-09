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
//   File name : entity.hh
//
//          By : Tom Russell
//
//        Date : 08-Sep-02
//
// Description : The interface class for all the entities in the game.
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __ENTITY_HH__
#define __ENTITY_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "game.hh"

class cEntity
{
public:
    cEntity (cGame * game);
    virtual ~cEntity ();

    virtual void draw (void) = 0;
    virtual bool update (float time) = 0;

    virtual void doPreRound (void) 
        {
            // By default do nothing. Most entities are created in round anyway 
            // so don't have to worry about this.
        }

    virtual bool doPostRound (void) 
        {
            // By default destroy the entity at the end of the round
            // This should be overridden by entities which want to persist 
            // between rounds. (Tanks are the obvious example.)

            delete this;
            return (false); // 'false' signifies that the entity was destroyed
        }

    void setPosition (float x,  float y)        { _x =  x; _y =  y; }
    void getPosition (float &x, float &y) const {  x = _x;  y = _y; }

protected:
    // Handy function for quickly setting a texture
    void texture (int textureNumber) 
    {
        _game->getInterface()->setTexture (textureNumber);
    }
    
    float _x; // The entity's x position
    float _y; // The entity's y position

    cGame * _game;
};

#endif // __ENTITY_HH__
