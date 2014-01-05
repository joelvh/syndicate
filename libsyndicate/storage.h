/*
   Copyright 2013 The Trustees of Princeton University

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

#ifndef _LIBSYNDICATE_STORAGE_H_
#define _LIBSYNDICATE_STORAGE_H_

#include "libsyndicate/libsyndicate.h"
#include "util.h"

// initialize local storage
int md_init_local_storage( struct md_syndicate_conf* c, char const* root_dir );

// file I/O
char* md_load_file_as_string( char const* path, size_t* size );

// directory manipulation
int md_mkdirs( char const* dirp );
int md_mkdirs2( char const* dirp, int start, mode_t mode );
int md_mkdirs3( char const* dirp, mode_t mode );
int md_rmdirs( char const* dirp );

#endif