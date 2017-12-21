# Metadata mapping from iRODS to the general B2SHARE metadata

iRODS key | value | B2SHARE key
------|--------------|-----
TITLE | String or collection name | /titles
---  |---|  /description 
ABSTRACT  | String  | "description_type":"Abstract"
TABLEOFCONTENTS |Ticket: <ticket> |  "description_type":"TableOfContents"
TECHNICALINFO |{"irods_host": "", "irods_port": 1247, "irods_user_name": "anonymous", "irods_zone_name": ""}; iget/ils -t \<ticket\> \<path\>|"description_type":"TechnicalInfo" 
OTHER | http andpoint for iRODS, e.g. Metalnx | "description_type":"Other"
  | |
CREATOR | String (names of creators and authors)  | /creators
  | |
PID | http://hdl.handle.net/<PID\> | /alternate_identifiers; "alternate_identifier_type": "EPIC + path"
TICKET  |  String, \<ticket\>, \<path\> | /ResourceTypes, resource_type, resource_type_general = Dataset

