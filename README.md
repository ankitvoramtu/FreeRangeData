FreeRangeData
=============

A script for uploading and updating FigShare articles. I assume that a folder is a discrete fileset for an experiment or sample, we check to see evidence of the folder being submitted previously by : 1) looking for a json document from previous sessions and/or 2) Packages of the same name being uploaded by the user previously. 

There is a more [here](http://www.dylanstorey.com/node/21) on why why it's named what it is, and why it got built. 



#SetUp Instructions
1. Get a [Figshare] (http://figshare.com/)  account 
2. Click on the Applications tab from the drop down menu in the upper right corner.
3. Create a new application. 
4. Click on View/Edit On your Application tab
5. Click on Access codes
6. Save the secrets,keys,tokens into the dummy\_oauth\_credentials.txt files
7. Copy the dummy file to oauth_credentials.txt

#Running FreeRangeData
./FreeRangeData --package <folder>

##OtherOptions:
  --tags <text> or <file> tag you wish added to the article. Use Multiple times for multiple tags.
  
  --description <file> or <text> Article Description.
  
  --noupload <pattern> Mask specific files from being uploaded. (Currently using to create less than full articles prior to making public and finalizing uploads of data sets.)
  
  --categories <int> Add a category tag to the article. FigShareCategoryCodes.txt contains a list of these. 
  
  --overwrite Will overwrite already uploaded files to the article.(Default behavior is to assume that an uploaded file hasn't changed from last update)
  
  --publish Publishes the article. 
  
  --force Will create a new article with the same name, even if you already have one with that name uploaded.




#Features that may need to be looked at / tested 
Currently only supports filesets. 
May need to add base name to the package name selector. 
Test Tagging / Categories updating etc. 


#Notes

This program is still in early development it was written primarily for my use making some pretty big assumptions about how people organize their data. It is also my first foray into Python,so while I would love feedback/criticisms please keep it as constructive as possible. 
