# faceRecogDaemon
- [faceRecogDaemon](#facerecogdaemon)
  - [description](#description)
    - [Problem](#problem)
    - [Possible solution](#possible-solution)
    - [Features](#features)
      - [user side](#user-side)
      - [technical side](#technical-side)
  - [installation](#installation)
    - [download & start](#download--start)
    - [configuration](#configuration)
  - [API](#api)
  - [Links](#links)

## description
Just started as a little application for easy managing face recognition outputs.

### Problem

You have a video/ image stream of a camera or something else. And you want to analyse the images for known faces. And get needed infos for further triggering for e.g. a smart home system to open a door or similar things.

### Possible solution

face recognition daamon ;-)

### Features

#### user side
- overview of recent historic recognized faces
  - change seen faces to other persons for next training
  - change seen faces to new persons for next training (coming soon)
- manage training data
  - remove images from person folder
  - move images to other persons
- manage settings (editing - coming soon)
- show api information

screenshots of client:

![home](./docs/home.png "home")
![home menu](./docs/home_menu.png "home menu")
![live](./docs/live.png "live")
![history](./docs/history.png "history")
![history training](./docs/history_train.png "history training")
![training](./docs/training.png "training")
![training images](./docs/training_images.png "training images")
![settings](./docs/settings.png "settings")
![api](./docs/api.png "api")

#### technical side
- for the recognition itself the library of https://github.com/ageitgey/face_recognition is used 
- api for all stuff provided
- client in hmtl/ javascript full responsive and prepared for web app
- 3-tier architecture - file-db, backend/ middleware, client ( not fully at this time ;-) )
  - "file-db" - primitve folder driven training data for images + archive for recognized faces
  - backend/ middleware - serves the functions over an api
  - client - html/ javascript web client prepared for a web app


## installation
The application is written in Python. So you need an already installed environment as described here: https://www.python.org/about/gettingstarted/


### download & start

Donwload 'face recognition daemon' application the last release at https://github.com/ohAnd/faceRecogDaemon/releases

Load needed modules with pip

        pip install "module"

start the serve (service installation coming soon)

        bash:// ./faecRecogDaemon.py

### configuration
create a config file in application root directory

        touch config.ini

with following content

        # config file for face recog daemon
        [webserver]
        Port: 5001

        [imageSource]
        urlToImageSrc = <your_path_to_image_src>

        [faceRecognition]
        knnDistance = 0.50

        [directories]
        pathToKnownFaces = <your_path>
        pathToImageArchive = <your_path>

## API

all features are described inside the client app
|method|url|
|---|---|
|**face recognition**| |
|trigger new face recognization with a fresh image from source<br> return: JSON|/api/check|
|get online face recognization, return the result image directly<br> return: image|/api/check?stream=1|
|**training**||
|get all training src data as summary in JSON|/api/training?getdata=true|
|retrigger the training of given images|/api/training?retrain=true|
|move image from history to training data with given person name|/api/training?rename=true&image=mmmmm.jpg&name=Joe|
|get trained image by person and filename|/api/get_train_image?person=name&filename=name01.png|
|get trained image by number|/api/get_train_image?person=name&number=0|
|**recent recognitions**||
|get most recent image|/api/get_recent_image|
|get an overview of recent images in JSON<br>(default limited to 10, if less images available it is shortend)|/api/get_recent_image?json|
|get an overview of recent images in JSON with given limit of resopnse<br>e.g. 30 entries (hard limited to 1000)|/api/get_recent_image?json&limit=30|
|get most recent image - higher number means older image|/api/get_recent_image?number=0|
|get most recent image with new face recognition fpr filename|/api/get_recent_image?filename=name|
|get most recent image without image manipulation (timestamp face frame/ naming)|/api/get_recent_image?number=0&original=true|
|**images**||
|get image file with name|/api/get_image?file=name|
                    


## Links
source for used libs:
- https://github.com/ageitgey/face_recognition
- https://github.com/ageitgey/face_recognition/blob/master/examples/face_recognition_svm.py
- https://face-recognition.readthedocs.io/en/latest/face_recognition.html

used images:
- https://www.freepik.com/premium-vector/biometric-person-identification-facial-recognition-concept-futuristic-low-polygonal-human-face_4847694.htm
- ...


