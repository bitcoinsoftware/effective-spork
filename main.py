from gui import *
from PyQt4 import QtCore, QtGui
from functools import partial
import subprocess
import os
from PhotogrammetryThread import PhotogrammetryThread
from AutomaticPhotoSourceThread import AutomaticPhotoSourceThread
import support_functions
import ProjectStatus

class UserInterface:
    def __init__(self, ui, MainWindow):
        self.dir = None
        self.projectStatus = None
        self.pg = None
        self.logStr = ''
        self.ui = ui
        self.mainWindow = MainWindow
        self.aps = None #automatic photo source

    def refresh(self):
        if self.projectStatus is not None:
            photos_in_folder_list = support_functions.getImagesList(self.projectStatus.inputDir)
            good_photos = self.projectStatus.photos
            wrong_photos = self.projectStatus.wrong_photos
            new_photos = list(set(photos_in_folder_list) - set(good_photos) - set(wrong_photos))
            support_functions.insertPhotosInListWidgets(self.ui, inputDir = self.projectStatus.inputDir,
                                                        goodPhotoNamesList = self.projectStatus.photos,
                                                        wrongPhotoNamesList = self.projectStatus.wrong_photos,
                                                        newPhotosList = new_photos )
            self.ui.label_3.setText("New images :")
            self.log(["Good photos number:", str(len(good_photos)), "Wrong photos number:", str(len(wrong_photos)), "New photos number", str(len(new_photos))])
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please initialize the project first", QtGui.QMessageBox.Ok)

    def newProject(self, precisionMode):
        self.dir = str(QtGui.QFileDialog.getExistingDirectory(caption = "Select Photo Directory"))
        if self.dir:
            self.projectStatus = ProjectStatus.ProjectStatus(self.dir, precisionMode)
            self.refresh()
            self.ui.label_3.setText("New images :")

    def loadProject(self, url = None):
        if url == None:
            self.dir = str(QtGui.QFileDialog.getOpenFileName(caption = "Select projectStatus.json file", filter=("projectStatus.json")))
        else:
            self.dir = url
        if self.dir and os.path.exists(self.dir):
            self.projectStatus      = ProjectStatus.ProjectStatus(self.dir)
            self.refresh()
            self.ui.label_3.setText("New images :")

    def editProjectFile(self):
        if self.projectStatus is None:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please load or open the project first", QtGui.QMessageBox.Ok)
        else:
            self.projectStatus.editStatus()

    def runAutomaticPhotoSource(self):
        if self.projectStatus is not None and self.projectStatus.successful and self.projectStatus.automatic_photo_source != None and self.aps == None:
            self.log(["Running Automatic Photo Source"])
            self.aps = AutomaticPhotoSourceThread(self.projectStatus, ui = self.ui, mainWindow = self.mainWindow)
            self.aps.start()
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please initialize the project first and set the automatic photo source in project preferences", QtGui.QMessageBox.Ok)

    def initializeProject(self, initializationType ='fromLocalPhotos'):
        if self.projectStatus is not None and self.projectStatus.successful:
            choice = QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Project is allready initialized, do you want to overwrite it?",
                                       QtGui.QMessageBox.Yes| QtGui.QMessageBox.No)
            if choice == QtGui.QMessageBox.Yes:
                self.projectStatus.successful = False
                self.initializeProject()
        elif self.projectStatus is not None:
            self.ui.menubar.setEnabled(False)
            if initializationType =='fromAutomaticPhotoSource':
                if self.projectStatus.automatic_photo_source != None:
                    self.log(["Downloading photos, this may take a minute."])
                    if support_functions.downloadPhotos(webSourceUrl = self.projectStatus.automatic_photo_source, workspaceUrl = self.projectStatus.inputDir) !=0:
                        QtGui.QMessageBox.question(self.mainWindow, 'Warning!',
                                                   "Unable to download photos from the automatic photo source. Please check the settings.",
                                                   QtGui.QMessageBox.Ok)
                else:
                    QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please set the automatic photo source in project preferences", QtGui.QMessageBox.Ok)

            self.pg = PhotogrammetryThread('initialize', self.projectStatus, self.ui)
            self.pg.start()
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please load or open the project first", QtGui.QMessageBox.Ok)

    def appendNewPhotos(self, matchingOption):
        if self.projectStatus is not None and self.projectStatus.successful:
            self.ui.menubar.setEnabled(False)
            self.pg = PhotogrammetryThread('append', self.projectStatus, self.ui, arg = matchingOption)
            self.pg.start()
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please initialize the project first", QtGui.QMessageBox.Ok)


    def computeSparseReconstruction(self):
        if self.projectStatus is not None and self.projectStatus.successful:
            self.log(["Compute sparse reconstruction"])
            self.ui.menubar.setEnabled(False)
            self.pg = PhotogrammetryThread('sparse', self.projectStatus, self.ui)
            self.pg.start()
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!',
                                       "Unable to compute the sparse reconstruction from the provided data. Please add more photos and initialize the project first",
                                       QtGui.QMessageBox.Ok)

    def computeRegionOfInterest(self):
        print "Not implemented yet"

    def computeFinalReconstruction(self, precision):
        if self.projectStatus is not None and (self.projectStatus.sparse_reconstruction or self.projectStatus.successful):
            choice = None
            if self.projectStatus.successful and not self.projectStatus.sparse_reconstruction: # if the project was successfully initialized but the sparse recon wasn't counted
                choice = QtGui.QMessageBox.question(self.mainWindow, 'Warning!',
                                           "Found only the initial structure from motion output. If you want to update the project, please compute the sparse reconstruction first. "
                                           "Do you want to compute it anyway?", QtGui.QMessageBox.Ok, QtGui.QMessageBox.Cancel)
            if self.projectStatus.sparse_reconstruction or choice == QtGui.QMessageBox.Ok:
                self.log(["Compute final reconstruction"])
                self.ui.menubar.setEnabled(False)
                self.pg = PhotogrammetryThread('final', self.projectStatus, self.ui, precision)
                self.pg.start()
                self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please compute the sparse reconstruction first", QtGui.QMessageBox.Ok)

    def computeTexturedReconstruction(self):
        if self.projectStatus is not None and self.projectStatus.dense_reconstruction:
            self.log(["Compute textured reconstruction"])
            self.ui.menubar.setEnabled(False)
            self.pg = PhotogrammetryThread('texture', self.projectStatus, self.ui)
            self.pg.start()
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please compute the dense reconstruction first", QtGui.QMessageBox.Ok)

    def findWeakNodes(self):
        if self.projectStatus is not None and self.projectStatus.successful:
            self.log(["Find weak nodes"])
            self.pg = PhotogrammetryThread('find_weak_nodes', self.projectStatus, self.ui)
            self.pg.start()
            self.projectStatus.saveCurrentStatus()
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please initialize the project first", QtGui.QMessageBox.Ok)

    def displayPhoto(self, widgetOptionStr):
        """Display the photo in an external editor after double click"""
        if widgetOptionStr == "textWidget":
            photo_path = os.path.join(self.projectStatus.inputDir, str(self.ui.listWidget.currentItem().text()))
        else:
            photo_path = str(self.ui.listWidget_2.currentItem().toolTip())
        p = subprocess.Popen(["eog", photo_path])

    def displayWeakNodes(self, photoNamesList):
        self.log(["Display weak nodes"])
        self.ui.listWidget_2.clear()
        self.log(["Inserting:"] + list(photoNamesList))
        for photoName in photoNamesList:
            support_functions.insertPhotoIntoListWidget(self.ui.listWidget_2, os.path.join(self.projectStatus.inputDir, str(photoName)))
        self.ui.label_3.setText("Required photos similar to :")

    def displayAllGoodPhotos(self):
        if self.projectStatus is not None:
            self.log(["Display all good photos"])
            self.ui.listWidget_2.clear()
            for photoName in self.projectStatus.photos:
                support_functions.insertPhotoIntoListWidget(self.ui.listWidget_2, os.path.join(self.projectStatus.inputDir, str(photoName)))
            self.ui.label_3.setText("Matched photos :")

    def reusePhoto(self):
        for item in self.ui.listWidget.selectedItems():
            curr_text = str(item.text())
            self.projectStatus.wrong_photos = list(set(self.projectStatus.wrong_photos) - set([curr_text]))
            self.projectStatus.saveCurrentStatus()
            self.projectStatus.loadStatus()
        self.ui.pushButton.setEnabled(False)
        self.refresh()

    def enableButton(self):
        curr_text = str(self.ui.listWidget.currentItem().text())
        if curr_text in self.projectStatus.wrong_photos:
            self.ui.pushButton.setEnabled(True)

    def log(self, txtList):
        for txt in txtList:
            self.ui.plainTextEdit.insertPlainText(str(txt) + '\n')
            print txt
            if txt == "enableMenu":
                self.ui.menuFile.setEnabled(True)
                self.ui.menuTools.setEnabled(True)
                self.refresh()
            elif txt == "disableMenu":
                self.ui.menuFile.setEnabled(False)
                self.ui.menuTools.setEnabled(False)
                self.refresh()
            elif txt == "refresh":
                self.refresh()
            elif txt == "appendNewPhotosToNewestPhotos":
                self.appendNewPhotos("toNewestPhotos")
            elif txt == "connectionError":
                QtGui.QMessageBox.question(self.mainWindow, 'Warning!',"Unable to communicate with the photo source. Please chceck if the provided path is proper and check the connection.", QtGui.QMessageBox.Ok)
                self.aps = None

        self.ui.plainTextEdit.verticalScrollBar().setValue(self.ui.plainTextEdit.verticalScrollBar().maximum())

    def viewMatchingGraph(self):
        """ Display a named matching graph  """
        if self.projectStatus is not None and self.projectStatus.successful:
            self.log(["View matching graph"])
            self.pg = PhotogrammetryThread('viewMatchesGraph', self.projectStatus, self.ui)
            self.pg.start()
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please initialize the project first", QtGui.QMessageBox.Ok)

    def viewSparseReconstruction(self):
        if self.projectStatus is not None and self.projectStatus.sparse_reconstruction:
            self.log(["View sparse reconstruction"])
            p = subprocess.Popen(["meshlab", self.projectStatus.openMVGSfMColorizedOutputFileName])
            self.ui.label_3.setText("New images :")
        elif self.projectStatus is not None and self.projectStatus.successful:
            p = subprocess.Popen(["meshlab", self.projectStatus.openMVGSfMInitialStructureFile])
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please compute the sparse reconstruction first", QtGui.QMessageBox.Ok)

    def viewDenseReconstruction(self):
        if self.projectStatus is not None and self.projectStatus.dense_reconstruction:
            self.log(["View dense reconstruction"])
            p = subprocess.Popen(["meshlab", self.projectStatus.mveMeshCleanOutputFile])
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please compute the dense reconstruction first", QtGui.QMessageBox.Ok)

    def viewTexturedReconstruction(self):
        if self.projectStatus is not None and self.projectStatus.textured_reconstruction:
            self.log(["View dense reconstruction"])
            p = subprocess.Popen(["meshlab", self.projectStatus.mveTextureOutputFile])
            self.ui.label_3.setText("New images :")
        else:
            QtGui.QMessageBox.question(self.mainWindow, 'Warning!', "Please compute the textured reconstruction first",
                                   QtGui.QMessageBox.Ok)


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    userInt = UserInterface(ui, MainWindow)
    if len(sys.argv)>1:
        userInt.loadProject(sys.argv[1])
    QtCore.QObject.connect(ui.actionNormal_precision,               QtCore.SIGNAL('triggered()'), partial(userInt.newProject, "NORMAL"))
    QtCore.QObject.connect(ui.actionHigh_precision,                 QtCore.SIGNAL('triggered()'), partial(userInt.newProject, "HIGH"))
    QtCore.QObject.connect(ui.actionUltra_precision,                QtCore.SIGNAL('triggered()'), partial(userInt.newProject, "ULTRA"))
    QtCore.QObject.connect(ui.actionLoad_project,                   QtCore.SIGNAL('triggered()'), userInt.loadProject)

    QtCore.QObject.connect(ui.actionRefresh,                        QtCore.SIGNAL('triggered()'), userInt.refresh)
    QtCore.QObject.connect(ui.actionInitialize_with_local_stored_photos,    QtCore.SIGNAL('triggered()'), userInt.initializeProject)
    QtCore.QObject.connect(ui.actionInitialize_with_remote_stored_photos,   QtCore.SIGNAL('triggered()'), partial(userInt.initializeProject, "fromAutomaticPhotoSource"))
    QtCore.QObject.connect(ui.actionTo_all_old_nodes,                       QtCore.SIGNAL('triggered()'), partial(userInt.appendNewPhotos, "toAllNodes" ))
    #QtCore.QObject.connect(ui.actionTo_weak_nodes_only,                     QtCore.SIGNAL('triggered()'), partial(userInt.appendNewPhotos, "toWeakNodes"))
    #QtCore.QObject.connect(ui.actionTo_smart_choosen_nodes,                 QtCore.SIGNAL('triggered()'), partial(userInt.appendNewPhotos, "toSmartChoosenNodes"))
    QtCore.QObject.connect(ui.actionTo_selected_photos_and_their_matches,   QtCore.SIGNAL('triggered()'), partial(userInt.appendNewPhotos, "toSelectedPhotos"))
    QtCore.QObject.connect(ui.actionTo_newest_photos_and_their_matches,     QtCore.SIGNAL('triggered()'), partial(userInt.appendNewPhotos, "toNewestPhotos"))

    QtCore.QObject.connect(ui.actionCompute_sparse_reconstruction,          QtCore.SIGNAL('triggered()'), userInt.computeSparseReconstruction)
    QtCore.QObject.connect(ui.actionCompute_Region_Of_Interest,             QtCore.SIGNAL('triggered()'), userInt.computeRegionOfInterest)
    QtCore.QObject.connect(ui.actionReinforce_matching_graph_structure,     QtCore.SIGNAL('triggered()'), partial(userInt.appendNewPhotos, "reinforceStructure" ))

    QtCore.QObject.connect(ui.actionUltra_Precision,                QtCore.SIGNAL('triggered()'), partial(userInt.computeFinalReconstruction, 1))
    QtCore.QObject.connect(ui.actionVery_High,                      QtCore.SIGNAL('triggered()'), partial(userInt.computeFinalReconstruction, 2))
    QtCore.QObject.connect(ui.actionHigh_Precision,                 QtCore.SIGNAL('triggered()'), partial(userInt.computeFinalReconstruction, 3))
    QtCore.QObject.connect(ui.actionMedium_Precision,               QtCore.SIGNAL('triggered()'), partial(userInt.computeFinalReconstruction, 4))
    QtCore.QObject.connect(ui.actionLow_Precision,                  QtCore.SIGNAL('triggered()'), partial(userInt.computeFinalReconstruction, 5))
    QtCore.QObject.connect(ui.actionTexture_final_reconstruction,   QtCore.SIGNAL('triggered()'), userInt.computeTexturedReconstruction)

    QtCore.QObject.connect(ui.actionFind_weak_nodes_2,              QtCore.SIGNAL('triggered()'), userInt.findWeakNodes)
    QtCore.QObject.connect(ui.actionView_the_matching_graph,        QtCore.SIGNAL('triggered()'), userInt.viewMatchingGraph)
    QtCore.QObject.connect(ui.actionView_the_sparse_reconstruction, QtCore.SIGNAL('triggered()'), userInt.viewSparseReconstruction)
    QtCore.QObject.connect(ui.actionView_the_dense_reconstruction,  QtCore.SIGNAL('triggered()'), userInt.viewDenseReconstruction)
    QtCore.QObject.connect(ui.actionView_the_textured_reconstruction,  QtCore.SIGNAL('triggered()'), userInt.viewTexturedReconstruction)
    QtCore.QObject.connect(ui.actionDisplay_all_matched_photos,     QtCore.SIGNAL('triggered()'), userInt.displayAllGoodPhotos)

    QtCore.QObject.connect(ui.actionEdit_project_preferences,       QtCore.SIGNAL('triggered()'), userInt.editProjectFile)
    QtCore.QObject.connect(ui.actionRun_automatic_photo_source,       QtCore.SIGNAL('triggered()'), userInt.runAutomaticPhotoSource)

    QtCore.QObject.connect(ui.listWidget,                           QtCore.SIGNAL('doubleClicked(QModelIndex)'),    partial(userInt.displayPhoto, 'textWidget'))
    QtCore.QObject.connect(ui.listWidget_2,                         QtCore.SIGNAL('doubleClicked(QModelIndex)'),    partial(userInt.displayPhoto, 'photoWidget'))
    QtCore.QObject.connect(ui.listWidget,                           QtCore.SIGNAL('clicked(QModelIndex)'),          userInt.enableButton)
    QtCore.QObject.connect(ui.pushButton,                           QtCore.SIGNAL('clicked()'),                     userInt.reusePhoto)
    QtCore.QObject.connect(ui.plainTextEdit,                        QtCore.SIGNAL('log(QStringList)'),              userInt.log)
    QtCore.QObject.connect(ui.listWidget_2,                         QtCore.SIGNAL('displayWeakNodes(QStringList)'), userInt.displayWeakNodes)

    MainWindow.show()
    MainWindow.move(0,0)
    sys.exit(app.exec_())
