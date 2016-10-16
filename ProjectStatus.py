import os
import json
import sys
import inspect

class ProjectStatus:
    newPhotosMatchingNumber             = 6 #just for option Appedn_to_newest_photos_and_their_matches
    nodePrefix                          = "n"
    projectStatusFileName               = "projectStatus.json"
    projectStatusBackupFileName         = "projectStatusBACKUP.json"
    featuresFolderName                  = "features"
    matchesFolderName                   = "matches"
    matchesBackupFolderName             = "matchesBACKUP"
    incrMatchesFolderName               = "incremental_matches"
    reconstructionFolderName            = "reconstruction_global"
    openMVGSensorWidthFileName          = "sensor_width_camera_database.txt"
    openMVGListingFileName              = "sfm_data.json"
    openMVGListingBackupFileName        = "sfm_dataBACKUP.json"
    openMVGPairListFileName             = "pair_list"
    openMVGMatchesFileName              = "matches.e.txt"
    openMVGGeoMatchesFileName           = "geometric_matches"
    openMVGNamedGeoMatchesFileName      = "named_geometric_matches"
    openMVGSfMOutputFileName            = "sfm_data.bin"
    openMVGSfMJSONOutputFileName        = "sfm_data.json"
    openMVGSfMColorizedOutputFileName   = "colorized.ply"
    openMVGSfMInitialStructureFileName  = "initial_structure.ply"
    openMVGRotationGraphFileName        = "global_relative_rotation_pose_graph_final.svg"
    mveFolderName                       = "MVE"
    mveViewsFolderName                  = "views"
    mveMainFileName                     = "synth_0.out"
    mveMetaDataFileName                 = "meta.ini"
    mveScene2PsetOutputFileName         = "dense_pointset.ply"
    mvePsetCleanOutputFileName          = "clean_dense_pointset.ply"
    mveFSSReconOutputFileName           = "surface.ply"
    mveMeshCleanOutputFileName          = "clean_surface.ply"
    mveTextureOutputFileNameNoExtension = "textured_clean_surface"
    mveTextureOutputFileName            = "textured_clean_surface.obj"

    def __init__(self, inputPath, precisionMode = "NORMAL"):
        #self.logMessageList             = []
        if os.path.exists(inputPath):
            if os.path.isdir(inputPath): #if we are opening a new project
                print "CREATING NEW PROJECT"
                self.inputDir               = inputPath
                self.outputDir              = os.path.join(inputPath, 'output')
                if not os.path.exists(self.outputDir):
                    os.mkdir(self.outputDir)
                self.url                    = os.path.join(self.outputDir, self.projectStatusFileName)
                self.backupUrl              = os.path.join(self.outputDir, self.projectStatusBackupFileName)
                self.successful             = False
                self.sparse_reconstruction  = False
                self.dense_reconstruction   = False
                self.textured_reconstruction= False
                self.mode                   = precisionMode
                self.photos                 = []
                self.wrong_photos           = []
                self.automatic_photo_source = None
                self.roi_scale              = False
                with open(self.url, 'w') as f:
                    json.dump(
                        {'status':self.successful, 'mode':self.mode, 'photos':self.photos, 'wrong_photos':[],
                         'sparse_reconstruction':self.sparse_reconstruction, 'dense_reconstruction':self.dense_reconstruction, 'textured_reconstruction':self.textured_reconstruction,
                         'new_photos_matching_number': self.newPhotosMatchingNumber, 'automatic_photo_source' : None, 'roi_scale':None},
                        f, sort_keys = True, indent = 4)

            elif os.path.isfile(inputPath): #if we are loading an old project
                print "LOADING PROJECT"
                self.url                = inputPath
                self.outputDir          = os.path.dirname(inputPath)
                self.backupUrl = os.path.join(self.outputDir, self.projectStatusBackupFileName)
                self.inputDir           = os.path.join(self.outputDir, '..')
                self.loadStatus()

            self.scriptDir                          = os.path.dirname(inspect.getfile(inspect.currentframe()))
            self.openMVGSensorWidthFile             = os.path.join(self.scriptDir,          self.openMVGSensorWidthFileName)
            self.featuresDir                        = os.path.join(self.outputDir,          self.featuresFolderName)
            self.matchesDir                         = os.path.join(self.outputDir,          self.matchesFolderName)
            self.matchesBackupDir                   = os.path.join(self.outputDir,          self.matchesBackupFolderName)
            self.incrMatchesDir                     = os.path.join(self.outputDir,          self.incrMatchesFolderName)
            self.reconstructionDir                  = os.path.join(self.outputDir,          self.reconstructionFolderName)
            self.matchesFile                        = os.path.join(self.matchesDir,         self.openMVGMatchesFileName)
            self.geoMatchesFile                     = os.path.join(self.matchesDir,         self.openMVGGeoMatchesFileName)
            self.namedGeoMatchesFile                = os.path.join(self.matchesDir,         self.openMVGNamedGeoMatchesFileName)
            self.imageListingFile                   = os.path.join(self.featuresDir,        self.openMVGListingFileName)
            self.imageListingBackupFile             = os.path.join(self.featuresDir,        self.openMVGListingBackupFileName)
            self.incrImageListingFile               = os.path.join(self.incrMatchesDir,     self.openMVGListingFileName)
            self.incrPairListFile                   = os.path.join(self.incrMatchesDir,     self.openMVGPairListFileName)
            self.incrMatchesFile                    = os.path.join(self.incrMatchesDir,     self.openMVGMatchesFileName)
            self.incrGeoMatchesFile                 = os.path.join(self.incrMatchesDir,     self.openMVGGeoMatchesFileName)
            self.openMVGSfMOutputFile               = os.path.join(self.reconstructionDir,  self.openMVGSfMOutputFileName)
            self.openMVGSfMJSONOutputFile           = os.path.join(self.reconstructionDir,  self.openMVGSfMJSONOutputFileName)
            self.openMVGSfMColorizedOutputFile      = os.path.join(self.reconstructionDir,  self.openMVGSfMColorizedOutputFileName)
            self.openMVGSfMInitialStructureFile     = os.path.join(self.reconstructionDir,  self.openMVGSfMInitialStructureFileName)
            self.openMVGSfMRotationGraphFile        = os.path.join(self.reconstructionDir,  self.openMVGRotationGraphFileName)
            self.mveDir                             = os.path.join(self.reconstructionDir,  self.mveFolderName)
            self.mveViewsDir                        = os.path.join(self.mveDir,             self.mveViewsFolderName)
            self.mveMainFile                        = os.path.join(self.mveDir,             self.mveMainFileName)
            self.mveScene2PsetOutputFile            = os.path.join(self.reconstructionDir,  self.mveScene2PsetOutputFileName)
            self.mvePsetCleanOutputFile             = os.path.join(self.reconstructionDir,  self.mvePsetCleanOutputFileName)
            self.mveFSSReconOutputFile              = os.path.join(self.reconstructionDir,  self.mveFSSReconOutputFileName)
            self.mveMeshCleanOutputFile             = os.path.join(self.reconstructionDir,  self.mveMeshCleanOutputFileName)
            self.mveTextureOutputFile               = os.path.join(self.reconstructionDir,  self.mveTextureOutputFileName)
            self.mveTextureOutputFileNoExtension    = os.path.join(self.reconstructionDir,  self.mveTextureOutputFileNameNoExtension)

            if not os.path.exists(self.featuresDir):
                os.mkdir(self.featuresDir)
            if not os.path.exists(self.matchesDir):
                os.mkdir(self.matchesDir)
            if not os.path.exists(self.incrMatchesDir):
                os.mkdir(self.incrMatchesDir)
            if not os.path.exists(self.reconstructionDir):
                os.mkdir(self.reconstructionDir)
            if not os.path.exists(self.mveDir):
                os.mkdir(self.mveDir)
        else:
            print "Path %s doesn't exists!" % inputPath

    def getPaths(self):
        return self.inputDir, self.outputDir, self.featuresDir, self.matchesDir, self.incrMatchesDir, self.reconstructionDir

    def loadStatus(self):
        with open(self.url) as f:
            #print f.read()
            jsonStatus                  = json.load(f)
            self.photos                 = jsonStatus['photos']
            self.wrong_photos           = jsonStatus['wrong_photos']
            self.mode                   = jsonStatus['mode']
            self.successful             = jsonStatus['status']
            self.sparse_reconstruction  = jsonStatus['sparse_reconstruction']
            self.dense_reconstruction   = jsonStatus['dense_reconstruction']
            self.textured_reconstruction= jsonStatus['textured_reconstruction']
            self.newPhotosMatchingNumber= jsonStatus['new_photos_matching_number']
            self.automatic_photo_source = jsonStatus['automatic_photo_source']
            self.roi_scale              = jsonStatus['roi_scale']

    def saveCurrentStatus(self):
        jsonStatus = {'status': self.successful, 'mode':self.mode, 'photos':self.photos, 'wrong_photos':self.wrong_photos,
                      'sparse_reconstruction':self.sparse_reconstruction, 'dense_reconstruction':self.dense_reconstruction,
                      'textured_reconstruction':self.textured_reconstruction,
                      'new_photos_matching_number':self.newPhotosMatchingNumber, 'automatic_photo_source':self.automatic_photo_source,
                      'roi_scale':self.roi_scale}
        with open(self.url, 'w') as f:
            json.dump(jsonStatus, f, sort_keys = True, indent = 4 )
        return jsonStatus

    def editStatus(self):
        os.system("gedit " + self.url)
        self.loadStatus()

    def getJsonStatus(self):
        with open(self.url) as f:
            return json.load(f)

    def getOldPhotos(self):
        return list(self.photos+self.wrong_photos)

    def getLastAddedPhotos(self):
        backup_photos = []
        with open(self.backupUrl) as f:
            jsonBackupStatus = json.load(f)
            backup_photos = jsonBackupStatus['photos']
            backup_wrong_photos = jsonBackupStatus['wrong_photos']
        last_added_photos = list(set(self.photos + self.wrong_photos) - set(backup_photos + backup_wrong_photos))
        return last_added_photos
