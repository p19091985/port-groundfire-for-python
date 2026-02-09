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
//   File name : interface.cc
//
//          By : Tom Russell
//
//        Date : 07-Sep-02
//
// Description : Handles the Graphics interface with the OS using the GLFW 
//               framework. Also uses GLFW to interface with the controller 
//               devices.
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#define STB_IMAGE_IMPLEMENTATION
#include "interface.hh"
#include "report.hh"
#include <string.h>

cInterface * cInterface::currentInterface = NULL;

////////////////////////////////////////////////////////////////////////////////
//
// Function    : resizeView
//
// Description : Callback function for resizing the window
//
////////////////////////////////////////////////////////////////////////////////
void resizeView
(
    GLFWwindow* window,
    int width,
    int height
)
{
    // Alter the OpenGL viewport to match the new window size.
    glViewport (0, 0, width, height);

    // reset the projection matrix
    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    glOrtho (-10.0, 10.0, -7.5, 7.5, 0.0, 1000.0);

    glMatrixMode (GL_MODELVIEW);						
    glLoadIdentity (); 
    
    // Set the width of openGL lines according to the resolution. These are 
    // mainly used for machine gun fire. At higher resolutions, a single pixel
    // width makes the bullets difficult to see so we increase the line width
    // to several pixels.
    if (width < 700)
    {
        glLineWidth (1.0f);
    }
    else if (width < 1100)
    {
        glLineWidth (2.0f);
    }
    else
    {
        glLineWidth (3.0f);
    }

    // Inform the interface object of the new width and height.
    cInterface::currentInterface->_width  = width;
    cInterface::currentInterface->_height = height;
}

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cInterface
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cInterface::cInterface
(
    int  width,
    int  height,
    bool fullscreen
)
        : _fullscreen (fullscreen), _window(NULL)
{
    // 'currentInterface' is needed so that the resizeView callback function 
    // can talk to the interface object.
    cInterface::currentInterface = this;

    // initialse the GLFW framework.
    if (!glfwInit ())
    {
        report ("ERROR: Could not initialise graphics");
        throw eInterface ();
    }

    glfwWindowHint(GLFW_RED_BITS, 8);
    glfwWindowHint(GLFW_GREEN_BITS, 8);
    glfwWindowHint(GLFW_BLUE_BITS, 8);
    glfwWindowHint(GLFW_ALPHA_BITS, 8);
    glfwWindowHint(GLFW_DEPTH_BITS, 16);
    glfwWindowHint(GLFW_STENCIL_BITS, 0);
    glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);

    // Create a new window for the game.
    _window = glfwCreateWindow(width, height, "Groundfire", fullscreen ? glfwGetPrimaryMonitor() : NULL, NULL);

    if (!_window)
    {
        glfwTerminate ();
        report ("ERROR: Could not create window");
        throw eInterface ();
    }

    glfwMakeContextCurrent(_window);

    // Set the default parameters for the window
    glfwSetWindowSizeCallback (_window, resizeView);

    resizeView (_window, width, height);

    _width  = width;
    _height = height;

    // Set up the OpenGL settings that we will use.
    glDisable (GL_TEXTURE_2D);

    glShadeModel (GL_SMOOTH);
    // Clear screen to black.
    glClearColor (0.0f, 0.0f, 0.0f, 0.0f);

    glClearDepth (1.0f);
    glEnable (GL_DEPTH_TEST);
    glDepthFunc (GL_LEQUAL);

    // This is the alpha blending formula we will use for all the transparency 
    // in the game.
    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    _numOfTextures = 0;
    _textures      = NULL;

    // Find and catalogue all the joysticks connected to this computer.
    _numOfControllers = 2;

    for (int i = 0; i < GLFW_JOYSTICK_LAST; i++)
    {
        if (glfwJoystickPresent(i))
        {
            for (int j = 0; j < 10; j++)
            {
                _joysticks[i].buttons[j] = 0;
             }

            _numOfControllers++;
        }
    }

    _mouseEnabled = false;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : ~cInterface
