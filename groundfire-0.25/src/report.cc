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
//   File name : report.cc
//
//          By : Tom Russell
//
//        Date : 13-Apr-04
//
// Description : Report an error/debug info to the user
//
//
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include "report.hh"
#include <stdarg.h>
#include <stdio.h>
#ifdef WIN32
#  include <windows.h>
#endif

////////////////////////////////////////////////////////////////////////////////
// Defines
////////////////////////////////////////////////////////////////////////////////
#define MAX_STRING 256

////////////////////////////////////////////////////////////////////////////////
//
// Function    : report
//
// Description : Reports an error (usually a fatal one)
//
////////////////////////////////////////////////////////////////////////////////

void
report
(
    const char * format,
    ...
)
{
    va_list args;
    
    va_start (args, format);
    
#ifdef WIN32
    // On Windows only, display the error in a message box
    char buffer[MAX_STRING] = {'\0'};

    _vsnprintf (buffer, MAX_STRING - 1, format, args);

    MessageBox (NULL, buffer, "Groundfire", MB_OK);
#else
    // Default behaviour for all systems is to write the error to the console
    vprintf (format, args);
    printf ("\n");
#endif 

    va_end (args);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : debug
//
// Description : Outputs debug information
//
////////////////////////////////////////////////////////////////////////////////

void
debug
(
    const char * format,
    ...
)
{
    va_list args;
    
    va_start (args, format);  

#ifdef WIN32
    // On Windows only, send the debug information as a debug string.
    char buffer[MAX_STRING] = {'\0'};

    _vsnprintf (buffer, MAX_STRING - 1, format, args);

    OutputDebugString (buffer);
#else
    // Default behaviour for all systems is to write the debug information to
    // the console window
    vprintf (format, args);
    printf ("\n");
#endif

    va_end (args);
}
