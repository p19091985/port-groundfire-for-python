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
//   File name : landscape.cc
//
//          By : Tom Russell
//
//        Date : 07-Sep-02
//
// Description : Handles the landscape.
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "landscape.hh"
#include <GLFW/glfw3.h>
#include "common.hh"
#include "inifile.hh"
#include "report.hh"

#include <math.h>
#include <cstdio>

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cLandscape
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cLandscape::cLandscape
(
    cReadIniFile * settings,
    double         seed
)
{
    srand ((int)(seed * 1000.0f));

    // Read the settings for the landscape.

    // 'fallPause' is the ammount of time before unsupported parts of the 
    // terrain will begin to fall.
    _fallPause        = settings->getFloat ("Terrain", "FallPause", 0.1f);
    _fallAcceleration = settings->getFloat ("Terrain", "FallAcceleration",5.0f);

    _numOfSlices    = settings->getInt   ("Terrain", "Slices", 10);
    _landscapeWidth = settings->getFloat ("Terrain", "Width",  11);
    _sliceToWorldConversion = ((float)(_numOfSlices / 2) / _landscapeWidth);

    _landChunks = new list<sLandChunk>[_numOfSlices];

    generateTerrain ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cLandscape
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cLandscape::~cLandscape
(
)
{
    for (int i = 0; i < _numOfSlices; i++)
    {
        _landChunks[i].clear ();
    } 

    delete[] _landChunks;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : generateTerrain
//
// Description : Builds up a new random terrain.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::generateTerrain 
(
)
{
    float * heights  = new float[_numOfSlices + 1];
    float * smoothed = new float[_numOfSlices + 1];

    // Start by initialising all slices to a flat constant elevation.
    for (int i = 0; i < _numOfSlices + 1; i++)
    {
        heights[i]  = -7.0f;
    }

    // Create a number of random 'plateaus'. This consists of raising various 
    // sized chunks of the terrain by a random ammount.
    for (int i = 0; i < 18; i++) 
    {
        int   centre  = rand () % ((_numOfSlices + 1) * 2) 
            - ((_numOfSlices + 1) / 2);
        float height  = (float)(rand () % 1000) / 300.0f;
        int   width   = rand () % ((_numOfSlices + 1) / 2) + 3;
        int   plateau = rand () % (width / 3); 

        for (int j = 0; j < _numOfSlices + 1; j++)
        {
            int distance = abs (centre - j);

            if (distance < plateau)
            {
                heights[j] += height;
            }
            else if (distance < width)
            {
                heights[j] += ((width - (distance - plateau)) / (float)width)
                    * height;
            }

            if (heights[j] > 5.0f)
            {
                heights[j] = 5.0f;
            }
        }
    }

    // Finally, run a smoothing algorithm across the landscape to remove sharp 
    // corners and to create a more natural look.

    for (int i = 0; i < _numOfSlices + 1; i++)
    {
        if (i >= 10 && i < _numOfSlices - 10)
        {
            smoothed[i] = 0.0f;

            for (int j = (i - 10); j < (i + 11); j++)
            {
                smoothed[i] += heights[j];
            }

            smoothed[i] /= 21;
        }
        else
        {
            smoothed[i] = heights[i];
        }
    }

    delete[] heights;

    // Now create the chunks for each landscape slice with the calculated 
    // heights.

    for (int i = 0; i < _numOfSlices; i++)
    {
        sLandChunk baseChunk;
        sLandChunk colourChunk;

        colourChunk.maxHeight1      = smoothed[i];
        colourChunk.maxHeight2      = smoothed[i + 1];
        colourChunk.maxColour1      = sColour (0.4f, 0.4f, 0.0f);
        colourChunk.maxColour2      = sColour (0.4f, 0.4f, 0.0f);
        colourChunk.minHeight1      = smoothed[i] - 1.0f;
        colourChunk.minHeight2      = smoothed[i + 1] - 1.0f;
        colourChunk.minColour1      = sColour (0.8f, 0.8f, 0.0f);
        colourChunk.minColour2      = sColour (0.8f, 0.8f, 0.0f);
        colourChunk.fallingState    = false;
        colourChunk.waitForFallTime = 0.0f;
        colourChunk.linkedToNext    = false;


        if (colourChunk.minHeight1 > -7.5f || colourChunk.minHeight2 > -7.5f )
        {
            colourChunk.linkedToNext  = true;

            baseChunk.maxHeight1      = smoothed[i] - 1.0f;
            baseChunk.maxHeight2      = smoothed[i + 1] - 1.0f;
            baseChunk.maxColour1      = sColour (0.8f, 0.8f, 0.0f);
            baseChunk.maxColour2      = sColour (0.8f, 0.8f, 0.0f);
            baseChunk.minHeight1      = -8.0f;
            baseChunk.minHeight2      = -8.0f;
            baseChunk.minColour1      = sColour (0.8f, 0.8f, 0.0f);
            baseChunk.minColour2      = sColour (0.8f, 0.8f, 0.0f);
            baseChunk.fallingState    = false;
            baseChunk.waitForFallTime = 0.0f;
            baseChunk.linkedToNext    = false;

            _landChunks[i].push_back (colourChunk);
            _landChunks[i].push_back (baseChunk);
        }
        else
        {
            _landChunks[i].push_back (colourChunk);
        }
    }

    delete[] smoothed;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : update
//
// Description : updates the landscape. This consists of dropping any falling 
//               chunks.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::update
(
    float time
)
{
 
    bool leftAtRest;
    bool rightAtRest;
   
    for (int i = 0; i < _numOfSlices; i++)
    {
        list<sLandChunk>::iterator iterator;
        list<sLandChunk>::iterator nextIterator;

        // For each chunk on this slice
        for (iterator  = _landChunks[i].begin ();
             iterator != _landChunks[i].end ();)
        {
            list<sLandChunk>::iterator startSuperChunkIterator;
            list<sLandChunk>::iterator endSuperChunkIterator;

            startSuperChunkIterator = endSuperChunkIterator = iterator;

            while ((*endSuperChunkIterator).linkedToNext)
            {
                endSuperChunkIterator++;
            }

            // Treat all chunks between startSuperChunkIterator & 
            // endSuperChunkIterator (inclusive) as one big chunk

            // Is this chunk falling?
            if ((*iterator).fallingState)
            {
                if ((*iterator).waitForFallTime > 0.0f)
                {
                    (*iterator).waitForFallTime -= time;
                }
                else
                {
                    leftAtRest = false;
                    rightAtRest = false;

                    float fallAmount      = (*iterator).fallingSpeed * time; 
                    float leftFallAmount  = fallAmount;
                    float rightFallAmount = fallAmount;

                    (*iterator).fallingSpeed += (_fallAcceleration * time);

                    nextIterator = endSuperChunkIterator;
                    nextIterator++;

                    float newMinHeight1 = 
                        (*endSuperChunkIterator).minHeight1 - fallAmount;
                    float newMinHeight2 =
                        (*endSuperChunkIterator).minHeight2 - fallAmount;

                    // Check the left side of the super chunk
                    if ((*nextIterator).maxHeight1 > newMinHeight1)
                    {
                        leftFallAmount = (*endSuperChunkIterator).minHeight1
                            - (*nextIterator).maxHeight1;
                        leftAtRest = true;
                    }

                    // Check the right side of the super chunk
                    if ((*nextIterator).maxHeight2 > newMinHeight2)
                    {
                        rightFallAmount = (*endSuperChunkIterator).minHeight2
                            - (*nextIterator).maxHeight2;
                        rightAtRest = true;
                    }
                    
                    // Move down all the blocks in the superblock
                    for (;iterator != nextIterator; iterator++)
                    {
                        (*iterator).minHeight1 -= leftFallAmount;
                        (*iterator).minHeight2 -= rightFallAmount;
                        (*iterator).maxHeight1 -= leftFallAmount;
                        (*iterator).maxHeight2 -= rightFallAmount;
                    }                    

                    // If both sides have stopped falling, merge this chunk
                    // with the one below it.
                    if (leftAtRest && rightAtRest) 
                    {
                        if ((*endSuperChunkIterator).maxColour1 == 
                            (*endSuperChunkIterator).minColour1 &&
                            (*endSuperChunkIterator).maxColour2 ==
                            (*endSuperChunkIterator).minColour2)
                        {                            
                            (*nextIterator).maxHeight1 = 
                                (*endSuperChunkIterator).maxHeight1;
                            (*nextIterator).maxHeight2 =
                                (*endSuperChunkIterator).maxHeight2;

                            if (   endSuperChunkIterator
                                != startSuperChunkIterator)
                            {
                                // Copy all the attributes of the block we're 
                                // merging with onto the first block in our 
                                // superblock.
                                (*startSuperChunkIterator).fallingState = 
                                    (*nextIterator).fallingState;
                                (*startSuperChunkIterator).fallingSpeed =  
                                    (*nextIterator).fallingSpeed;
                                (*startSuperChunkIterator).waitForFallTime = 
                                    (*nextIterator).waitForFallTime;
                            }

                            iterator = _landChunks[i].erase 
                                (endSuperChunkIterator);

                            // NOTE :: We should skip over the next superblock 
                            // because it has just been attached to the previous
                            // superblock and thus should not be moved again 
                            // seperately.
                            while (iterator->linkedToNext)
                            {
                                iterator++;
                            }
                            iterator++;
                            continue;
                        }
                        else
                        {
                            // There is a difference in the colours between 
                            // these blocks so don't merge. Instead, link them
                            // together into a superblock.
                            (*endSuperChunkIterator).linkedToNext   = true;

                            // Our superblock takes on the attributes of the
                            // bottom block that we just merged with.
                            (*startSuperChunkIterator).fallingState = 
                                (*nextIterator).fallingState;
                            (*startSuperChunkIterator).fallingSpeed =  
                                (*nextIterator).fallingSpeed;
                            (*startSuperChunkIterator).waitForFallTime = 
                                (*nextIterator).waitForFallTime;

                            // NOTE :: We should skip over the next superblock 
                            // because it has just been attached to the previous
                            // superblock and thus should not be moved again 
                            // seperately.
                            while (iterator->linkedToNext)
                            {
                                iterator++;
                            }
                            iterator++;
                            continue;
                        }
                    }
                }
            }
            iterator = endSuperChunkIterator;
            iterator++;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : draw
//
// Description : draws the landscape
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::draw
(
)
{
    glLoadIdentity ();
    
    glBegin (GL_QUADS);

    // Draw the sky
    glColor3f  (0.0f, 0.0f, 0.4f);
    glVertex3f (-10.0f,  7.5f, -20.0f);
    glVertex3f ( 10.0f,  7.5f, -20.0f);
    glColor3f  (0.6f, 0.0f, 0.4f);
    glVertex3f ( 10.0f, -7.5f, -20.0f);
    glVertex3f (-10.0f, -7.5f, -20.0f);
    
    for (int i = 0; i < _numOfSlices; i++)
    {
        float x1 = 
            ((i / (float)(_numOfSlices / 2)) - 1.0f) * _landscapeWidth;
        float x2 = 
            (((i + 1) / (float)(_numOfSlices / 2)) - 1.0f) * _landscapeWidth;
        
        list<sLandChunk>::iterator iterator;

        // draw each chunk on this slice.
        for (iterator  = _landChunks[i].begin ();
             iterator != _landChunks[i].end ();
             iterator++)
        {            
            glColor3f ((*iterator).minColour1.r,
                       (*iterator).minColour1.g,
                       (*iterator).minColour1.b);

            glVertex3f (x1, (*iterator).minHeight1, -10.0f);

            glColor3f ((*iterator).maxColour1.r,
                       (*iterator).maxColour1.g,
                       (*iterator).maxColour1.b);

            glVertex3f (x1, (*iterator).maxHeight1, -10.0f);

            glColor3f ((*iterator).maxColour2.r,
                       (*iterator).maxColour2.g,
                       (*iterator).maxColour2.b);

            glVertex3f (x2, (*iterator).maxHeight2, -10.0f);

            glColor3f ((*iterator).minColour2.r,
                       (*iterator).minColour2.g,
                       (*iterator).minColour2.b);
            
            glVertex3f (x2,  (*iterator).minHeight2, -10.0f);
        }
    }   
    
    glEnd ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : makeHole
//
// Description : Makes a hole in the landscape at the specified position and of
//               the specified size.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::makeHole 
(
    float x,
    float y,
    float radius
) 
{
    int minSlice = getSliceFromWorldX (x - radius);
    int maxSlice = getSliceFromWorldX (x + radius) + 1;
  
    if (minSlice < 0) 
    {
        minSlice = 0;
    }
    
    if (maxSlice >= _numOfSlices)
    {
        maxSlice = _numOfSlices - 1;
    }
    
    for (int i = minSlice; i <= maxSlice; i++) 
    {
        clipSlice (i, x, y, radius);
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : clipSlice
//
// Description : clips or splits the chunks on a slice depending on whether they
//               are within a certain distance from the specified point.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::clipSlice
(
    int                        slice,
    float                      x,
    float                      y,
    float                      radius
)
{
    float newHeight;

    list<sLandChunk>::iterator iterator;

    // For each chunk on this slice
    for (iterator  = _landChunks[slice].begin ();
         iterator != _landChunks[slice].end ();) 
    {
        float x1 = getWorldXFromSlice (slice);
        float x2 = getWorldXFromSlice (slice + 1);

        int state1 = checkWithinBlastRange (x, y, radius, 
                                            x1, (*iterator).maxHeight1);
        int state2 = checkWithinBlastRange (x, y, radius, 
                                            x2, (*iterator).maxHeight2);

        int state3;
        int state4;

        if ((*iterator).minHeight1 > -7.0f)
        {
            state3 = checkWithinBlastRange (x, y, radius,
                                                x1, (*iterator).minHeight1);
            state4 = checkWithinBlastRange (x, y, radius,
                                                x2, (*iterator).minHeight2);
        }
        else
        {
            // If below the minimum landscape destruction height, the bottom of
            // the chunk is always marked as below the blast.
            state3 = state4 = 1;
        }

        bool wasLinkedToNext = (*iterator).linkedToNext;

        if (wasLinkedToNext)
        {
            if (   (state1 == 0 && state2 != 3 && state4 == 3) 
                || (state2 == 0 && state1 != 3 && state3 == 3))
            {
                while (iterator->linkedToNext)
                {
                    ++iterator;
                }
                ++iterator;
                continue;
            }
        }

        int needSplit = 0;
        
        list<sLandChunk>::iterator superblock = getSuperblock(slice, iterator);

        switch ((state2 << 2) | state1)
        {
        case 3:
        case 6:
        case 7:
            newHeight = clipHeight (x, y, radius, x1, false);
            calculateColour (&(*iterator).maxColour1,
                             &(*iterator).minColour1,
                             (*iterator).maxHeight1,
                             (*iterator).minHeight1,
                             newHeight,
                             true);
            (*iterator).maxHeight1 = newHeight;
            break;
            
        case 9:
        case 12:
        case 13:
            newHeight = clipHeight (x, y, radius, x2, false);
            calculateColour (&(*iterator).maxColour2,
                             &(*iterator).minColour2,
                             (*iterator).maxHeight2,
                             (*iterator).minHeight2,
                             newHeight,
                             true);
            (*iterator).maxHeight2 = newHeight;
            break;
            
        case 10:
            needSplit++;
            // possible split of this chunk needed :-D
            break;
            
        case 11:
        case 14:
        case 15:
            newHeight = clipHeight (x, y, radius, x1, false);
            calculateColour (&(*iterator).maxColour1,
                             &(*iterator).minColour1,
                             (*iterator).maxHeight1,
                             (*iterator).minHeight1,
                             newHeight,
                             true);
            (*iterator).maxHeight1 = newHeight;

            newHeight = clipHeight (x, y, radius, x2, false);
            calculateColour (&(*iterator).maxColour2,
                             &(*iterator).minColour2,
                             (*iterator).maxHeight2,
                             (*iterator).minHeight2,
                             newHeight,
                             true);
            (*iterator).maxHeight2 = newHeight;
            break;
            
        default:
            break;
        }

        switch ((state4 << 2) | state3)
        {
        case 5:
            // Possible Split of this chunk needed :-D
            needSplit++;
            break;
            
        case 6:
        case 12:
        case 14:
            newHeight = clipHeight (x, y, radius, x2, true);
            calculateColour (&(*iterator).maxColour2,
                             &(*iterator).minColour2,
                             (*iterator).maxHeight2,
                             (*iterator).minHeight2,
                             newHeight,
                             false);
            (*iterator).minHeight2   = newHeight;

            if ((*iterator).linkedToNext)
            {                
                if (state3 == 2)
                {
                    newHeight = clipHeight (x, y, radius, x1, true); 
                    (*iterator).minHeight1   = newHeight;
                }

                list<sLandChunk>::iterator nextSuperblock = iterator;

                nextSuperblock++;

                (*nextSuperblock).fallingState 
                    = (*superblock).fallingState;

                (*nextSuperblock).waitForFallTime 
                    = (*superblock).waitForFallTime;

                (*nextSuperblock).fallingSpeed 
                    = (*superblock).fallingSpeed;
            }

            (*iterator).linkedToNext = false;

            if (!(*superblock).fallingState)
            {
                (*superblock).fallingState    = true;
                (*superblock).waitForFallTime = _fallPause;
                (*superblock).fallingSpeed    = 0.0f;
            }
            break;
            
        case 7:
        case 13:
        case 15:
            newHeight = clipHeight (x, y, radius, x1, true);
            calculateColour (&(*iterator).maxColour1,
                             &(*iterator).minColour1,
                             (*iterator).maxHeight1,
                             (*iterator).minHeight1,
                             newHeight,
                             false);
            (*iterator).minHeight1   = newHeight;

            newHeight = clipHeight (x, y, radius, x2, true);
            calculateColour (&(*iterator).maxColour2,
                             &(*iterator).minColour2,
                             (*iterator).maxHeight2,
                             (*iterator).minHeight2,
                             newHeight,
                             false);
            (*iterator).minHeight2 = newHeight;

            if ((*iterator).linkedToNext)
            {                
                list<sLandChunk>::iterator nextSuperblock = iterator;

                nextSuperblock++;

                (*nextSuperblock).fallingState 
                    = (*superblock).fallingState;

                (*nextSuperblock).waitForFallTime 
                    = (*superblock).waitForFallTime;

                (*nextSuperblock).fallingSpeed 
                    = (*superblock).fallingSpeed;
            }

            (*iterator).linkedToNext = false;

            if (!(*superblock).fallingState)
            {
                (*superblock).fallingState    = true;
                (*superblock).waitForFallTime = _fallPause;
                (*superblock).fallingSpeed    = 0.0f;                
            }
            break;
            
        case 3:
        case 9:
        case 11:
            newHeight = clipHeight (x, y, radius, x1, true);
            calculateColour (&(*iterator).maxColour1,
                             &(*iterator).minColour1,
                             (*iterator).maxHeight1,
                             (*iterator).minHeight1,
                             newHeight,
                             false);
            (*iterator).minHeight1 = newHeight;

            if ((*iterator).linkedToNext)
            {                
                if (state4 == 2)
                {
                    newHeight = clipHeight (x, y, radius, x2, true); 
                    (*iterator).minHeight2   = newHeight;
                }

                list<sLandChunk>::iterator nextSuperblock = iterator;

                nextSuperblock++;

                (*nextSuperblock).fallingState 
                    = (*superblock).fallingState;

                (*nextSuperblock).waitForFallTime 
                    = (*superblock).waitForFallTime;

                (*nextSuperblock).fallingSpeed 
                    = (*superblock).fallingSpeed;
            }

            (*iterator).linkedToNext = false;

            if (!(*superblock).fallingState)
            {
                (*superblock).fallingState    = true;
                (*superblock).waitForFallTime = _fallPause;
                (*superblock).fallingSpeed    = 0.0f;                
            }
            break;
            
        default:
            break;
        }

        if (needSplit == 2) 
        {
            // Both the top and bottom of the chunk think we need to split it, 
            // so lets do it!
             
            sLandChunk newChunk;
            
            newChunk.maxHeight1 = (*iterator).maxHeight1;
            newChunk.maxColour1 = (*iterator).maxColour1;
            newChunk.maxHeight2 = (*iterator).maxHeight2;
            newChunk.maxColour2 = (*iterator).maxColour2;

            newHeight = clipHeight (x, y, radius, x1, true);
            newChunk.maxColour1 = (*iterator).maxColour1;
            newChunk.minColour1 = (*iterator).minColour1;
            calculateColour (&newChunk.maxColour1,
                             &newChunk.minColour1,
                             (*iterator).maxHeight1,
                             (*iterator).minHeight1,
                             newHeight,
                             false);
            newChunk.minHeight1 = newHeight;

            newHeight = clipHeight (x, y, radius, x2, true);
            newChunk.maxColour2 = (*iterator).maxColour2;
            newChunk.minColour2 = (*iterator).minColour2;
            calculateColour (&newChunk.maxColour2,
                             &newChunk.minColour2,
                             (*iterator).maxHeight2,
                             (*iterator).minHeight2,
                             newHeight,
                             false);
            newChunk.minHeight2 = newHeight;
            
            newHeight = clipHeight (x, y, radius, x1, false);
            calculateColour (&(*iterator).maxColour1,
                             &(*iterator).minColour1,
                             (*iterator).maxHeight1,
                             (*iterator).minHeight1,
                             newHeight,
                             true);
            (*iterator).maxHeight1 = newHeight;

            newHeight = clipHeight (x, y, radius, x2, false);
            calculateColour (&(*iterator).maxColour2,
                             &(*iterator).minColour2,
                             (*iterator).maxHeight2,
                             (*iterator).minHeight2,
                             newHeight,
                             true);
            (*iterator).maxHeight2 = newHeight;

            newChunk.linkedToNext = false;
            newChunk.fallingState = false;

            _landChunks[slice].insert (iterator, newChunk);

            if (superblock == iterator)
            {
                superblock--;
            }

            // 'superblock' now points to the head of the superblock above the 
            // split.

            if (!(*superblock).fallingState)
            {
                (*superblock).fallingState    = true;
                (*superblock).waitForFallTime = _fallPause;
                (*superblock).fallingSpeed    = 0.0f;
            }
            else
            {
                // the block we split was already falling, so copy the 
                // attributes from the above superblock to the below one.
                (*iterator).fallingState    = (*superblock).fallingState;
                (*iterator).waitForFallTime = (*superblock).waitForFallTime;
                (*iterator).fallingSpeed    = (*superblock).fallingSpeed;
            }
        }
       
        // Check that we don't have a crossed over chunk (e.g. top lower than 
        // bottom. If we have, then the chunk was completely destroyed, so 
        // remove it.)
        if (((*iterator).minHeight1 > (*iterator).maxHeight1) ||
            ((*iterator).minHeight2 > (*iterator).maxHeight2))
        {
            if (wasLinkedToNext)
            {
                list<sLandChunk>::iterator nextIterator = iterator;
                ++nextIterator;

                nextIterator->maxHeight1 = iterator->maxHeight1;
                nextIterator->maxHeight2 = iterator->maxHeight2;
            }

            // Chunk is crossed over, delete it from the list
            iterator = _landChunks[slice].erase (iterator);  
        }
        else
        {
            ++iterator;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : checkWithinBlastRange
//
// Description : returns one of several values depending on the position of a 
//               point in relation to a blast radius 
//
////////////////////////////////////////////////////////////////////////////////
int
cLandscape::checkWithinBlastRange
(
    float blastX,
    float blastY,
    float radius,
    float x,
    float y
)
{
    if (x > (blastX + radius) || (x < (blastX - radius)))
    {
        // Not within the horizontal reach of the blast
        return 0;
    }
    else
    {
        if ((sqr (x - blastX) + sqr (y - blastY)) < sqr (radius))
        {
            // Inside the blast radius
            return 3;
        }
        else
        {
            if (blastY > y) 
            {
                // Below the blast radius
                return 1;
            }
            else
            {
                // Above the blast radius
                return 2;
            }
        }
    }

}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : clipHeight
//
// Description : For a point within a blast radius, returns a clipped value at 
//               the edge of the blast radius, either directly above or below 
//               the point depending on what the 'up' parameter is set to.
//
////////////////////////////////////////////////////////////////////////////////
float
cLandscape::clipHeight
(
 float  blastX,
 float  blastY,
 float  blastRadius,
 float  x,
 bool   up
)
{
    if (up)
    {
        return (blastY + sqrt (sqr (blastRadius) - sqr (x - blastX)));
    }
    else
    {
        float newY = blastY - sqrt (sqr (blastRadius) - sqr (x - blastX));
        if (newY < -7.0f) 
        {
            // Never clip to below -7.0, this is the minimum landscape height
            return (-7.0f);
        }
        else
        {
            return (blastY - sqrt (sqr (blastRadius) - sqr (x - blastX)));
        }
    }
}        

////////////////////////////////////////////////////////////////////////////////
//
// Function    : moveToGround
//
// Description : Given a point, returns the y value of the first point on the 
//               terrain exactly below it.
//
////////////////////////////////////////////////////////////////////////////////
float
cLandscape::moveToGround
(
    float x,
    float y
)
{
    int   slice = getSliceFromWorldX (x);
    float xOffset = getSliceOffsetFromWorldX (x);

    float height = 0.0f;
    float oldHeight = -1000.0f;

    list<sLandChunk>::iterator iterator;

    // check each chunk
    for (iterator  = _landChunks[slice].begin ();
         iterator != _landChunks[slice].end ();
         iterator++)
    {
        int state = inChunk (iterator, xOffset, y);

        if (state != 2) 
        {
            height = ((*iterator).maxHeight1 * (1.0f - xOffset)) +
                     ((*iterator).maxHeight2 * xOffset);

            if (state == 0)
            {
                break;
            }

            if ((y - height) < (y - oldHeight))
            {
                oldHeight = height;
            }
            else
            {
                height = oldHeight;
            }
        }
    }

    return (height);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : moveToGroundAtAngle
//
// Description : Same as previous function but instead of tracing straight down,
//               it traces down at the specified angle. This is much more
//               complex :-)
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::moveToGroundAtAngle
(
    float * x,
    float * y,
    float   angle
)
{
    int   slice   = getSliceFromWorldX (*x);
    float xOffset = getSliceOffsetFromWorldX (*x);
    bool  done    = false;

    while (!done)
    {
        list<sLandChunk>::iterator iterator;
        
        bool found = false;

        for (iterator  = _landChunks[slice].begin ();
             iterator != _landChunks[slice].end ();
             iterator++)
        {
            int state = inChunk (iterator, xOffset, *y);
            
            if (state == 0)
            {
                found = true;

                if (angle == 0.0f)
                {
                    *y = ((*iterator).maxHeight1 * (1.0f - xOffset)) +
                         ((*iterator).maxHeight2 * xOffset);

                    done = true;
                }
                else if (angle > 0.0f)
                {
                    float newY = *y + xOffset / tan (angle);
                    
                    if (newY > (*iterator).maxHeight1)
                    {
                        findTopChunkIntersect (iterator, 
                                               0.0f, newY, 
                                               xOffset, *y, 
                                               x, y);

                        *x   += (float)slice;
                        *x    = getWorldXFromSliceX (*x);
                        done = true;
                    }
                    else
                    {
                        *x      = getWorldXFromSlice (slice);
                        *y      = newY;
                        xOffset = 1.0f;
                        slice--;
                    }
                }
                else
                {
                    float newY = *y + (1.0 - xOffset) / tan (-angle);

                    if (newY > (*iterator).maxHeight2)
                    {
                        findTopChunkIntersect (iterator, 
                                               1.0f, newY, 
                                               xOffset, *y, 
                                               x, y);

                        *x   += (float)slice;
                        *x    = getWorldXFromSliceX (*x);
                        done  = true;
                    }
                    else
                    {
                        *x      = getWorldXFromSlice (slice + 1);
                        *y      = newY;
                        xOffset = 0.0f; 
                        slice++;
                    }
                }
                
                break;
            }
        }

        if (!found)
        {
            done = true;
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : inChunk
//
// Description : Returns whether a point is within a chunk (note: the x 
//               coordinate is an offset from the chunk's slice's x position)
//
////////////////////////////////////////////////////////////////////////////////
int
cLandscape::inChunk 
(
    list<sLandChunk>::iterator chunk,
    float                      xOffset,
    float                      y
)
{
    float maxHeight = ((*chunk).maxHeight1 * (1.0f - xOffset)) +
                      ((*chunk).maxHeight2 * xOffset);

    float minHeight = ((*chunk).minHeight1 * (1.0f - xOffset)) +
                      ((*chunk).minHeight2 * xOffset);

    if (y > maxHeight) 
    {
        // point is above the chunk
        return 1;
    }
    else if (y < minHeight)
    {
        // point is below the chunk
        return 2;
    }

    // point is inside the chunk
    return 0;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : findTopChunkIntersect
//
// Description : Calculates the coordinates at which a line would cross the top
//               edge of a chunk.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::findTopChunkIntersect
(
    list<sLandChunk>::iterator   chunk,
    float                        xOffset1,
    float                        y1,
    float                        xOffset2,
    float                        y2,
    float                      * collisionX, // OUT
    float                      * collisionY  // OUT
)
{
    float projectileGradiant = (y2 - y1) / (xOffset2 - xOffset1);
    float sliceGradiant      = (*chunk).maxHeight2 - (*chunk).maxHeight1;
   
    if (projectileGradiant > 1.0f || projectileGradiant < -1.0f)
    {
        *collisionX = ((((*chunk).maxHeight1 - y1) / projectileGradiant) + 
                       xOffset1) / 
            (1.0f - sliceGradiant / projectileGradiant);
    }
    else
    {
        *collisionX = ((*chunk).maxHeight1 - y1 + projectileGradiant * 
                       xOffset1) / 
            (projectileGradiant - sliceGradiant);
    }
    
    *collisionY = (*collisionX * sliceGradiant) + (*chunk).maxHeight1;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : findBottomChunkIntersect
//
// Description : Calculates the coordinates at which a line would cross the 
//               bottom edge of a chunk.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::findBottomChunkIntersect
(
    list<sLandChunk>::iterator   chunk,
    float                        xOffset1,
    float                        y1,
    float                        xOffset2,
    float                        y2,
    float                      * collisionX, // OUT
    float                      * collisionY  // OUT
)
{
    float projectileGradiant = (y2 - y1) / (xOffset2 - xOffset1);
    float sliceGradiant      = (*chunk).minHeight2 - (*chunk).minHeight1;

    if (projectileGradiant > 1.0f || projectileGradiant < -1.0f)
    {
        *collisionX = ((((*chunk).minHeight1 - y1) / projectileGradiant) 
                       + xOffset1) /
            (1.0f - sliceGradiant / projectileGradiant);
    }
    else
    {
        *collisionX = ((*chunk).minHeight1 - y1 + projectileGradiant * xOffset1)
            /
            (projectileGradiant - sliceGradiant);
    }
        
    *collisionY = (*collisionX * sliceGradiant) + (*chunk).minHeight1;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : IntersectChunk
//
// Description : Works out the intersection point between a line and any chunks
//               on a slices.
//
////////////////////////////////////////////////////////////////////////////////
bool
cLandscape::intersectChunk
(    
    float   xOffset1,
    float   y1,
    float   xOffset2,
    float   y2,
    int     slice,
    float * collisionX,                  // OUT
    float * collisionY                   // OUT
)
{

    list<sLandChunk>::iterator chunk;

    for (chunk  = _landChunks[slice].begin ();
         chunk != _landChunks[slice].end ();
         chunk++)
    {
        int state1 = inChunk (chunk, xOffset1, y1);
        int state2 = inChunk (chunk, xOffset2, y2);

        if (state1 == 0)
        {
            if (collisionX)
            {
                // Test started inside a chunk so mark it as a collision
                *collisionX = xOffset1 + slice;
                *collisionX = getWorldXFromSliceX (*collisionX);
                *collisionY = y1;
            }

            return (true);
        }
        else if (state1 != state2)
        {
            if (state1 == 1) 
            {
                if (collisionX)
                {
                    findTopChunkIntersect (chunk, 
                                           xOffset1, 
                                           y1, 
                                           xOffset2, 
                                           y2, 
                                           collisionX,
                                           collisionY);
                    
                    *collisionX += (float)slice;
                    *collisionX = getWorldXFromSliceX (*collisionX);
                }

                return (true);
            }
            else
            {
                if (collisionX)
                {
                    findBottomChunkIntersect (chunk,
                                              xOffset1, 
                                              y1, 
                                              xOffset2, 
                                              y2, 
                                              collisionX, 
                                              collisionY);
                    
                    *collisionX += (float)slice;
                    *collisionX = getWorldXFromSliceX (*collisionX);
                }
                return (true);
            }    
        }
    }    

    return (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : groundCollision
//
// Description : Work out the first intersect point between a line and the
//               entire terrain. Returns 'false' if the line doesn't intersect 
//               the terrain.
//               if collisionX or collisionY are set to NULL, the function will
//               not calculate an intersection point, only whether an intersect
//               occured.
//
////////////////////////////////////////////////////////////////////////////////
bool
cLandscape::groundCollision
(
    float x1,
    float y1,
    float x2,
    float y2,
    float * collisionX, // OUT (if not NULL)
    float * collisionY  // OUT (if not NULL)
)
{
    int index1 = getSliceFromWorldX (x1);
    int index2 = getSliceFromWorldX (x2);

    float oldY;

    if (index1 < index2) 
    {
        float lengthX = x2 - x1;
        float lengthY = y2 - y1;

        float x = getWorldXFromSlice (index1 + 1);
        float y = y1 + (((x - x1) / lengthX) * lengthY);

        if (intersectChunk (getSliceOffsetFromWorldX (x1), 
                            y1, 
                            1.0f,
                            y,
                            index1,
                            collisionX,
                            collisionY))
        {
            return (true);
        }
            
        for (int i = index1 + 1; i < index2; i++)
        {

            x    += 1 / _sliceToWorldConversion;
            oldY  = y;
            y     = y1 + (((x - x1) / lengthX) * lengthY);
            
            if (intersectChunk (0.0f,
                                oldY,
                                1.0f,
                                y,
                                i,
                                collisionX,
                                collisionY))
            {
                return (true);
            }
        }

        if (intersectChunk (0.0f,
                            y,
                            getSliceOffsetFromWorldX (x2),
                            y2,
                            index2,
                            collisionX,
                            collisionY))
        {
            return (true);
        }

    }
    else if (index2 < index1)
    {
        float lengthX = x1 - x2;
        float lengthY = y1 - y2;

        float x = getWorldXFromSlice (index1);
        float y = y2 + (((x - x2) / lengthX) * lengthY);

        if (intersectChunk (getSliceOffsetFromWorldX (x1), 
                            y1, 
                            0.0f,
                            y,
                            index1,
                            collisionX,
                            collisionY))
        {
            return (true);
        }

        for (int i = index1 - 1; i > index2; i--)
        {
            x    -= 1 / _sliceToWorldConversion;
            oldY  = y;
            y     = y2 + (((x - x2) / lengthX) * lengthY);

            if (intersectChunk (1.0f,
                                oldY,
                                0.0f,
                                y,
                                i,
                                collisionX,
                                collisionY))
            {
                return (true);
            }
        }

        if (intersectChunk (1.0f,
                            y,
                            getSliceOffsetFromWorldX (x2),
                            y2,
                            index2,
                            collisionX,
                            collisionY))
        {
            return (true);
        }
    }
    else
    {
        // Movement confined to a single slice

        if (intersectChunk (getSliceOffsetFromWorldX (x1),
                            y1,
                            getSliceOffsetFromWorldX (x2),
                            y2,
                            index1,
                            collisionX,
                            collisionY))
        {
            return (true);
        }
    }

    // If we've got this far, obviously we haven't hit anything.
    return (false);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : calculateColour
//
// Description : Not Used.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::calculateColour
(
    sColour * top,
    sColour * bottom,
    float     maxX,
    float     minX,
    float     x,
    bool      calcTop // decides whether the top or bottom is changed
)
{
    float ratio = (x - minX) / (maxX - minX);
 
    if (calcTop) 
    {
        top->r = bottom->r + (ratio * (top->r - bottom->r));
        top->g = bottom->g + (ratio * (top->g - bottom->g));
        top->b = bottom->b + (ratio * (top->b - bottom->b));
    }
    else
    {
        bottom->r = bottom->r + (ratio * (top->r - bottom->r));
        bottom->g = bottom->g + (ratio * (top->g - bottom->g));
        bottom->b = bottom->b + (ratio * (top->b - bottom->b));
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : dropTerrain
//
// Description : lowers the whole terrain by the ammount specified.
//               The terrain cannot go below the minimum height.
//
////////////////////////////////////////////////////////////////////////////////
void
cLandscape::dropTerrain
(
    float ammount
)
{
    for (int i = 0; i < _numOfSlices; i++)
    {
        list<sLandChunk>::iterator iterator;

        for (iterator  = _landChunks[i].begin ();
             iterator != _landChunks[i].end ();
             iterator++)
        {
            (*iterator).maxHeight1 -= ammount;
            (*iterator).maxHeight2 -= ammount;
            //(*iterator).minHeight1 -= ammount;
            //(*iterator).minHeight2 -= ammount;
            
            if ((*iterator).maxHeight1 < -7.0f)
            {
                (*iterator).maxHeight1 = -7.0f;
            }
            
            if ((*iterator).maxHeight2 < -7.0f)
            {
                (*iterator).maxHeight2 = -7.0f;
            }
            
            if ((*iterator).maxHeight1 > -7.0f)
            {
                (*iterator).minHeight1 -= ammount;
            }
            
            if ((*iterator).maxHeight1 > -7.0f)
            {
                (*iterator).minHeight2 -= ammount;
            }
        }
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getSuperblock
//
// Description : 
//
////////////////////////////////////////////////////////////////////////////////
list<cLandscape::sLandChunk>::iterator
cLandscape::getSuperblock
(
    int slice,
    list<sLandChunk>::iterator block
)
{
    if (block == _landChunks[slice].begin ())
    {
        return (block);
    }

    block--;

    while (block != _landChunks[slice].begin () && (*block).linkedToNext)
    {
        block--;
    }

    if (block == _landChunks[slice].begin () && (*block).linkedToNext)
    {
        return (block);
    }

    block++;

    return (block);
}
