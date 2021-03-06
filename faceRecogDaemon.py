#!/usr/bin/python3

portForWebserver = 5001
urlToImageSrc = 'https://c.pxhere.com/images/57/9c/893d3c322850a321e164a0c8cc75-1418580.jpg!d'

knnDistance = 0.6

pathToKnownFaces = 'train_dir'
pathToImageArchive = 'webserver2'

version = '1.0.2'

################################################################################################################################
import os
import sys
sys.path.append("modules/")
import imageHandling
import faceRecogKNN
import configparser

from flask import Flask, jsonify, request, send_file, render_template, g, \
     abort, Response, redirect, url_for
from datetime import datetime
app = Flask(__name__)

cfg = configparser.ConfigParser()
cfg.read("config.ini")
try:
    if cfg.get('webserver','Port') != '':
        port = cfg.get('webserver','Port')
    if cfg.get('imageSource','urlToImageSrc') != '':
        urlToImageSrc = cfg.get('imageSource','urlToImageSrc')
    if cfg.get('faceRecognition','knnDistance') != '':
        knnDistance = cfg.getfloat('faceRecognition','knnDistance')
        app.logger.info("config: "+str(knnDistance))
    if cfg.get('directories','pathToImageArchive') != '':
        pathToImageArchive = cfg.get('directories','pathToImageArchive')
    if cfg.get('directories','pathToKnownFaces') != '':
        pathToKnownFaces = cfg.get('directories','pathToKnownFaces')
except configparser.NoSectionError:
    app.logger.info("no config.ini - use defaults")
except configparser.NoOptionError:
    app.logger.info("config.ini - missing option")

# initialize rtsp instance for later threading, if rtsp url is given
if(urlToImageSrc.startswith("rtsp")):
    newRTSP = imageHandling.RTSPstream(urlToImageSrc)
global debug
debug = False
# # # # Webserver # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

@app.route('/api/check', methods=['GET'])
def check():
    if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" - API-check 1 start gettinf rtsp frame")
    startProcessTime = datetime.now()
    # is online streaming requested
    if request.args.get('stream') == '1':
        stream = 1
    else:
        stream = 0
    checkResponse = {
        "status": 'not started',
        "checkDetails": {
            'NumberOfFaces': 0,
            'imageToCheck': '',
            'linkToArchivedImage': '',
            },
        "checkResults": {
            "personsFound": {},
            "linkToResultImage": ''
            }
    }
    # get last image
    
    if(urlToImageSrc.startswith("rtsp")):
        # start rtsp stream with first image request and start a timer to stop after 60 sec
        # TODO: restsart timer with every request to get the stream alive        
        if newRTSP.isNotRunning():
            newRTSP.start()
            timer = imageHandling.startTimer(newRTSP.stop)
            timer.start()
        # get image from rtsp stream
        lastImage = imageHandling.getImageFromRTSP(newRTSP)
                
        # send loading image if last image couldn't get (at starting this happnes sometimes)
        if lastImage is None:
            pathFilename = 'static/img/loading.png'
            return send_file(pathFilename, mimetype='image/gif')           
    else:
        lastImage = imageHandling.getImageFromUrl(urlToImageSrc)
    
    if "error" in lastImage:
        checkResponse['status'] = lastImage
        return jsonify(checkResponse)
    else:
        checkResponse['checkDetails']['imageToCheck'] = urlToImageSrc
    # get face Recog
    if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     1 start getFaces on frame")
    startProcessTimeFaces = datetime.now()
    noOfFaces = faceRecogKNN.getFacesInImage(lastImage)
    processTime = (datetime.now() - startProcessTimeFaces)
    if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     2 done  getFaces on frame: "+str(processTime))
    checkResponse['checkDetails']['NumberOfFaces'] = noOfFaces
    # get predictions for found faces
    personsFound = {} 
    imageBlob = ''
    if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     1 start prediction on frame")
    startProcessTimePred = datetime.now()
    predictions = faceRecogKNN.predict(lastImage, model_path=pathToKnownFaces+"/trained_knn_model.clf",distance_threshold=knnDistance)
    processTime = (datetime.now() - startProcessTimePred)
    if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     2 done  prediction on frame: "+str(processTime))
    if noOfFaces > 0:
        for name, (top, right, bottom, left) in predictions:
            if name in personsFound:
                name = name+'_'+str(datetime.now().strftime("%Y%m%d_%H%M%S"))
            personsFound[name] = {
                "left" : left,
                "top": top
            }
        checkResponse['status'] = 'ok'
        checkResponse['checkResults']['personsFound'] = personsFound
    else:
        checkResponse['status'] = 'no faces found'
    # save prediction image
    if stream == 0:
        imageLocalLink = faceRecogKNN.show_prediction_labels_on_image(lastImage,pathToImageArchive,predictions,0,noOfFaces)
        checkResponse['checkResults']['linkToResultImage'] = 'http://'+request.host +'/api/get_image?file='+imageLocalLink
    else:
        if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     1 start recog on frame")
        startProcessTimeRecog = datetime.now()
        imageBlob = faceRecogKNN.show_prediction_labels_on_image(lastImage,pathToImageArchive,predictions,0,noOfFaces,retLinkOrBlob='blob')
        processTime = (datetime.now() - startProcessTimeRecog)
        if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" -     2 done  recog on frame: "+str(processTime))
        
    if stream == 1:
        # print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" - 4 send image to client")
        processTime = (datetime.now() - startProcessTime)
        if debug: print (str(datetime.now().strftime("%Y%m%d_%H%M%S.%f"))+" - API-Check 2 done - send image to client: "+str(processTime))
        return send_file(imageBlob, mimetype='image/gif')
    else:
        # Return the result as json
        return jsonify(checkResponse)

