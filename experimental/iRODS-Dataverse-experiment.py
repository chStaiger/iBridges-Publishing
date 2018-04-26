#cd /home/admincentos/src/dataverse
from dataverse import Connection
from dataverse.dataverse import Dataverse
from dataverse.dataset import Dataset
from dataverse import utils
import uuid
import requests

#Create connection to dataverse
host = 'demo.dataverse.nl' # Instance at DANS
token = '********'
connection = Connection(host, token, use_https=False)

alias = 'myDataverseAlias'

# Create Dataverse
dataverse = connection.create_dataverse(alias, alias, 'me@home.nl', alias)
# Http responses on server malformatted: https:// ... 8080:8080 or 8181:8181 --> server side fault, github issue created
#if connection.host.endswith(':8080') and connection.host != 'localhost':
#    href = dataverse.collection.get('href')
#    href = href.replace('https', 'http')
#    href = href.replace('8080:8080', '8080')
#    dataverse.collection.set('href', href)
# and publish
dataverse.publish()


# Get dataverse and data
dataverse = connection.get_dataverse(alias)
datasets = dataverse.get_datasets() # throws error Failed to parse: ip.add.ress:8080:8080
dataset = dataverse.get_dataset_by_doi(dataverse.get_datasets()[0].doi)
#if self.connection.host.endswith(':8080') and self.connection.host != 'localhost':
#            self.edit_uri = self.edit_uri.replace('https', 'http')
#            self.edit_uri = self.edit_uri.replace('8080:8080', '8080')
#            self.edit_media_uri = self.edit_media_uri.replace('https', 'http')
#            self.edit_media_uri = self.edit_media_uri.replace('8080:8080', '8080')
#files = dataset.get_files()
print files[0].download_url

# Delete Dataverse
alias="another-alias"
dataverse = connection.get_dataverse(alias)
connection.delete_dataverse(dataverse)

# Create datasets
title = 'API dataset'
creator = 'API user'
description = 'Upload by API'
metadata = {'date': '2018-04-10', 'subject': 'my subject'} # keywords as in DC:AtomPub

# test creation functions
#dataset = Dataset(title=title, description=description, creator=creator)
#resp = requests.post(dataverse.collection.get('href'), data=dataset.get_entry(), headers={'Content-type': 'application/atom+xml'}, auth=dataverse.connection.auth)
#response = resp.content # malformatted URLs
#if dataverse.connection.host != 'localhost' and dataverse.connection.host.endswith(':8080'):
#    response = resp.content.replace("8080:8080", "8181")

# after fix:
dataverse.create_dataset(title=title, creator=creator,
    description=description, **md)
dataset = dataverse.get_dataset_by_title(title)

# Upload files
#if dataset.connection.host.endswith(':8080') and dataset.connection.host != 'localhost':
#    dataset.edit_uri = dataset.edit_uri.replace('https', 'http')
#    dataset.edit_uri = dataset.edit_uri.replace('8080:8080', '8080')
#    dataset.edit_media_uri = dataset.edit_media_uri.replace('https', 'http')
#    dataset.edit_media_uri = dataset.edit_media_uri.replace('8080:8080', '8080')
uploadFiles = [os.getenv("HOME")+'/Desktop/smile.jpeg', os.getenv("HOME")+'/Desktop/irods_gsp_alice.cyberduckprofile']
dataset.upload_filepaths(uploadFiles)

# Update metadata
# curl -u $API_TOKEN: --data-binary "@metadata.xml" -H "Content-Type: application/atom+xml" http://$HOSTNAME:8080/dvn/api/data-deposit/v1.1/swordv2/collection/dataverse/christineverse
#Either edit example metadata or extend existing metadata
exampleMD = json.loads(open('dataverseMD.json').read())
md = dataset.get_metadata()
md['metadataBlocks']['citation']['fields'][4]['value']=[u'Other', u'Chemistry']
dataset.update_metadata(md)
