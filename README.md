# iBridges
**Authors**
- Christine Staiger (SURFsara)

**License**
Copyright 2017 SURFsara BV

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

## Synopsis
- Some classes and workflows to connect iRODS to other data services
- directory with experimental scripts highlighting the workflow
- directory with workflow and client implementations

## Requirements
- icommands
- python 2.7
- python-irodsclient v0.7
- B2HANDLE python library
- iRODS instance
  - iRODS 4.1.10 or 4.2.1
  - Rodsuser 'anonymous' with read rights to /zone/home/public/<repo_name> 
  
 ## Features
 ### iRODS functionality
 - Creation of tickets for anonymous access
 
 ### Integration with B2SHARE
 - Creating a B2SHARE deposit with either only metadata or metadata and data
 - Mapping of metadata in iRODS to B2SHARE generic metadata template
 - Creation of Persistent Identifiers with B2HANDLE
 - Linking to data in iRODS by Persistent Identifiers or by iRODS Tickets
