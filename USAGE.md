# Usage

## Clients
The folder clients contains the classes and workflows for publishing data from iRODS to external repositories.

## Requirements and preparation
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

### Dataverse
- You need access to a demo instance and create a token there:
  - https://demo.dataverse.nl/
  - https://demo.dataverse.org/
- Or you can install an [own instance](Dataverse%20Installation.pdf).

Configuration for iRods - Dataverse integration
```bash 
cp dataverse.json.template dataverse.json
vi dataverse.json
```

### Install python packages

```bash
pip install -r requirements.txt
```

### Prepare icommands
```bash
iinit
```

## Usage

```bash
./ipublish --config dataverse.json [COLLECTION]
```
