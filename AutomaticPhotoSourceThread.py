#import subprocess
import time
import os
#import re
#import ast
#import BeautifulSoup
import support_functions
#import urllib2
from PyQt4 import QtCore

class AutomaticPhotoSourceThread(QtCore.QThread):
    def __init__(self, projectStatusObject, mainWindow, ui):
        QtCore.QThread.__init__(self)
        self.projectStatusObject = projectStatusObject
        self.mainWindow = mainWindow
        self.ui = ui
        self.oldPhotos = []
        pc = support_functions.downloadWebPageContent(projectStatusObject.automatic_photo_source)
        if pc != None:
            self.oldPhotos = support_functions.findNewPhotos(pc, self.oldPhotos)

    def log(self, txtList):
        self.ui.plainTextEdit.emit(QtCore.SIGNAL("log(QStringList)"), txtList)

    def run(self):
        while self.mainWindow.isVisible():
            pc = support_functions.downloadWebPageContent(self.projectStatusObject.automatic_photo_source)
            if pc != None:
                newPhotos = support_functions.findNewPhotos(pc, self.oldPhotos)
                self.oldPhotos += newPhotos
                for photo in newPhotos:
                    support_functions.downloadSinglePhoto(photoName = photo, webSourceUrl=self.projectStatusObject.automatic_photo_source, workspaceUrl=self.projectStatusObject.inputDir)

                    self.log(["refresh"])
                    self.log(["appendNewPhotosToNewestPhotos"])
                    while not self.ui.menubar.isEnabled(): #wait until appending finishes
                        time.sleep(1)
            else:
                self.log(["connectionError"])
                break
            time.sleep(1)


