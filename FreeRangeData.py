#!/usr/bin/python
#imports 
import requests
from requests_oauthlib import OAuth1
import json
import pprint
import os
import sys
import getopt
import re
import fnmatch
import signal
#its not data dumper but it will do
pp = pprint.PrettyPrinter(indent=4)

#functions

def signal_handler(signal,frame):
	print "Caught a SIGINT , grabbing most recent copy of JSON from figshare and exiting gracefully"
	if package != '' and 'article_id' in package_json is not None: # we need both a package and an articleID in memory to fetch most recent copy
		fetch_article_info()
		sys.exit(0)
	else:
		sys.exit(0)

def fetch_credentials():
	cred = {}
	path = os.path.dirname(os.path.realpath(sys.argv[0]))
	path = path +'/oauth_credentials.txt'
	with open(path) as f:
		cred = json.load(f)
	return cred

#Sets up oath for the application
def authenticate():
	cred = fetch_credentials()
	oauth = OAuth1(client_key=cred['client_key'], client_secret=cred['client_secret'],
               resource_owner_key=cred['token_key'], resource_owner_secret=cred['token_secret'],
                signature_type = 'auth_header')
	return oauth


#Sets two lookup containers for articleID->filenames and tests for unique IDs for your uploads
def getMyArticles():
	client = requests.session()
	url = 'http://api.figshare.com/v1/my_data/articles'
	response=client.get(url,auth=oauth)
	json_response = json.loads(response.content)
	myArticles = json_response['items'] #all of my articles
	
	global articleID_and_files
	global title_and_articleIDs
	
	for article in myArticles:
		articleID_and_files[article["article_id"]] = []
		if article["title"] in title_and_articleIDs:
			(title_and_articleIDs[article["title"]]).append(article["article_id"])
		else:
			title_and_articleIDs[article["title"]] = []
			(title_and_articleIDs[article["title"]]).append(article["article_id"])
		for f in article["files"]:
			(articleID_and_files[article["article_id"]]).append(f['name'])


	return

#takes a file path and tests if it matches a unix like wildcard expression, if true returns false
def should_upload(path):
	should = 1

	for p in uploadmask:
		if fnmatch.fnmatch(path, p):
			should = 0
	#if we're overwriting just return now
	if overwrite == 1:
		return should
	#other wise test if the files been uploaded
	else: 
		if f in articleID_and_files[package_json['article_id']]:
			should = 0
	return should

##TODO: UPDATE/FORMAT USAGE MESSAGE (100)

def usage():
	print "usage:"
	print "./FigShareUpload <options>"
	print "options:"
	print "--package <directory>\t a directory to be uploaded. the directory name will be set as the article title."
	print "--tags <tag> or --tags <file> The tags to be associated with an upload. Can be called multiple times"
	print "--description <file> A text description for the upload. Can be called multiple times"
	print "--noupload <patter> Masks specific files in the package from being uploaded. wildcards accepted. Can be called multiple times"
	print "--publish Will set an article as PUBLIC. Use with caution as once it's public it WILL NOT come down"
	print "--force Will create a new article even if an article with that title already exists. Use with caution."
	print "--categories <int> Adds a category tag to the upload. Categories are currently integer only and defined By Figshare. Check FSCategories.json for categories"
	print "--overwrite Will overwrite uploaded files in the file set, Only use if you NEED the overwrite. It's unclear if Figshare tracks actual file chages in versioning"
	print "\n\n"
	return

###############################################################################
#																			  #
#																			  #
#								JSON MANIPULATION							  #
#																			  #
#																			  #
###############################################################################
#loads the current JSON file from the package
def load_json():
	json_data = open (package+'/Figshare.json')
	#retarded double load because stuff (honestly this seems like a shitty "feature")
	data = json.load(json_data)
	global package_json
	package_json = json.loads(data)
	print "JSON loaded from " + package +"/Figshare.json"
	return


