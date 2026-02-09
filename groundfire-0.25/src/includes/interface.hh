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
//   File name : interface.hh
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
#ifndef __INTERFACE_HH__
#define __INTERFACE_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <GLFW/glfw3.h>
#include "stb_image.h"

////////////////////////////////////////////////////////////////////////////////
// Exception Classes
////////////////////////////////////////////////////////////////////////////////
class eInterface {};

#define MAX_TEXTURES 16

// A useful function for storing a colour definition
struct sColour
{
    sColour () {}
    sColour (float red, float green, float blue) : r(red), g(green), b(blue) {}

    bool operator== (const sColour & c) const
        {
            return (r == c.r && g == c.g && b == c.b);
        }

    float r;
    float g;
    float b;
};

class cInterface
{
    // Make the resize callback function a friend
    friend void resizeView (GLFWwindow* window, int width, int height);

public:
    cInterface (int width, int height, bool fullscreen);
    ~cInterface ();

    void startDraw       (void);
    void endDraw         (void);

    bool shouldClose     () { return glfwWindowShouldClose(_window); }

    void getMousePos     (float & x, float & y) { x = _mouseX; y = _mouseY; }

    bool getMouseButton  (int button) { return (glfwGetMouseButton (_window, button)); }

    bool getKey          (int keycode) { return (glfwGetKey (_window, keycode)); }

    bool  getJoystickButton (int joyDevice, int button);

    float getJoystickAxis (int joyDevice, int axis);

    void defineTextures  (int numOfTextures);
    bool loadTexture     (char * filename, int textureNum);
    void setTexture      (int texture)
        {
            glBindTexture (GL_TEXTURE_2D, _textures[texture]);
        }

    // Get the settings for the window
    bool getWindowSettings (int & width, int & height) const
        {
            width  = _width;
            height = _height;

            return (_fullscreen);
        }

    void enableMouse      (bool enable) { _mouseEnabled = enable; }

    void changeWindow     (int  width, int  height, bool fullscreen);

    int  numOfControllers (void) const
        {
            return (_numOfControllers);
        }

    static cInterface * currentInterface;

    void offsetViewport (float xOffset, float yOffset);

private:
    void drawMouse ();

    void reloadTextures ();

    struct sJoystick
    {
        float         axis[4];
        unsigned char buttons[10];
    };

    bool  _fullscreen;
    int   _width;
    int   _height;
    bool  _mouseEnabled;
    float _mouseX;
    float _mouseY;

    sJoystick     _joysticks[8];
    int           _numOfControllers;

    GLuint      * _textures;
    char       ** _textureFiles;
    int           _numOfTextures;
    
    GLFWwindow*   _window;
};

#endif // __INTERFACE_HH__