//
// Description : Destructor
//
////////////////////////////////////////////////////////////////////////////////
cInterface::~cInterface
(
)
{
    if (_numOfTextures > 0) 
    {
        // Wipe all the textures from memory
        glDeleteTextures (_numOfTextures, _textures);
        delete[] _textures;

        for (int i = 0; i < _numOfTextures; i++)
        {
            if (_textureFiles[i])
            {
                delete[] _textureFiles[i];
            }
        }

        delete[] _textureFiles;

        _textures      = NULL;
        _numOfTextures = 0;
    }

    if (_window)
    {
        glfwDestroyWindow(_window);
        _window = NULL;
    }

    // Tell GLFW we have finished.
    glfwTerminate ();
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : startDraw
//
// Description : Does all the start-of-frame stuff.
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::startDraw
(
)
{ 
    glClear (GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : endDraw
//
// Description : Does all the end-of-frame stuff
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::endDraw
(
)
{
    // If the mouse cursor is enabled, draw it.
    if (_mouseEnabled)
    {
        drawMouse ();
    }

    // Display the new frame
    glfwSwapBuffers (_window);
    glfwPollEvents();

    // Update the controllers

    // for each joystick
    for (int i = 0; i < GLFW_JOYSTICK_LAST; i++)
    {
        if (glfwJoystickPresent(i)) {
             int count;
             const float* axes = glfwGetJoystickAxes(i, &count);
             if (count > 0) {
                 int toCopy = count > 4 ? 4 : count;
                 for (int k=0; k < toCopy; k++) _joysticks[i].axis[k] = axes[k];
             }

             const unsigned char* buttons = glfwGetJoystickButtons(i, &count);
             if (count > 0) {
                 int toCopy = count > 10 ? 10 : count;
                 for (int k=0; k < toCopy; k++) _joysticks[i].buttons[k] = buttons[k];
             }
        }
    }
    
    if (_mouseEnabled)
    {
        // Get the mouse's position
        double xpos, ypos;
        glfwGetCursorPos(_window, &xpos, &ypos);
        int screenX = (int)xpos;
        int screenY = (int)ypos;

        // Do we need to clip the mouse to the window edge?
        bool clipMouse = false; 

        if (screenX < 0)
        {
            screenX   = 0;
            clipMouse = true;
        }
        else if (screenX > _width - 1)
        {
            screenX   = _width - 1;
            clipMouse = true;
        }

        if (screenY < 0)
        {
            screenY   = 0;
            clipMouse = true;
        }
        else if (screenY > _height - 1)
        {
            screenY   = _height - 1;
            clipMouse = true;
        }

        // we only need to keep the mouse on the screen
        // if we are in fullscreen mode. In windowed mode it just follows the 
        // OS system's cursor.
        if (_fullscreen && clipMouse)
        {
            glfwSetCursorPos (_window, screenX, screenY);
        }

        _mouseX = -10.0f + ((float)screenX / (float)_width)  * 20.0f;
        _mouseY =  7.5f  - ((float)screenY / (float)_height) * 15.0f;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : changeWindow
//
// Description : sets a new resolution and fullscreen/windowed mode
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::changeWindow
(
    int  width,
    int  height,
    bool fullscreen
)
{
    if (_fullscreen || fullscreen) 
    {
        // Check that we actually need to change anything.
        if (width != _width || height != _height || (_fullscreen != fullscreen))
        {
            // we can't change the size of a fullscreen window so we must
            // destroy and recreate it.

            // Free up all textures first
            glDeleteTextures (_numOfTextures, _textures);

            if (_window) glfwDestroyWindow(_window);

            glfwWindowHint(GLFW_RED_BITS, 8);
            glfwWindowHint(GLFW_GREEN_BITS, 8);
            glfwWindowHint(GLFW_BLUE_BITS, 8);
            glfwWindowHint(GLFW_ALPHA_BITS, 8);
            glfwWindowHint(GLFW_DEPTH_BITS, 16);
            glfwWindowHint(GLFW_STENCIL_BITS, 0);
            glfwWindowHint(GLFW_RESIZABLE, GLFW_TRUE);

            _window = glfwCreateWindow(width, height, "Groundfire", fullscreen ? glfwGetPrimaryMonitor() : NULL, NULL);

            if (!_window)
            {
                glfwTerminate ();
                
                report ("Error: Could not change window");

                throw eInterface ();
            }

            glfwMakeContextCurrent(_window);

            glfwSetWindowSizeCallback (_window, resizeView);

            glDisable (GL_TEXTURE_2D);

            glShadeModel (GL_SMOOTH);
            glClearColor (0.0f, 0.0f, 0.0f, 0.0f);
            
            glClearDepth (1.0f);
            glEnable (GL_DEPTH_TEST);
            glDepthFunc (GL_LEQUAL);
            
            glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

            reloadTextures ();

            resizeView (_window, width, height);
        }
    }
    else
    {
        // Not fullscreen so just alter the size of the window
        glfwSetWindowSize (_window, width, height);
    }

    _width  = width;
    _height = height;
    _fullscreen = fullscreen;
}


////////////////////////////////////////////////////////////////////////////////
//
// Function    : getJoystickAxis
//
// Description : gets the current state of an axis for the specified joystick
//
////////////////////////////////////////////////////////////////////////////////
float
cInterface::getJoystickAxis
(
    int joystick,
    int axis
)
{
    return (_joysticks[joystick].axis[axis]);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getJoystickButton
//
// Description : Gets the current state of a button for the specified joystick
//
////////////////////////////////////////////////////////////////////////////////
bool
cInterface::getJoystickButton
(
    int joystick,
    int button
)
{
    return (_joysticks[joystick].buttons[button]);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : defineTextures
//
// Description : tells OpenGL to create enough space for the textures.
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::defineTextures
(
    int numOfTextures
)
{
    _numOfTextures = numOfTextures;
    _textures      = new GLuint[numOfTextures];
    _textureFiles  = new char *[numOfTextures]; 

    // blank the texture files
    for (int i = 0; i < numOfTextures; i++)
    {
        _textureFiles[i] = NULL;
    }
    
    glGenTextures (numOfTextures, _textures);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : loadTexture
//
// Description : loads a texture
//
////////////////////////////////////////////////////////////////////////////////
bool
cInterface::loadTexture
(
    char * filename,
    int    textureNum
)
{
    // TGA files may have origin at bottom-left, flip to match OpenGL convention
    stbi_set_flip_vertically_on_load(1);
    
    int width, height, channels;
    unsigned char* data = stbi_load(filename, &width, &height, &channels, 4); 

    if (!data)
    {
        report ("ERROR: Failed to load file '%s'", filename);
        return false;
    }

    // Setup the texture parameters.
    glBindTexture   (GL_TEXTURE_2D, _textures[textureNum]);
    // Set unpack alignment
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data);

    stbi_image_free(data);

    // Record the texture's filename in case we have to reload it later.
    if (_textureFiles[textureNum]) delete[] _textureFiles[textureNum];
    _textureFiles[textureNum] = new char[strlen (filename) + 1];
    strcpy (_textureFiles[textureNum], filename);

    return true;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : drawMouse
//
// Description : draws the mouse cursor
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::drawMouse
(
)
{
    int screenX, screenY;
    double xpos, ypos;

    glfwGetCursorPos(_window, &xpos, &ypos);
    screenX = (int)xpos;
    screenY = (int)ypos;

    // ScreenX and ScreenY are in pixels. Convert to game units

    float gameX = -10.0f + ((float)screenX / (float)_width)  * 20.0f;
    float gameY =  7.5f  - ((float)screenY / (float)_height) * 15.0f;

    glEnable (GL_TEXTURE_2D);

    glTexEnvf (GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
    glEnable  (GL_BLEND);
    glDisable (GL_DEPTH_TEST);

    // Use the mouse cursor texture
    setTexture (8);

    // Draw the mouse pointer shadow first
    glLoadIdentity ();
    glTranslatef (gameX - 0.06f, gameY - 0.06f, -8.0f);
    glColor4f (0.0f, 0.0f, 0.0f, 0.4f);

    glBegin (GL_QUADS);
    glTexCoord2f (0.0f,    0.0f); glVertex3f ( 0.0f, -0.6f, 0.0f);
    glTexCoord2f (0.6666f, 0.0f); glVertex3f ( 0.4f, -0.6f, 0.0f);
    glTexCoord2f (0.6666f, 1.0f); glVertex3f ( 0.4f,  0.0f, 0.0f);
    glTexCoord2f (0.0f,    1.0f); glVertex3f ( 0.0f,  0.0f, 0.0f);
    glEnd ();

    // Now draw the mouse pointer itself
    glLoadIdentity ();
    glTranslatef (gameX, gameY, -8.0f);
    glColor4f (1.0f, 1.0f, 1.0f, 1.0f);

    glBegin (GL_QUADS);
    glTexCoord2f (0.0f,    0.0f); glVertex3f ( 0.0f, -0.6f, 0.0f);
    glTexCoord2f (0.6666f, 0.0f); glVertex3f ( 0.4f, -0.6f, 0.0f);
    glTexCoord2f (0.6666f, 1.0f); glVertex3f ( 0.4f,  0.0f, 0.0f);
    glTexCoord2f (0.0f,    1.0f); glVertex3f ( 0.0f,  0.0f, 0.0f);
    glEnd ();

    glDisable (GL_TEXTURE_2D);
    glEnable  (GL_DEPTH_TEST);
    glDisable (GL_BLEND);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : reloadTextures
//
// Description : when the resolution of the screen is changed, we need to reload
//               all the textures.
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::reloadTextures
(
)
{
    stbi_set_flip_vertically_on_load(1);
    
    for (int i = 0; i < _numOfTextures; i++) 
    {
        int width, height, channels;
        unsigned char* data = stbi_load(_textureFiles[i], &width, &height, &channels, 4);
        
        if (!data) {
            report("ERROR: Failed to reload texture '%s'", _textureFiles[i]);
            continue;
        }
        
        glBindTexture   (GL_TEXTURE_2D, _textures[i]);
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
        glTexParameteri (GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data);
        
        stbi_image_free(data);
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : offsetViewport
//
// Description : moves the viewport offcentre by the specified ammount. Used to
//               create screen effects (such as for the earthquake.)
//
////////////////////////////////////////////////////////////////////////////////
void
cInterface::offsetViewport
(
    float xOffset,
    float yOffset
)
{
    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    glOrtho (-10.0 + xOffset, 10.0 + xOffset,
             -7.5  + yOffset,  7.5 + yOffset,
             0.0, 1000.0);

    glMatrixMode (GL_MODELVIEW);
}