#Gets the current JSON on figshare for the article id
def fetch_article_info():
	client = requests.session()
	url="http://api.figshare.com/v1/my_data/articles/{}".format(package_json['article_id'])
	response = client.get(url, auth=oauth)
	#check our return codes
	if(response.status_code == requests.codes.ok):
		print "Successfully updated article ", package_json['article_id']," through figshare"
		json_response = json.loads(response.content)
		json_response = json_response['items'].pop()
		#have to redump this resonse to a string dump, this is making more sense now but still a little odd
		json_response = json.dumps(json_response)
		update_json(json_response)
		return
	else:
		response.raise_for_status()
		exit(133) #may be overkill not sure

	return

#update the JSON document in memory and on disk
def update_json(response):
	try:
		with open (package+'/Figshare.json','w') as outfile:
			json.dump(response, outfile)
		outfile.close()
	except IOError: # a little bit of a wonky fix to get around some directory traversal
		try:
			with open ('Figshare.json','w') as outfile:
				json.dump(response, outfile)
			outfile.close()
		except IOError:
			exit(2)
	print "JSON for " + package + " updated to disk"
	return
###############################################################################
#																			  #
#																			  #
#					Article Creation/Manipulations							  #
#																			  #
#																			  #
###############################################################################

#create an article (minimum required to reserve said article)
def create_article(title, description,defined_type):
	client = requests.session()
	url ="http://api.figshare.com/v1/my_data/articles"
	body = {'title': title, 'description': description,'defined_type': defined_type}
	headers = {'content-type':'application/json'}
	response = client.post(url,auth=oauth,data=json.dumps(body),headers=headers)
	#check our return codes
	if(response.status_code == requests.codes.ok):
		global json_response
		json_response = json.loads(response.content)
		update_json(response.content)
		load_json()
		print "Article ", package_json['article_id'], " has been created"
	else:
		response.raise_for_status()
	return 

#add a file to the article , update JSON
def add_file(file_path):
	client = requests.session()
	file_name = os.path.basename(file_path)
	url = "http://api.figshare.com/v1/my_data/articles/{}/files".format(package_json['article_id'])
	files = {'filedata':(file_name, open( file_path , 'rb'))}
	response = client.put(url, auth=oauth,files=files)
	
	#check our return codes
	if(response.status_code == requests.codes.ok):
		print file_path ," was successfully uploaded"
		json_response = json.loads(response.content)
		update_json(response.content) # might get rid of this
	else:
		response.raise_for_status()
	return


def addCategory():
	client = requests.session()
	for categoryInt in catagories:
		body = {'category_id':categoryInt}
		headers = {'content-type':'application/json'}
		url = 'http://api.figshare.com/v1/my_data/articles/{}/categories'.format(package_json['article_id'])
		response = client.put(url,auth=oath,data=json.dumps(body),headers=headers)

		#check our return codes
		if(response.status_code == requests.codes.ok):
			print categoryInt , " has been added to article " , package_json['article_id']
			json_response = json.loads(response.content)
			update_json(json_response)
		else:
			response.raise_for_status()
	return

def addTag():
	client = requests.session()
	
	current_tags=[]
	for tag in package_json['tags']:
		current_tags.append(tag['name'])
	for tag in taglist:
		body = {'tag_name':tag}
		headers = {'content-type':'application/json'}

		if tag not in current_tags:
			url = 'http://api.figshare.com/v1/my_data/articles/{}/tags'.format(package_json['article_id'])
			response = client.put(url, auth=oauth,data=json.dumps(body), headers=headers)
			#check our return codes
			if(response.status_code == requests.codes.ok):
				json_response = json.loads(response.content)
				update_json(json_response)
				print package_json['article_id'] , "now has the tag " , tag," associated with it"
				current_tags.append(tag)
			else:
				response.raise_for_status()
	return


