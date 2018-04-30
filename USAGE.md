# Contents and usage

## Clients
The folder clients contains the classes and workflows for publishing data from iRODS to external repositories.

## Requirements
### iRODS
- irods user who has read/write access to the designated publish collections in iRODS
- If you want to use tickets to refer to data in iRODS, you need to create an iRODS 
 user 'anonymous' without password and with read access to the respective data collections i iRODS.

### B2SHARE
You need an account and API token for the instance https://trng-b2share.eudat.eu/

### Dataverse
- You need access to a demo instance and create token there:
  - https://demo.dataverse.nl/
  - https://demo.dataverse.org/
- Or you can install an [own instance](Dataverse%20Installation.pdf).

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

 #Other parameters for publication
 maxDataSize     = 2000 # in MB
 ```

- Instantiation of classes
 ```py
 ipc = irodsPublishCollection(irodsEnvFile, collection)
 draft = b2shareDraft(apiToken, apiUrl, community)
 draft = dataverseDraft(apiToken, apiUrl, alias) 
 publishclient = irodsRepositoryClient(ipc, draft)
 ```
- Workflows
 - [workflowPublishIRODS2B2SHARE.py](clients/workflowPublishIRODS2B2SHARE.py): You only need the class for the iRODS collection and the draft
 - [workflowPublishIRODS2B2SHARE.py](clients/workflowPublishDataverse.py): You only need the class for the iRODS collection and the draft
 - [workflowPublish.py](clients/workflowPublish.py) more convenient example; uses the irodsRepositoryClient to abstract from single tasks in the publishing proccess (works for B2SHARE and Dataverse)
 
- [workflowPublishClt.py](clients/workflowPublishClt.py): 
 You will need to prepare the [parameters.json](parameters_template.json).
 Run the whole publication workflow by starting:
 
  ```sh
  python workflowPublishClt.py
  ```
