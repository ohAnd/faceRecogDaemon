#!/usr/bin/python3

from datetime import datetime
from PIL import Image, ImageDraw, ExifTags
import piexif
import glob
import os
import sys
import io
from io import BytesIO
from shutil import copyfile
import platform
import collections
from face_recognition.face_recognition_cli import image_files_in_folder
import threading 
from threading import Thread
import requests

import cv2

def getImageFromUrl(urlToImageSrc):
    
    
    try:
      response = requests.get(urlToImageSrc)
    except requests.ConnectionError:
      return 'connection_timeout'
    
    if response.status_code == 503:
        return 'error: doorbird - not available (503)'
    else:
        imageContent = BytesIO(response.content)
        return imageContent

def getImageFromRTSP(capture):   
    print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     1 start gettinf rtsp frame")
    startProcessTime = datetime.now()
    
    frame = capture.getFrame()
    if frame is None:
      return None
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    
    image = Image.fromarray(frame)    
    stream = io.BytesIO()       # creating a stream object to not write to the disk    
    image.save(stream, format="TIFF", compression=None) # tiff instead PNG for performace
    # stream.seek(0)
    
    processTime = (datetime.now() - startProcessTime)
    processTime = str(processTime)
    print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     2 done  rtsp frame - needed: "+processTime)
    return stream

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
      
class RTSPstream:
  def __init__(self, path):
    # print ("try to init with: "+path)
    # initialize the file video stream along with the boolean
    # used to indicate if the thread should be stopped or not
    self.stream = cv2.VideoCapture(path)
    if self.stream is None or not self.stream.isOpened():
       print('Warning: unable to open video source: ', path)
    self.stopped = True
    # init last data for warm start
    self.last_ready = None
  def start(self):
    # start a thread to read frames from the file video stream
    self.stopped = False
    t = Thread(target=self.update, args=())
    t.daemon = True
    t.start()
    return self
  def update(self):
    # keep looping infinitely
    while True:
      # if the thread indicator variable is set, stop the
      # thread
      if self.stopped:
        return
      # otherwise, get the last frame
      self.last_ready, self.last_frame = self.stream.read()

  def getFrame(self):
    if self.stream is None or not self.stream.isOpened():
       print('Warning: unable to open video source')
    # return last frame if available
    if (self.last_ready is not None) and (self.last_frame is not None):
        return self.last_frame.copy()
    else:
        print ("no frame seen")
        return None
  def stop(self):
    # indicate that the thread should be stopped
    self.stopped = True
  def isNotRunning(self):
    # indicate that the thread should be stopped
    # print ("rtsp is running?")
    return self.stopped