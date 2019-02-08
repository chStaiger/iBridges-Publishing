# Contents and usage

## Clients
The folder clients contains the classes and workflows for publishing data from iRODS to external repositories.

## Requirements
### iRODS

- irods user who has read/write access to the designated publish collections in iRODS
- If you want to use tickets to refer to data in iRODS, you need to create an iRODS 
 user 'anonymous' without password and with read access to the respective data collections in iRODS.
- In general you need those collections with the respective ACL settings:

```sh
 # users to access data anonymously
 iadmin mkuser anonymous rodsuser
 iadmin mkuser davrods rods user # access to data via davrods
 iadmin moduser davrods password davrods

 # users in group public can place data under public, however data will be owned by service account to publish data 
 ichmod own ibridges /ibridgesZone/home/public
 ichmod write public /ibridgesZone/home/public
 # anonymous users only get read rights under public
 ichmod -r read anonymous /ibridgesZone/home/public
 ichmod -r read davrods /ibridgesZone/home/public
 ichmod -r read davrods /ibridgesZone/home/davrods

 ichmod inherit /ibridgesZone/home/public

 imkdir inherit /ibridgesZone/home/public/Dataverse
 imkdir inherit /ibridgesZone/home/public/B2SHARE
 imkdir inherit /ibridgesZone/home/public/CKAN
``` 

### B2SHARE
You need an account and API token for the instance https://trng-b2share.eudat.eu/

### Dataverse
- You need access to a demo instance and create a token there:
  - https://demo.dataverse.nl/
  - https://demo.dataverse.org/
- Or you can install an [own instance](Dataverse%20Installation.pdf).

### CKAN
 - You need access to a demo CKAN instance and create a token there.
 - [Guide](https://github.com/EUDAT-Training/B2FIND-Training/blob/master/04-install-CKAN-CentOS.md) to create an own CKAN instance.

### EPIC PIDs
To connect to the handle server you need
- Access to a handle prefix
- A private key and certficate associated with your prefix
- A credentials.json:
 ```sh
 {
    "handle_server_url": "https://epic4.storage.surfsara.nl:8007",
    "private_key": "<full/path/to/privkey.pem>",
    "certificate_only": "<full/path/to/certificate_only.pem>",
    "prefix": "21.T12995",
    "handleowner": "200:0.NA/21.T12995",
    "reverselookup_username": "21.T12995",
    "reverselookup_password": "***",
    "HTTPS_verify": "False"
}
 ```
Note: If you do not have a Handle prefix, uuids will be created for the data.

## Usage

- Imports
 ```py
 from irodsPublishCollection import irodsPublishCollection
 from b2shareDraft import b2shareDraft
 from dataverseDraft import dataverseDraft
 from ckanDraft import ckanDraft
 from irodsRepositoryClient import irodsRepositoryClient
 import datetime

 RED     = "\033[31m"
 GREEN   = "\033[92m"
 BLUE    = "\033[34m"
 DEFAULT = "\033[0m"
 ```
 
- Parameters
 ```py
 #iRODS credentials and parameters
 irodsEnvFile    = '' # .irods/irodsenviroment.json; needs to be accompanied with the .irodsA password file
 collection      = '<full irods path>'

 #B2SHARE credentials and parameters
 apiToken        = '******************************************'
 apiUrl          = 'https://trng-b2share.eudat.eu/api/'
 community       = 'e9b9792e-79fb-4b07-b6b4-b9c2bd06d095'
 
 #Dataverse credentials and parameters
 apiToken        = '******************************************'
 apiUrl          = 'http://demo.dataverse.nl/'
 alias           = 'a64b880c-408b-11e8-a58f-040091643b8b'

 #Dataverse credentials and parameters
 apiToken        = '******************************************'
 apiUrl          = 'http://your.ckan.org/'
 organisation    = 'ibridges'
 group           = 'test' # optional ckan group

 #Other parameters for publication
 maxDataSize     = 2000 # in MB
 ```

- Instantiation of classes
 ```py
 ipc = irodsPublishCollection(irodsEnvFile, collection)
 draft = b2shareDraft(apiToken, apiUrl, community)
 draft = dataverseDraft(apiToken, apiUrl, alias)
 draft = ckanDraft(parameters[apiToken, apiUrl, organisation, ckanGroup = group) 
 publishclient = irodsRepositoryClient(ipc, draft)
 ```
- Workflows
 - [workflowPublishIRODS2B2SHARE.py](clients/workflowPublishIRODS2B2SHARE.py): You only need the class for the iRODS collection and the draft
 - [workflowPublishDataverse.py](clients/workflowPublishDataverse.py): You only need the class for the iRODS collection and the draft
 - [workflowPublish.py](clients/workflowPublish.py) more convenient example; uses the irodsRepositoryClient to abstract from single tasks in the publishing proccess (works for B2SHARE and Dataverse)
 
- [workflowPublishClt.py](clients/workflowPublishClt.py): 
 You will need to prepare the [parameters.json](parameters_template.json).
 Run the whole publication workflow by starting:
 
  ```sh
  python workflowPublishClt.py
  ```
  Hello
