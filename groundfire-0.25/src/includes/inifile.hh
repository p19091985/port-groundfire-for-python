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
//   File name : inifile.hh
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
#ifndef __INIFILE_HH__
#define __INIFILE_HH__

////////////////////////////////////////////////////////////////////////////////
// Includes
////////////////////////////////////////////////////////////////////////////////
#include <string>
#include <map>

using namespace std;

// INPUT

class cReadIniFile 
{
public:
    cReadIniFile (string const & configFile);
    
    float  getFloat  (string const & section, 
                      string const & entry, 
                      float          defaultValue) const;

    int    getInt    (string const & section,
                      string const & entry,
                      int            defaultValue) const;

    string getString (string const & section,
                      string const & entry,
                      string         defaultValue) const;
    
private:
    map<string, string> _entries;

};

// OUTPUT

class cWriteIniFile
{
public:
    void addSection (string const & section);

    bool putFloat  (string const & section,
                    string const & entry,
                    float          value);

    bool putInt    (string const & section,
                    string const & entry,
                    int            value);

    bool putString (string const & section,
                    string const & entry,
                    string const & value);

    void write (string const & configFile);

private:
    map<string, map<string, string> > _entries;
    
};

#endif
