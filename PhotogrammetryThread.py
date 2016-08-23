from PyQt4 import QtCore, QtGui
import support_functions
import Photogrammetry
import subprocess

class PhotogrammetryThread(QtCore.QThread):
    def __init__(self, command, projectStatus, mainWindow, arg=None):
        QtCore.QThread.__init__(self)
        self.command = command
        self.arg = arg
        self.projectStatus = projectStatus
        self.incPG = Photogrammetry.Photogrammetry(self.projectStatus, self.log)
        self.mainWindow = mainWindow

    def log(self, txtList):
        self.mainWindow.plainTextEdit.emit(QtCore.SIGNAL("log(QStringList)"), txtList)

    def __del__(self):
        self.wait()

    def run(self):
        print "DISABLING MENU"
        self.log(["disableMenu"])
        p = None
        if self.command == 'initialize':
            jsonStatus = self.incPG.getIncrementalInitialization()
            p = subprocess.Popen(["xdot", self.projectStatus.geoMatchesFile])
            if jsonStatus:
                p = subprocess.Popen(["meshlab", self.projectStatus.openMVGSfMInitialStructureFile])

        elif self.command == 'append':
            self.incPG.projectStatusObject  = self.projectStatus
            old_photos                      = self.projectStatus.getOldPhotos()
            all_photos                      = support_functions.getImagesList(self.projectStatus.inputDir)
            new_photos                      = support_functions.getNewPhotosList(old_photos, all_photos)
            print "PHOTO GRAMMETRY THREAD", new_photos
            #exit()
            selected_photos_list            = support_functions.getSelectedPhotoList(self.mainWindow)
            self.log(["Selected photo list"] + selected_photos_list)
            if len(new_photos) > 0:
                self.voiceReport(jsonStatus=None, new_photos=new_photos)
                self.log(["Doing incremental append with option:", self.arg])
                jsonStatus = self.incPG.getIncrementalAppend(new_photos, selected_photos_list, matchingOption = self.arg)

                p = subprocess.Popen(["xdot", self.projectStatus.incrGeoMatchesFile])
                self.voiceReport(jsonStatus, new_photos) #inform via audio if  a single photo was matched
            else:
                #QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "There are no new photos!", QtGui.QMessageBox.Ok)
                #TODO EMIT SIGNAL THAT THERE ARE NO NEW PHOTOS
                pass
        elif self.command == 'find_weak_nodes':
            """ Find nodes with low number of matches """
            old_photos = self.projectStatus.getOldPhotos()
            all_photos = support_functions.getImagesList(self.projectStatus.inputDir)
            new_photos = support_functions.getNewPhotosList(old_photos, all_photos)
            nodesList = self.incPG.getWeakNodes(new_photos)
            self.mainWindow.listWidget_2.emit(QtCore.SIGNAL("displayWeakNodes(QStringList)"), nodesList)

        elif self.command == 'sparse':
            self.incPG.projectStatusObject = self.projectStatus
            """ Generate the sparese reconstruction file """
            if self.incPG.getSparseReconstruction():
                self.log([" Display the file using meshlab "])
                p = subprocess.Popen(["meshlab", self.projectStatus.openMVGSfMColorizedOutputFile])

        elif self.command == 'final':
            """ Generate the dense reconstruction file """
            if self.incPG.getDenseReconstruction(scale=self.arg):
                """ Display the file using meshlab"""
                p = subprocess.Popen(["meshlab", self.projectStatus.mveMeshCleanOutputFile])
        elif self.command == 'texture':
            """ Generate the texture for the mesh """
            if self.incPG.getTexturedReconstruction():
                """ Display the file using meshlab"""
                p = subprocess.Popen(["meshlab", self.projectStatus.mveTextureOutputFile])
        elif self.command == 'viewMatchesGraph':
            """ Display matches graph with the changed node names """
            newGraphUrl = self.incPG.generateNamedMatchesGraph()
            if newGraphUrl:
                p = subprocess.Popen(["xdot", newGraphUrl])
        if p:
            self.log(["Waiting for subprocess termination"])
            p.wait()
        self.log(["enableMenu"])

    def voiceReport(self, jsonStatus, new_photos):
        if len(new_photos) == 1:
            if jsonStatus == None:
                p = subprocess.Popen(["espeak", "\""+new_photos[0].split('.')[0]+"\""]) # say the name of the photo
            elif new_photos[0] in jsonStatus['wrong_photos']:
                p = subprocess.Popen(["espeak", "\" False photo. Please make it again. \""])
            else:
                p = subprocess.Popen(["espeak", "\" Photo was matched.\""])
                #TODO chceck the number of connections
            p.wait()