#add an author to the article
def add_Author(authID):
	client = requests.session()
	body = {'author_id':authID}
	headers = {'content-type':'application/json'}
	url = "http://api.figshare.com/v1/my_data/articles/{}/authors".format(package_json['article_id'])
	response = client.put( url, auth=oauth,data=json.dumps(body), headers=headers)
	#check our return codes
	if(response.status_code == requests.codes.ok):
		print package_json['article_id'] , "now has the author " , authID," associated with it"
		json_response = json.loads(response.content)
		update_json(json_response)
	else:
		response.raise_for_status()

	return


#PUBLISH A PRIVATE ARTICLE USE WITH CAUTION THIS IS IRREVERSIBLE
def publish():
	client = requests.session()
	url = 'http://api.figshare.com/v1/my_data/articles/{}/action/make_public'.format(package_json['article_id'])
	fetch_article_info()

	response = client.post(url,auth=oath)
		#check our return codes
	if(response.status_code == requests.codes.ok):
		print package_json['article_id'] , " is now free range!"
		json_response = json.loads(response.content)
		update_json(json_response)
	else:
		response.raise_for_status()

	return




##################################MAIN#########################################


#variables
#describe the package
package = ''
taglist = []
description =''
article_id = -1
articleID_and_files ={}
title_and_articleIDs ={}
package_json = {}
oauth = authenticate()
categories = []

#describe the process	
tagfile = ''
description_file =''
uploadmask = ['Figshare.json']
publish = 0
force = 0
overwrite = 0
upload = 0


try:
	options, remainder = getopt.gnu_getopt(sys.argv[1:],'o', ['package=','tags=','description=','noupload=', 'publish' , 'force' , 'categories=','overwrite'])
except getopt.GetoptError:
	usage()

#Argument Parsing
for opt,arg in options:
	if opt=='--package':
		if os.path.isdir(arg):
			package=arg
			if package.endswith('/'): 
				package=package[:-1]
		else:
			print "Currently a package must be a directory that contains files"
			sys.exit(2)
	if opt=='--tags':
		if os.path.isfile(arg):
			taglist = getTags(arg)
		else:
			taglist.append(arg)
	if opt=='--description':
		if os.path.isfile(arg):
			desciption = getDescription(arg)
		else:
			description = arg
	if opt =='--categories':
		categories.append(arg)
	if opt=='--noupload':
		uploadmask.append(arg)
	if opt=='--publish':
		publish = 1
	if opt=='--force':
		force = 1
	if opt=='--overwrite':
		overwrite =1
	if opt=='--upload': #not sure I want this to be explicit 
		upload =1

#SigInt Catches
signal.signal(signal.SIGINT, signal_handler)

	#test sensible setttings
if (not os.path.isdir(package)):
	print "Currently a package must be a directory that contains files"
	sys.exit(2)


#get fresh list of my articles from Figshare
getMyArticles()

#TODO: (5) Test if articles with package name exsist 

#is this a new figshare article or is there evidence that this has been uploaded before
if os.path.isfile(package+'/Figshare.json'):
	print "Package has a json inside of it, assuming that we're simply updating"
	#get information from the actual JSON we have on file
	##TODO (10)test if the JSON shows up in getMyArticle 
	load_json()
else:
	#create a new article
	print "Package appears to be a new upload"
	create_article(package,description,'fileset')
	load_json()
	
#refresh article info

getMyArticles()

pp.pprint (package_json)

upload = 1
if upload:
#move into the package and upload everything that is in there.
	if (os.path.isdir(package)):
		os.chdir(package)
		files = next(os.walk('.'))[2]
		for f in files:
			if should_upload(f):
				add_file(f)
		os.chdir('..')
	else:
		print("This doesn't appear to be a directory!")
		sys.exit(133)
	


if len(taglist) > 0 :
	addTag()

if len(categories) > 1:
	addCategory()



##TODO: (1) verify if these require , copy current , update, update on figshare @testing
##TODO: Update Categories (1) [testing]
##TODO: Update Description (1) [testing]
##TODO: Update Tags (1) [testing]
##TODO: Publish Article (1) [testing]


#need publish tag and description flow control. (need to add in tests and overwrites as well)
#get current JSON record from figshare and save to disk
fetch_article_info()
