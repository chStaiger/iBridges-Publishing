# Metadata mapping from iRODS to the general Dataverse metadata

Dataverse allows to upload data as json and xml. Here we use the json metadata description which is also supported by the python API.
We provide a generic Dataverse metadata json file. The most generic metadata can be retrieved by:

```py 
md = json.load(open('dataverseMD.json'))
md['metadataBlocks']['citation']['fields']

for i in range(0, len(md['metadataBlocks']['citation']['fields'])):
  print i, md['metadataBlocks']['citation']['fields'][i]['typeName']

0 	title 		          primitive
1 	subtitle 		        primitive
2 	alternativeTitle 		primitive
3 	alternativeURL 		  primitive
4 	otherId 		        compound
5 	author 		          compound
6 	datasetContact 		  compound
7 	dsDescription 		  compound
8 	subject 		        controlledVocabulary
9 	keyword 		        compound
10 	topicClassification 		compound
11 	publication 		    compound
12 	notesText 		      primitive
13 	language 		        controlledVocabulary
14 	producer 		        compound
15 	productionDate 		  primitive
16 	productionPlace 		primitive
17 	contributor 		    compound
18 	grantNumber 		    compound
19 	distributor 		    compound
20 	distributionDate 		primitive
21 	depositor 		      primitive
22 	dateOfDeposit 		  primitive
23 	timePeriodCovered   compound
24 	dateOfCollection 		compound
25 	kindOfData 		      primitive
26 	series 		          compound
27 	software 		        compound
28 	relatedDatasets 		primitive
29 	otherReferences 		primitive
30 	dataSources 		    primitive
```
There are in total 31 generic metadata fields one can set. We pick some of them in the table below and sketch how to adjust them.

iRODS key | value | Dataverse access 
------|--------------|-----
TITLE | String | 0  title
ABSTRACT  | String  | 7   dsDescription
TABLEOFCONTENTS |iRODS Ticket or PID to iRODS data |  4 	otherId
TECHNICALINFO |{"irods_host": "", "irods_port": 1247, "irods_user_name": "anonymous", "irods_zone_name": ""}; iget/ils -t \<ticket\> \<path\>|27 	software
OTHER | http endpoint for iRODS, e.g. Metalnx | 3 alternativeURL
  | |
CREATOR | Surname, First name  | 5 	author
  | |
PID | http://hdl.handle.net/<PID\> | 29 	otherReferences
TICKET  |  String, \<ticket\>, \<path\> | 29 	otherReferences
SUBJECT | controlled vocabulary | 8 	subject

Dataverse asks for a metadata item called "Subject" which comes from a controlled vocabulary:
```
Agricultural Sciences; Arts and Humanities; Astronomy and Astrophysics; 
Business and Management; Chemistry; Computer and Information Science; 
Earth and Environmental Sciences; Engineering; Law; Mathematical Sciences; 
Medicine, Health and Life Sciences; Physics; Social Sciences; Other
```
If not defined we will set it to "Other".
