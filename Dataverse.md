# Metadata mapping from iRODS to the general Dataverse metadata

Dataverse allows to upload data as json and xml. Here we use the json metadata description which is also supported by the python API.
We provide a generic Dataverse metadata json file. The most generic metadata can be retrieved by:

```py 
md = json.load(open('dataverseMD.json'))
md['metadataBlocks']['citation']['fields']
```

There are in total 31 generic metadata fields one can set. We pick some of them in the table below and sketch how to adjust them.

iRODS key | value | Dataverse access | Compulsary
------|--------------|-----|-----
TITLE | String | md['metadataBlocks']['citation']['fields'][0]['value']
ABSTRACT  | String  | "description_type":"Abstract"
TABLEOFCONTENTS |Ticket: <ticket> |  "description_type":"TableOfContents"
TECHNICALINFO |{"irods_host": "", "irods_port": 1247, "irods_user_name": "anonymous", "irods_zone_name": ""}; iget/ils -t \<ticket\> \<path\>|"description_type":"TechnicalInfo" 
OTHER | http andpoint for iRODS, e.g. Metalnx | "description_type":"Other"
  | |
CREATOR | String (names of creators and authors)  | /creators
  | |
PID | http://hdl.handle.net/<PID\> | /alternate_identifiers; "alternate_identifier_type": "EPIC + path"
TICKET  |  String, \<ticket\>, \<path\> | /ResourceTypes, resource_type, resource_type_general = Dataset

