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
//   File name : inifile.cc
//
//          By : Tom Russell
//
//        Date : 25-Feb-04
//
// Description : Generic module to handle reading and writing ini files. 
//
//               NOTE : The writing of ini files is currently untested!
//
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <fstream>
#include <stdio.h>
#ifdef DEBUG
#include <windows.h>
#endif
#include "inifile.hh"

////////////////////////////////////////////////////////////////////////////////
// Public Member Functions
////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////
//
// Function    : cReadIniFile
//
// Description : Constructor
//
////////////////////////////////////////////////////////////////////////////////
cReadIniFile::cReadIniFile
(
    string const & configFile
) 
{
    ifstream file (configFile.c_str ());

    if (!file)
    {
        return;
    }
    
    string line;
    string name;
    string value;
    string inSection;
    int    posEqual;

    while (getline (file, line))
    {
        if (!line.length ()) continue;
        
        // Ignore comment lines
        if (line[0] == '#') continue;
        if (line[0] == ';') continue;
        
        // A new section, record it.
        if (line[0] == '[')
        {
            inSection = line.substr (1, line.find (']') - 1);
            continue;
        }
        
        // get a value
        posEqual = line.find ('=');

        name  = line.substr (0, posEqual);
        value = line.substr (posEqual + 1);

        // Strip whitespace from the beginning and end of the strings
        name.erase  (0, name.find_first_not_of ("\t "));
        name.erase  (   name.find_last_not_of ("\t ") + 1);
        value.erase (0, value.find_first_not_of ("\t "));
        value.erase (   value.find_last_not_of ("\t ") + 1);

#ifdef DEBUG
        OutputDebugString (inSection.c_str ());
        OutputDebugString (name.c_str ());
        OutputDebugString (value.c_str ());
        OutputDebugString ("\n");
#endif
        
        // Insert this entry into the map.
        _entries[inSection + '/' + name] = value;
    }
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getFloat
//
// Description : Returns an ini file entry as a floating point number
//
////////////////////////////////////////////////////////////////////////////////
float
cReadIniFile::getFloat
(
    string const & section,
    string const & entry,
    float          defaultValue
) 
const
{
    map<string,string>::const_iterator ci 
        = _entries.find (section + '/' + entry);
    
    if (ci == _entries.end ()) 
    {
        return (defaultValue);
    }

    return ((float)atof (ci->second.c_str ()));
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getInt
//
// Description : Returns an ini file entry as a integer number.
//
////////////////////////////////////////////////////////////////////////////////
int
cReadIniFile::getInt
(
    string const & section,
    string const & entry,
    int            defaultValue
) 
const
{
    map<string,string>::const_iterator ci 
        = _entries.find (section + '/' + entry);
    
    if (ci == _entries.end ()) 
    {
        return (defaultValue);
    }

    return (atoi (ci->second.c_str ()));
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : getString
//
// Description : Returns an ini file entry as a string.
//
////////////////////////////////////////////////////////////////////////////////
string
cReadIniFile::getString
(
    string const & section,
    string const & entry,
    string         defaultValue
) 
const
{
    map<string,string>::const_iterator ci 
        = _entries.find (section + '/' + entry);
    
    if (ci == _entries.end ()) 
    {
        return (defaultValue);
    }
    
    return (ci->second);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : addSection
//
// Description : Adds a new section to an ini file.
//
////////////////////////////////////////////////////////////////////////////////
void
cWriteIniFile::addSection
(
    string const & section
)
{
    map<string, string> newEntry;
    _entries[section] = newEntry;
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : putFloat
//
// Description : Puts a floating point value entry into the ini file
//
////////////////////////////////////////////////////////////////////////////////
bool
cWriteIniFile::putFloat
(
    string const & section,
    string const & entry,
    float          value
)
{
    map<string,map<string, string> >::iterator ci = _entries.find (section);

    if (ci == _entries.end ())
    {
        return (false);
    }

    char buffer[16];
    snprintf (buffer, 16, "%f", value);

    ci->second[entry] = buffer;

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : putInt
//
// Description : Puts an integer value entry into the ini file
//
////////////////////////////////////////////////////////////////////////////////
bool
cWriteIniFile::putInt
(
    string const & section,
    string const & entry,
    int            value
)
{
    map<string,map<string, string> >::iterator ci = _entries.find (section);

    if (ci == _entries.end ())
    {
        return (false);
    }

    ci->second[entry] = value;

    return (true);
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : putString
//
// Description : puts a string value into the ini file
//
////////////////////////////////////////////////////////////////////////////////
bool
cWriteIniFile::putString
(
    string const & section,
    string const & entry,
    string const & value
)
{
    map<string,map<string, string> >::iterator ci = _entries.find (section);

    if (ci == _entries.end ())
    {
        return (false);
    }

    ci->second[entry] = value;

    return (true);    
}

////////////////////////////////////////////////////////////////////////////////
//
// Function    : write
//
// Description : Writes out the ini file to disk.
//
////////////////////////////////////////////////////////////////////////////////
void 
cWriteIniFile::write 
(
    string const & configFile // The file name of the ini file.
)
{
    ofstream file (configFile.c_str ());

    map<string, map<string, string> >::iterator i;

    for (i = _entries.begin (); i != _entries.end (); i++)
    {
        file << "[" << i->first << "]" << endl;

        map<string, string>::iterator j;

        for (j = i->second.begin (); j != i->second.end (); j++)
        {
            file << j->first << "=" << j->second << endl; 
        }

        file << endl;
    }
}