@app.route('/api/retrain', methods=['GET'])
def reTrain():
    app.logger.info("Training KNN classifier...")
    classifier = faceRecogKNN.train(pathToKnownFaces, model_save_path=pathToKnownFaces+"/trained_knn_model.clf", n_neighbors=2)
    app.logger.info("Training complete!")
    # Return the result as json
    result = {
        "training": 'done',
    }
    return jsonify(result)

@app.route('/api/training', methods=['GET', 'POST'])
def apiTraining():
    if request.method == 'GET' and request.args.get('getdata') == 'true':
        persons = imageHandling.getPersonFromTrainFolder(pathToKnownFaces)
        result = {
            "persons": persons
        }
        return jsonify(result)
    elif request.method == 'GET' and request.args.get('retrain') == 'true':
        # import time
        def generate():
            # app.logger.info('request started')
            # for i in range(5):
            #     time.sleep(1)
            #     yield str(i)
            # app.logger.info('request finished')
            startProcessTime = datetime.now()
            app.logger.info("Training KNN classifier...")
            n_neighbors = faceRecogKNN.train(pathToKnownFaces, model_save_path=pathToKnownFaces+"/trained_knn_model.clf", verbose=True) #, n_neighbors=2
            app.logger.info("Training complete!")
            processTime = (datetime.now() - startProcessTime)
            processTime = str(processTime).split('.')[0]
            yield str(processTime + " with " + str(n_neighbors) + " neighbors")
        return Response(generate(), mimetype='text/plain')
    elif request.method == 'GET' and request.args.get('rename') == 'true':
        src = pathToImageArchive+request.args.get('image','')
        tgt = pathToKnownFaces+'/'+request.args.get('name','')+'/'+os.path.basename(request.args.get('image',''))
        taggedImageFile = imageHandling.getTaggedImageOfOriginal(src)
        taggedImage = pathToImageArchive+'/faces/tagged/'+taggedImageFile
        # def generate():
        app.logger.info("add image to train dir - src: "+src+" dst: "+tgt)
        resp = imageHandling.copyFileToFolder(src,tgt)
        resp = imageHandling.deleteFileWithPath(taggedImage)
            # if resp != 0:
            #     yield resp
            # yield ''
        # return 0 Response(generate(), mimetype='text/plain')
        return redirect(url_for('.history', _anchor=request.args.get('image','')))
    abort(404)

@app.route('/api/get_image')
def get_image():
    filename = request.args.get('file')
    pathFilename = os.path.abspath(pathToImageArchive+'/'+filename)
    if not os.path.isfile(pathFilename):
        pathFilename = 'static/img/404.png'
    return send_file(pathFilename, mimetype='image/gif')

