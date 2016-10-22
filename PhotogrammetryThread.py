from PyQt4 import QtCore, QtGui
import support_functions
import Photogrammetry
import subprocess
import os
import shutil

import ProjectMerge

class PhotogrammetryThread(QtCore.QThread):

    incr_geo_matches_process = True

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
        self.log(["disableMenu", self.command])
        print "COMMAND >>", self.command, "<< COMMAND"
        p = None
        if self.command == 'initialize':
            jsonStatus = self.incPG.getIncrementalInitialization()
            p = subprocess.Popen(["xdot", self.projectStatus.geoMatchesFile])
            if jsonStatus:
                p = subprocess.Popen(["meshlab", self.projectStatus.openMVGSfMInitialStructureFile])
                #TODO run automatic photo source
                if self.arg == 'fromAutomaticPhotoSource':
                    self.log(['fromAutomaticPhotoSource'])
        elif self.command == 'append':
            self.incPG.projectStatusObject  = self.projectStatus
            old_photos                      = self.projectStatus.getOldPhotos()
            all_photos                      = support_functions.getImagesList(self.projectStatus.inputDir)
            new_photos                      = support_functions.getNewPhotosList(old_photos, all_photos)
            selected_photos_list            = support_functions.getSelectedPhotoList(self.mainWindow)
            print "SELECTED PHOTO LIST", selected_photos_list
            self.log(["Selected photo list"] + selected_photos_list)
            if len(new_photos) > 0 or self.arg == 'reinforceStructure':
                self.voiceReport(jsonStatus=None, new_photos=new_photos)
                self.log(["Doing incremental append with option:", self.arg])
                jsonStatus = self.incPG.getIncrementalAppend(new_photos, selected_photos_list, matchingOption = self.arg)
                self.log(['displayIncrementedGraph'])
                self.voiceReport(jsonStatus, new_photos) #inform via audio if  a single photo was matched
            else:
                self.log(["There are no new photos, please add some."])
        elif self.command == "merge":
            self.log(["Merge"])
            [projectStatus2, out_dir] = self.arg
            pm = ProjectMerge.ProjectMerge(self.projectStatus, projectStatus2, out_dir, log=self.log)
            result_url = pm.mergeProjects()
            self.log(["Result url", result_url])
            if support_functions.fileNotEmpty(result_url):

                self.incPG.run_DataColor(["-i", result_url, "-o", pm.psObjectOut.openMVGSfMColorizedOutputFile])
                self.log([" Display the file using meshlab "])
                p = subprocess.Popen(["meshlab",  pm.psObjectOut.openMVGSfMColorizedOutputFile])
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
                subprocess.Popen(["eog", self.projectStatus.openMVGSfMRotationGraphFile])
        elif self.command == "dense":
            """ Generate the dense reconstruction file """
            if self.incPG.getDenseReconstruction(scale = self.arg):
                self.meshlab_process = p = subprocess.Popen(["meshlab", self.projectStatus.mveScene2PsetOutputFile])
        elif self.command == "mesh":
            if self.incPG.getMesh(scale = self.arg):
                self.meshlab_process = p = subprocess.Popen(["meshlab", self.projectStatus.mveMeshCleanOutputFile])
        elif self.command == 'final':
            """ Generate the final reconstruction file """
            if self.incPG.getFinalReconstruction(scale=self.arg):
                """ Display the file using meshlab"""
                self.meshlab_process = p = subprocess.Popen(["meshlab", self.projectStatus.mveMeshCleanOutputFile])
        elif self.command == 'texture':
            """ Generate the texture for the mesh """
            if self.incPG.getTexturedReconstruction():
                """ Display the file using meshlab"""
                p = subprocess.Popen(["meshlab", self.projectStatus.mveTextureOutputFile])
        elif self.command == 'viewMatchesGraph':
            """ Display matches graph with the changed node names """
            #newGraphUrl = self.incPG.generateNamedMatchesGraph()
            #if newGraphUrl:
            if os.path.exists(self.incPG.projectStatusObject.geoMatchesFile) :
                #p = subprocess.Popen(["xdot", newGraphUrl])
                p = subprocess.Popen(["xdot", self.incPG.projectStatusObject.geoMatchesFile])

        elif self.command == "backup":
            support_functions.copyTree(self.projectStatus.matchesDir, self.projectStatus.matchesBackupDir)
            shutil.copy2(self.projectStatus.url, self.projectStatus.backupUrl)
            shutil.copy2(self.projectStatus.imageListingFile, self.projectStatus.imageListingBackupFile)
        elif self.command == 'recoverFromBackup':
            lastAddedPhotos = self.projectStatus.getLastAddedPhotos()
            self.projectStatus.wrong_photos = list(set(self.projectStatus.wrong_photos + lastAddedPhotos))
            self.projectStatus.photos = list(set(self.projectStatus.photos) - set(lastAddedPhotos))
            support_functions.copyTree(self.projectStatus.matchesBackupDir, self.projectStatus.matchesDir)
            self.projectStatus.saveCurrentStatus()
        if p:
            self.log(["Waiting for subprocess termination"])
            p.wait()
        self.log(["enableMenu"])


    def voiceReport(self, jsonStatus, new_photos):
        if len(new_photos) == 1:
            if jsonStatus == None:
                text = new_photos[0].split('.')[0]
                v = subprocess.Popen(["espeak", "\""+ text +"\""]) # say the name of the photo
            elif new_photos[0] in jsonStatus['wrong_photos']:
                text = "False photo. Please make it again."
                v = subprocess.Popen(["espeak", "\" "+ text+" \""])
            elif "connections" in jsonStatus.keys():
                if jsonStatus["connections"] > 0:
                    if jsonStatus["connections"] < 4:
                        text = "Only "+ str(jsonStatus["connections"]) +" connection, please make more similar photos"
                        v = subprocess.Popen(["espeak", "\" "+ text +" \""])
                    else:
                        text =  str(jsonStatus["connections"]) + " connections found"
                        v = subprocess.Popen(["espeak", "\"" + text +"\""])
                else:
                    text = "False photo " + str(jsonStatus["connections"]) + " connections found"
                    v = subprocess.Popen(["espeak", "\" "+ text +"\""])
            else:
                text = "Reused photo was matched."
                v = subprocess.Popen(["espeak", "\" "+ text +"\""])
            self.log([text])
            v.wait()

