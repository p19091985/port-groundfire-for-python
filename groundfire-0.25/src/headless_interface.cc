////////////////////////////////////////////////////////////////////////////////
//
//               Groundfire Headless Interface
//
////////////////////////////////////////////////////////////////////////////////
//
// Description : Stub implementation of cInterface for headless testing.
//               Replaces interface.cc during test compilation.
//
////////////////////////////////////////////////////////////////////////////////

#include "interface.hh"
#include "report.hh"
#include <string.h>
#include <iostream>

// Re-declare static member
cInterface * cInterface::currentInterface = NULL;

// Stub resize callback (unused but friendly)
void resizeView(GLFWwindow* window, int width, int height) {}

////////////////////////////////////////////////////////////////////////////////
// Constructor
////////////////////////////////////////////////////////////////////////////////
cInterface::cInterface(int width, int height, bool fullscreen)
    : _fullscreen(fullscreen), _width(width), _height(height), _window(NULL)
{
    // Need to init GLFW for timer
    extern int glfwInit(void);
    glfwInit();
    
    cInterface::currentInterface = this;
    _numOfTextures = 0;
    _textures = NULL;
    _numOfControllers = 0;
    _mouseEnabled = false;
    _mouseX = 0.0f;
    _mouseY = 0.0f;
    
    // Initialize dummy joysticks
    for (int i = 0; i < 8; ++i) {
        for (int j = 0; j < 4; ++j) _joysticks[i].axis[j] = 0.0f;
        for (int j = 0; j < 10; ++j) _joysticks[i].buttons[j] = 0;
    }
}

////////////////////////////////////////////////////////////////////////////////
// Destructor
////////////////////////////////////////////////////////////////////////////////
cInterface::~cInterface()
{
    if (_textures) {
        delete[] _textures;
        _textures = NULL;
    }
    if (_textureFiles) {
        for (int i = 0; i < _numOfTextures; i++) {
            if (_textureFiles[i]) delete[] _textureFiles[i];
        }
        delete[] _textureFiles;
        _textureFiles = NULL;
    }
}

////////////////////////////////////////////////////////////////////////////////
// Drawing Stubs
////////////////////////////////////////////////////////////////////////////////
void cInterface::startDraw() { }
void cInterface::endDraw() { }
void cInterface::drawMouse() { }

void cInterface::offsetViewport(float xOffset, float yOffset) { }
void cInterface::changeWindow(int width, int height, bool fullscreen) {
    _width = width;
    _height = height;
    _fullscreen = fullscreen;
}

////////////////////////////////////////////////////////////////////////////////
// Input Stubs
////////////////////////////////////////////////////////////////////////////////
bool cInterface::getJoystickButton(int joyDevice, int button) { return false; }
float cInterface::getJoystickAxis(int joyDevice, int axis) { return 0.0f; }

////////////////////////////////////////////////////////////////////////////////
// Texture Stubs
////////////////////////////////////////////////////////////////////////////////
void cInterface::defineTextures(int numOfTextures)
{
    _numOfTextures = numOfTextures;
    _textures = new GLuint[numOfTextures]; // Dummy IDs
    _textureFiles = new char *[numOfTextures];
    for (int i = 0; i < numOfTextures; i++) {
        _textureFiles[i] = NULL;
        _textures[i] = i; // simple ID
    }
}

bool cInterface::loadTexture(char * filename, int textureNum)
{
    // Headless: Just record the name, don't load actual image
    if (_textureFiles[textureNum]) delete[] _textureFiles[textureNum];
    _textureFiles[textureNum] = new char[strlen(filename) + 1];
    strcpy(_textureFiles[textureNum], filename);
    return true;
}

void cInterface::reloadTextures() {}