@app.route('/api/get_recent_image')
def get_recent_image():
    if 'json' in request.args: # request.args.get('json','false') == 'true':
        limit = int(request.args.get('limit',10)) # limit the response to default 10 recent images
        if limit > 1000:
            limit = 1000
        images=[]
        for imgNo in range(0,limit):
            imgObj = {}
            apiLink     = "http://"+request.host+'/api/get_image?file='
            apiLinkNew  = "http://"+request.host+'/api/get_recent_image?filename='
            subFolderWithFaces = "/faces"            
            image = imageHandling.getRecentFileOfDirectory(pathToImageArchive+subFolderWithFaces,imgNo)
            if image == 'notFound':
                continue
            
            taggedImage = imageHandling.getTaggedImageOfOriginal(image)
            
            imageOriginalLink   = apiLinkNew+image.replace(pathToImageArchive,'')
            if taggedImage != 'notFound':
                imageTaggedLink = apiLink+subFolderWithFaces+'/tagged/'+ taggedImage
                taggedName = taggedImage.split('__')[1].split('.jpg')[0]
            else:
                imageTaggedLink = 'notFound'
                taggedName = 'notFound'
                            
            # tagged = apiLink+image.replace(pathToImageArchive,"")
            # orig = apiLink+image.replace(pathToImageArchive+'/faces/',"")
            # orig = orig.split('__')[0]+'.jpg'
            # origImageName = orig.split(apiLink)[1]
            
            imgObj['imageTaggedLink']   = imageTaggedLink
            imgObj['imageOriginalLink'] = imageOriginalLink
            imgObj['imageOriginalName'] = image.replace(pathToImageArchive,'')

            imgObj['name'] = taggedName
            images.append(imgObj)
        result = {
        "recentImages": images,
        "overallRecognitons": str(imageHandling.getRecentFileOfDirectoryMaxCount(pathToImageArchive+subFolderWithFaces))
        }
        return jsonify(result)
    elif 'filename' in request.args:
        pathFilename = pathToImageArchive+request.args.get('filename')
    elif 'number' in request.args:
        recentImageNumber = request.args.get('number')
        pathFilename = imageHandling.getRecentFileOfDirectory(pathToImageArchive+'/faces/tagged/',recentImageNumber,'jpg')
        return send_file(pathFilename, mimetype='image/gif')
    else: # no args given, most recent image
        pathFilename = imageHandling.getRecentFileOfDirectory(pathToImageArchive+'/faces/tagged/',0)
    app.logger.info("/api/get_recent_image - given filename: "+pathFilename)
    # compose the response
    if not os.path.isfile(pathFilename):
        pathFilename = 'static/img/404.png'
        return send_file(pathFilename, mimetype='image/gif') 
    elif request.args.get('original','false') == 'true':
        if not os.path.isfile(pathFilename):
            pathFilename = 'static/img/404.png'
        return send_file(pathFilename, mimetype='image/gif') 
    else:
        startProcessTime = datetime.now()
        lastImage = pathFilename
        timeStampOfFile = imageHandling.getCtimeFormmatedOfFile(lastImage)
        predictions = faceRecogKNN.predict(lastImage, model_path=pathToKnownFaces+"/trained_knn_model.clf",distance_threshold=knnDistance)
        imageBlob = faceRecogKNN.show_prediction_labels_on_image(lastImage,pathToImageArchive,predictions,timeStampOfFile,retLinkOrBlob='blob')
        processTime = (datetime.now() - startProcessTime)
        app.logger.info("recogonition for: "+lastImage+" needs: "+str(processTime))
        return send_file(imageBlob, mimetype='image/gif')

@app.route('/api/get_train_image')
def get_train_image():
    imageToShow = request.args.get('number',0) # if not set take most recent -> 0
    person = request.args.get('person','')
    if 'filename' in request.args: 
        pathFilename = pathToKnownFaces+"/"+person+"/"+request.args.get('filename',0)
    else:
        pathFilename = imageHandling.getImageInTrainDirectory(pathToKnownFaces,person,imageToShow)
    #print "path: "+pathFilename
    if not os.path.isfile(pathFilename):
        pathFilename = 'static/img/404.png'
    return send_file(pathFilename, mimetype='image/gif')

# website #########################################################################

@app.route('/')
def index():
    g.version = version
    # imageHandling.getFileProps('eee.jpgneu1.jpg')
    return  render_template("index.html")

@app.route('/liveview')
def liveview():
    values = {}
    values['hostlink'] = request.host
    g.version = version
    return  render_template("liveview.html", values=values)

@app.route('/history')
def history():
    values = {}
    values['hostlink'] = request.host
    g.version = version
    return  render_template("history.html", values=values)

@app.route('/training')
def training():
    g.version = version
    values = {}
    values['hostlink'] = request.host
    persons = imageHandling.getPersonFromTrainFolder(pathToKnownFaces)
    return  render_template("training.html", persons=persons, values=values)

@app.route('/settings')
def settings():
    config = {}
    config['urlToImageSrc'] = urlToImageSrc
    config['pathToImageArchive'] = pathToImageArchive
    config['knnDistance'] = knnDistance
    g.version = version
    return  render_template("settings.html", config=config)

@app.route('/apiinfo')
def apiinfo():
    values = {}
    values['hostlink'] = request.host
    g.version = version
    return  render_template("apiinfo.html", values=values)

if __name__ == "__main__":
    #faceRecog.init_faceRecog(pathToKnownFaces)
    if not os.path.isfile(pathToKnownFaces+"/trained_knn_model.clf"):
        app.logger.info("Training KNN classifier...")
        classifier = faceRecogKNN.train(pathToKnownFaces, model_save_path=pathToKnownFaces+"/trained_knn_model.clf", n_neighbors=2)
        app.logger.info("Training complete!")

    import logging
    logging.basicConfig(level=logging.INFO,filename=pathToImageArchive+"/faceRecogDeamon.log")
    logger = logging.getLogger(__name__)

    # httpLogger = logging.getLogger("*")
    # httpLogger.addHandler(logging.FileHandler("http-log.txt"))
    # # httpLogger.addFilter(logging.Filter("HTTP"))
    # httpLogger.propagate = False
    
    # app.run(host='0.0.0.0', port=portForWebserver, debug=True)
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(('', portForWebserver), app, log=logger)
    http_server.serve_forever()