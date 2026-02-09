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
//   File name : landscape.hh
//
//          By : Tom Russell
//
//        Date : 09-Sep-02
//
// Description : Handles the landscape.
//
//
//
////////////////////////////////////////////////////////////////////////////////
#ifndef __LANDSCAPE_HH__
#define __LANDSCAPE_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <list>
#include <math.h>
#include "interface.hh"

class cReadIniFile;

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////

using namespace std;
    
class cLandscape
{
public:
    cLandscape (cReadIniFile * settings, double seed);
    ~cLandscape ();

    void  update (float time);

    void  draw ();

    float moveToGround (float x, float y);

    void  moveToGroundAtAngle (float * x,
                               float * y,
                               float   angle);

    void  makeHole (float x, float y, float radius);

    bool  groundCollision (float x1,
                           float y1,
                           float x2,
                           float y2,
                           float * collisionX,
                           float * collisionY);

    float getLandscapeWidth () const { return (_landscapeWidth); }

    void dropTerrain (float ammount);

private:
    
   // The internal data structure for the 'chunks' that make up the landscape.
    struct sLandChunk
    {
        float   maxHeight1;  // The top left y coordinate of the chunk
        float   maxHeight2;  // The top right y coordinate of the chunk
        float   minHeight1;  // The bottom left y coordinate of the chunk 
        float   minHeight2;  // The bottom right y coordinate of the chunk
        sColour maxColour1;
        sColour maxColour2;
        sColour minColour1;
        sColour minColour2;
        bool    linkedToNext;    // Is this block attached to the one below it?
        bool    fallingState;    // Whether the chunk is currently falling
        float   waitForFallTime; // Time before the chunk starts falling
        float   fallingSpeed;    // Current falling speed.
    };
    
    void generateTerrain (void);

    void clipSlice (int   slice,
                    float x,
                    float y,
                    float radius);

    int  checkWithinBlastRange (float blastX,
                                float blastY,
                                float radius,
                                float x,
                                float y);

    float clipHeight (float blastX,
                      float blastY,
                      float blastRadius,
                      float x,
                      bool  up);

    int  inChunk (list<sLandChunk>::iterator chunk, float xOffset, float y);

    void findBottomChunkIntersect (list<sLandChunk>::iterator   chunk,
                                   float                        xOffset1,
                                   float                        y1,
                                   float                        xOffset2,
                                   float                        y2,
                                   float                      * collisionX,
                                   float                      * collisionY);

    void findTopChunkIntersect (list<sLandChunk>::iterator   chunk,
                                float                        xOffset1,
                                float                        y1,
                                float                        xOffset2,
                                float                        y2,
                                float                      * collisionX,
                                float                      * collisionY);

    bool intersectChunk (float   xOffset1,
                         float   y1,
                         float   xOffset2,
                         float   y2,
                         int     slice,
                         float * collisionX,
                         float * collisionY);

    void calculateColour (sColour * top,
                          sColour * bottom,
                          float     maxX,
                          float     minX,
                          float     x,
                          bool      calcTop);

    list<sLandChunk>::iterator getSuperblock (int slice, 
                                              list<sLandChunk>::iterator chunk);

    // inline functions
    // These are used to convert world X coordinate into landscape 'slice'
    // coordinates
    inline float getSliceXFromWorldX      (float x);
    inline float getWorldXFromSliceX      (float x);
    inline int   getSliceFromWorldX       (float x);
    inline float getWorldXFromSlice       (int slice);
    inline float getSliceOffsetFromWorldX (float x);

    // Each slice has a list of chunks that are currently on that slice.
    list<sLandChunk> * _landChunks;

    int   _numOfSlices;
    float _sliceToWorldConversion; // Store the value to convert between slice
                                   // number and world x coordinate.
    float _landscapeWidth;

    // Constants (from settings file)
    float _fallPause;
    float _fallAcceleration;
    
};


////////////////////////////////////////////////////////////////////////////////
//
// Function    : getSliceXFromWorldX
//
// Description : Takes a world x coordinate and converts it into a slice 
//               coordinate
//
////////////////////////////////////////////////////////////////////////////////
inline float 
cLandscape::getSliceXFromWorldX
(
    float x
)
{
    return ((x * _sliceToWorldConversion) + (_numOfSlices / 2));
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getWorldXFromSliceX
//
// Description : Takes a slice coordinate and converts it into a world x
//               coordinate
//
////////////////////////////////////////////////////////////////////////////////
inline float
cLandscape::getWorldXFromSliceX
(
    float x
)
{
    return ((x - (_numOfSlices / 2)) / _sliceToWorldConversion);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getSliceFromWorldX
//
// Description : Finds the slice number from a world x coordinate
//
////////////////////////////////////////////////////////////////////////////////
inline int
cLandscape::getSliceFromWorldX
(
    float x
)
{
    return (int)((x * _sliceToWorldConversion) + (_numOfSlices / 2));
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getWorldXFromSlice
//
// Description : Gets the world x coordinate of the start of the numbered slice
//
////////////////////////////////////////////////////////////////////////////////
inline float
cLandscape::getWorldXFromSlice
(
    int slice
)
{
    return ((float)(slice - (_numOfSlices / 2)) / _sliceToWorldConversion);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getSliceOffsetFromWorldX
//
// Description : Gets the fraction across a slice from a world x coordinate
//
////////////////////////////////////////////////////////////////////////////////
inline float
cLandscape::getSliceOffsetFromWorldX
(
    float x
)
{
    float t = getSliceXFromWorldX (x);

    return (t - floor (t));
}

#endif // __LANDSCAPE_HH__
