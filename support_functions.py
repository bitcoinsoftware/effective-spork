import glob
import os
import shutil
from PyQt4 import QtCore, QtGui


def fileNotEmpty(url):
    if os.path.isfile(url):
        fsize = os.stat(url)
        if fsize.st_size > 0:
            return True 
    return False

def getImagesList(folderUrl):
    photoNameList = glob.glob1(folderUrl, '*.jpg') + glob.glob1(folderUrl, '*.JPG') + glob.glob1(folderUrl, '*.png')
    photoNameList += glob.glob1(folderUrl, '*.jpeg') + glob.glob1(folderUrl, '*.JPEG') + glob.glob1(folderUrl,'*.PNG')
    photoNameList.sort()
    return photoNameList

def insertPhotosInListWidgets(mainWindow, inputDir, goodPhotoNamesList=[], wrongPhotoNamesList=[], newPhotosList=[], recentlyMatchedPhotosList=[]):
    mainWindow.menubar.setEnabled(True)
    mainWindow.listWidget.clear()
    mainWindow.listWidget_2.clear()
    mainWindow.listWidget.addItems(goodPhotoNamesList)
    mainWindow.listWidget.addItems(wrongPhotoNamesList)
    mainWindow.listWidget.addItems(newPhotosList)

    for i in xrange(mainWindow.listWidget.count()):
        item = mainWindow.listWidget.item(i)
        photoName = item.text()
        if photoName in wrongPhotoNamesList: #is a wrong matched photo
            item.setBackgroundColor(QtGui.QColor("red"))
        elif photoName in newPhotosList: #is a new photo
            item.setBackgroundColor(QtGui.QColor("blue"))
            insertPhotoIntoListWidget(mainWindow.listWidget_2, os.path.join(inputDir, str(photoName)))
        elif photoName in recentlyMatchedPhotosList: # was matched recently correctly
            item.setBackgroundColor(QtGui.QColor("green"))

""" insert images into the second listWidget that holds only new photos """
def insertPhotoIntoListWidget(listWid, photoPath):
    qImage = QtGui.QImage(photoPath)
    qImage = qImage.scaledToWidth(listWid.width())
    qBrush = QtGui.QBrush(qImage)
    qListWidgetItem = QtGui.QListWidgetItem()
    qListWidgetItem.setBackground(qBrush)
    qListWidgetItem.setToolTip(photoPath)
    qListWidgetItem.setSizeHint(QtCore.QSize(listWid.width(), qImage.height()))
    listWid.addItem(qListWidgetItem)

def getNewPhotosList(oldPhotos, allPhotos):
    newPhotosList = list(set(allPhotos) - set(oldPhotos))
    newPhotosList.sort()
    return newPhotosList

def getSelectedPhotoList(mainWindow):
    selected_items = mainWindow.listWidget_2.selectedItems()
    selected_photo_list = []
    for item in selected_items:
        selected_photo_list.append(os.path.basename(str(item.toolTip())))

    selected_items = mainWindow.listWidget.selectedItems()
    for item in selected_items:
        selected_photo_list.append(str(item.text()))
    return selected_photo_list

def writeToStdout(textArray):
    for text in textArray:
        print text

def downloadSinglePhoto(photoName, webSourceUrl, workspaceUrl):
    photoWebUrl = os.path.join(webSourceUrl, photoName)
    data = downloadWebPageContent(photoWebUrl)
    with open(os.path.join(workspaceUrl, photoName), 'w') as f:
        f.write(data)

def downloadPhotos(webSourceUrl, workspaceUrl):
    wpc = downloadWebPageContent(webSourceUrl)
    if wpc != None:
        photosList = findNewPhotos(wpc)
        if len(photosList) > 0:
            for photoName in photosList:
                downloadSinglePhoto(photoName, webSourceUrl, workspaceUrl)
            return 0
        else:
            return -1
    else:
        return -1

def downloadWebPageContent(url):
    import urllib2
    user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
    headers = {'User-Agent': user_agent}
    req = urllib2.Request(url, None, headers)
    try:
        response = urllib2.urlopen(req).read()
        return response
    except urllib2.URLError:
        return None

def findNewPhotos(pageContent, oldPhotos = []):
    import re, ast
    photoLines = re.findall("wlansd.push.*$", pageContent, re.MULTILINE)
    photoNames = []
    for photoLine in photoLines:
        photoLine = photoLine.strip().replace("wlansd.push(", "").replace(");", "")
        photoLineDict = ast.literal_eval(photoLine)
        if len(photoLineDict['fname'].split('.') ) ==2:
            if photoLineDict['fname'].split('.')[1] in ['jpg', 'JPG', 'jpeg', 'JPEG', 'PNG','png']:
                photoNames.append(photoLineDict['fname'])
    newPhotoNames = list(set(photoNames) - set(oldPhotos))
    return newPhotoNames

def copyTree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.mkdir(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)