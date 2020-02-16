#!/usr/bin/python

from datetime import datetime
from PIL import Image, ImageDraw, ExifTags
import piexif
import glob
import os
from shutil import copyfile
import platform
import collections
from face_recognition.face_recognition_cli import image_files_in_folder

def getImageFromUrl(urlToImageSrc):
    import requests
    from io import BytesIO
    try:
      response = requests.get(urlToImageSrc)
    except requests.ConnectionError:
      return 'connection_timeout'
    
    if response.status_code == 503:
        return 'error: doorbird - not available (503)'
    else:
        imageContent = BytesIO(response.content)
        return imageContent

def getRecentFileOfDirectory(pathToImageArchive,num):  
  files_path = pathToImageArchive+'/*.png' # * means all if need specific format then *.csv
  files = sorted(glob.iglob(files_path), key=os.path.getctime, reverse=True)
  if int(num) >= len(files):
    return 'notFound'
  return files[int(num)]

def getRecentFileOfDirectoryMaxCount(pathToImageArchive):  
  files_path = pathToImageArchive+'/*.png' # * means all if need specific format then *.csv
  files = sorted(glob.iglob(files_path), key=os.path.getctime, reverse=True)
  return len(files)

def getImageInTrainDirectory(trainDir,nameDir,num):  
  files_path = trainDir+'/' + nameDir + '/*' # * means all if need specific format then *.csv
  files = sorted(glob.iglob(files_path), key=os.path.getctime, reverse=True)
  if len(files) == 0: # or len(files) <= num:
    print ("cnt: "+str(len(files))+" num: "+ str(num))
    return 'notFound'
  if int(num) >= len(files):
    print ("2. cnt: "+str(len(files))+" num: "+ str(num))
    return 'notFound'
  return files[int(num)]

# def getImageInTrainDirectoryByFilename(trainDir,nameDir,filename):  
#   files_path = trainDir+'/' + nameDir + '/*' # * means all if need specific format then *.csv
#   files = sorted(glob.iglob(files_path), key=os.path.getctime, reverse=True)
#   if len(files) == 0: # or len(files) <= num:
#     print "cnt: "+str(len(files))+" num: "
#     return 'notFound'
#   if int(num) >= len(files):
#     print "2. cnt: "+str(len(files))+" num: "
#     return 'notFound'
#   return files[int(num)]

def getPersonFromTrainFolder(train_dir):
  persons = {}
  # Loop through each person in the training set
  for class_dir in os.listdir(train_dir):
    if not os.path.isdir(os.path.join(train_dir, class_dir)):
       continue
    # Loop through each training image for the current person
    images = []
    files_path = os.path.join(train_dir, class_dir)
    imageFiles = sorted(glob.iglob(files_path+'/*.*'), key=os.path.getctime, reverse=True)
    for img_path in imageFiles:
      images.append(os.path.basename(img_path))
    
    persons[class_dir] = {
      'count': len(imageFiles),
      # 'imagelinksBase': imageFiles,
      'imagelinks': images 
    }
    persons = collections.OrderedDict(sorted(persons.items()))
  return persons

def getFileProps(file):
  # print file
  img = Image.open(file)
  # print "info: "
  # print img.info 
  exif_dict = piexif.load(img.info["exif"])
  # print "dict: "
  # print exif_dict
  
  #exif_dict = {}
  
  exif_dict["faceRecog"] = {}
  exif_dict["faceRecog"]['srcData'] = 'quelle/hier'
  # exif_dict["faceRecog"]['names'] = {}
  # exif_dict["faceRecog"]['names'] = {'test','test1','test2'}
  exif_bytes = piexif.dump(exif_dict)

  img.save(file, "jpeg", exif=exif_bytes)

  return 0

def moveFileToFolder(src,target):
  os.rename(src, target)
  return 0

def copyFileToFolder(src,target):    
  if os.path.isfile(target):
    print ("file: "+target+" already exists")
    return 1
  else:
    print ("copy file: "+src+" to: "+target)
    copyfile(src,target)
  return 0

def deleteFileWithPath(pathToFile):
  print ("delete file - "+pathToFile)
  os.remove(pathToFile)
  return 0

def getCtimeFormmatedOfFile(path_to_file):
  cTimeString = ''
  """
  Try to get the date that a file was created, falling back to when it was
  last modified if that isn't possible.
  See http://stackoverflow.com/a/39501288/1709587 for explanation.
  """
  if platform.system() == 'Windows':
    cTimeString = os.path.getctime(path_to_file)
  else:
      stat = os.stat(path_to_file)
      try:
        cTimeString = stat.st_birthtime
      except AttributeError:
          # We're probably on Linux. No easy way to get creation dates here,
          # so we'll settle for when its content was last modified.
          cTimeString = stat.st_mtime  
  import time
  cTimeString = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(cTimeString))
  return cTimeString

def getTaggedImageOfOriginal(pathToOriginalFile):
    #print "search for: "+pathToOriginalFile
    # directory for searching ../tagged
    directory = os.path.dirname(pathToOriginalFile)+'/tagged'
    filenameOrig = os.path.splitext(os.path.basename(pathToOriginalFile))[0]
    taggedImage = "notFound"
    listOfFile = os.listdir(directory)    
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(directory, entry)
        #print "search in: "+fullPath
        if entry.startswith(filenameOrig):
          taggedImage = entry
                
    return taggedImage