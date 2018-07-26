# Metadata mapping from iRODS to the general CKAN metadata

iRODS key | value | CKAN key
------|--------------|-----
TITLE | String or collection name | title
ABSTRACT  | String  | notes
TABLEOFCONTENTS |Ticket: <ticket> | extras/iRODS ticket (for collection)
TECHNICALINFO |{"irods_host": "", "irods_port": 1247, "irods_user_name": "anonymous", "irods_zone_name": ""}; iget/ils -t \<ticket\> \<path\>| extras/anonymous access
OTHER | http endpoint for iRODS, e.g. Metalnx | extras/Metalnx access
  | |
CREATOR | String (names of creators and authors)  | author
  | |
PID | http://hdl.handle.net/<PID\> | extras/PIDS (for collection and collection members)
TICKET  |  String, \<ticket\>, \<path\> | extras/iRODS tickets (for collection and collection members)

## Mnimal metadata which is accepted by CKAN
```py
from urllib2 import quote
import simplejson as json
from urllib2 import urlopen, Request
import uuid

#Create connection to ckan
host = '145.100.59.86:8080'
token = '********'

alias = 'ibridges' #CKAN org, compulsory
group = '' #optional
title = ‘Goldfish1’ # Does not need to be unique
name = 'str(uuid.uuid1())' # needs to be unique

# Create datasets
action = 'package_create' # package_update
action_url = 'http://{host}/api/3/action/{action}'.format(host=host,action=action)
data = {'title': title, 'owner_org': alias, 'name': name}

data_string = quote(json.dumps(data))
request = Request(action_url,data_string)
request.add_header('Authorization', token)
response = urlopen(request) # if name already exists or is not given throws 409
```

## B2FIND training metadata

```
{'DiscHierarchy': [],
 'extras': [{'key': 'Discipline', 'value': 'Not stated'},
  {'key': 'ResourceType', 'value': 'Relatively peaceful'},
  {'key': 'SpatialCoverage', 'value': ['Lake Tanganyika']},
  {'key': 'fulltext',
   'value': 'Multi;Neolamprologus multifasciatus;Relatively peaceful;Breed in colonies;2 inches;PH 7.4 to 9.0, Temp 72F - 84F;Bottom;Carnivore;Lake Tanganyika'},
  {'key': 'oai_identifier', 'value': 'Multi'},
  {'key': 'oai_set', 'value': None},
  {'key': 'ManagerVersion', 'value': '2.3.1'}],
 'group': 'fishproject',
 'groups': [{'name': 'fishproject'}],
 'name': 'multi',
 'owner_org': 'rda',
 'state': 'active',
 'title': 'Neolamprologus multifasciatus',
 'url': u'',
 'version': '58131b7e445b6999ef68a312034d7f95'}
```

In the field 'extras' Community specific metadata can be stored with own keys. This metadat is mapped to specific B2FIND facets.
