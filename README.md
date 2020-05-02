# iBridges
**Authors**
- Christine Staiger (SURFsara)
- Stefan Wolfsheimer (SURFsara)

**License**
Copyright 2017-2018 SURFsara BV

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

## Synopsis
- Some classes and workflows to connect iRODS to other data services
- directory with experimental scripts highlighting the workflow
- directory with workflow and client implementations

## Requirements

- python 2.7 
- iRods icommands
- iRODS instance
  - iRODS 4.1.10 or 4.2.1
  - Rodsuser 'anonymous' with read rights to /zone/home/public/<repo_name> 

### python packages
(see also requirements.txt)
- urllib3
- requests
- lxml
- bleach
- termcolor
- uuid
- python-irodsclient
  
## Features
### iRODS functionality
 - Creation of tickets for anonymous access

### Integration with Dataverse
 - Creating a Dataverse draft with either only metadata or metadata and data
 - Mapping of metadata in iRODS to [Dataverse citation metadata template](Dataverse_metadata_map.md)
 - Creation of Persistent Identifiers with B2HANDLE [TODO]
 - Linking to data in iRODS by Persistent Identifiers or by iRODS Tickets
 - If HTTP endpoint or Davrods endpoint is given, data is made accessible to user davrods and anonymous
 - NOTE: Dataverse offers a nice user interface for data in draft state and already assigns PIDs to drafts, hence we skip that publishing part in the client and leave it to the user.
 
### Integration CKAN
 - Creating a CKAN package containing only metadata
 - Mapping of metadata in iRODS to [CKAN citation metadata template](CKAN-metadata-map.md)
 - Creation of Persistent Identifiers with B2HANDLE [TODO]
 - Linking to data in iRODS by Persistent Identifiers or by iRODS Tickets
 - If HTTP endpoint or Davrods endpoint is given, data is made accessible to user davrods and anonymous
 - NOTE: Metadata is publicly available directly publicly available, i.e. there is no draft phase in CKAN


## Usage

[see Usage](USAGE.md)
