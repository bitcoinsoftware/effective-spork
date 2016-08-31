import support_functions
import json
import os
import re
import ast
from collections import OrderedDict

from PIL import Image
from PIL.ExifTags import TAGS

class SfMDataGenerator:
    def __init__(self, projectStatus, log = None):
        self.projectStatus = projectStatus
        self.log = log
        #['ExifImageWidth', 'ExifImageHeight', 'Make', 'Model', 'ExifImageWidth', 'ExifImageHeight', 'FocalLength']

    def getExifDict(self, imageUrl):
        if os.path.isfile(imageUrl):
            exifTags = ['ExifImageWidth', 'ExifImageHeight', 'Make', 'Model', 'ExifImageWidth', 'ExifImageHeight', 'FocalLength']
            exifDict = {}
            for (k, v) in Image.open(imageUrl)._getexif().iteritems():
                tag = TAGS.get(k)
                if tag in exifTags:
                    if type(v) == type(u'test'):
                        v = v.rstrip().rstrip('\x00')
                    exifDict[tag] = v
            if set(exifDict.keys()) == set(exifTags):
                return exifDict
        return None

    def getSfMData(self):
        sfmData     = OrderedDict()
        sfmData["sfm_data_version"] = "0.2"
        sfmData["root_path"]        = self.projectStatus.inputDir

        optics      = [] #stores dicts with exif data
        intrinsics  = [] #stores intrinsic data ready to save in sfm_data
        views       = [] #stores the photo info

        imageList       = support_functions.getImagesList(self.projectStatus.inputDir)
        photosNumber    = len(imageList)
        key = 0
        startId = 2147483649

        for imageName in imageList:
            exifDict = self.getExifDict(os.path.join(self.projectStatus.inputDir, imageName))
            if exifDict == None:
                if self.log:
                    self.log(["Error:Exif data in photo %s not found" % imageName])
                return
            else:
                if exifDict in optics:
                    """ The photo was made with an allready registered camera """
                    intrinsic_key = optics.index(exifDict)
                else:
                    """ The photo was made with a new camera or the params of the foto changed, generate a new intrinsic """
                    intrinsic_key = len(optics)
                    optics.append(exifDict)
                    """ Append a new intrinsic """
                    intrData = self.getIntrinsic(exifDict, photosNumber, key = len(intrinsics), startId =startId )
                    if intrData == None:
                        return
                    intrinsics.append(intrData)
            """ Append a new view """
            views.append(self.getView(imageName, exifDict, key = key, intrinsicKey = intrinsic_key, id = startId + key))
            key += 1

        sfmData["views"]            = views
        sfmData["intrinsics"]       = intrinsics
        sfmData["extrinsics"]       = []
        sfmData["structure"]        = []
        sfmData["control_points"]   = []
        sfmData["optics"]           = optics
        with open(self.projectStatus.imageListingFile, 'w') as f:
            f.write(json.dumps(sfmData, indent=4))
        return sfmData

    def getIntrinsic(self, exifDict, photosNumber, key, startId):
        #focal = std::max ( width, height ) * exifReader->getFocal() / ccdw;
        ccdWidth  = self.getSensorWidth(exifDict["Make"], exifDict["Model"])
        if ccdWidth:
            #TODO verify that focal is a tuple and there is no 0 division
            focalMM = exifDict["FocalLength"][0]/float(exifDict["FocalLength"][1])
            focal = max(exifDict["ExifImageWidth"], exifDict["ExifImageHeight"]) * focalMM / ccdWidth
            if key == 0:
                polymorphic_id = startId
            else:
                polymorphic_id = 1
            outDict = OrderedDict(
                {
                       'key':key,
                       'value':
                           {
                            "polymorphic_id"    : polymorphic_id,
                            "polymorphic_name"  : "pinhole_radial_k3",
                            "ptr_wrapper"       :
                                {
                                        "id": photosNumber + key + startId,
                                        "data": {
                                            "width": exifDict["ExifImageWidth"],
                                            "height": exifDict["ExifImageHeight"],
                                            "focal_length": focal,
                                            "principal_point":
                                                    [
                                                    exifDict["ExifImageWidth"]/2,
                                                    exifDict["ExifImageHeight"]/2
                                                    ],
                                                    "disto_k3": [
                                                            0,
                                                            0,
                                                            0 ]
                                                }
                                }
                            }
                })
            return outDict
        return


    def getView(self, filename, exifDict, key, intrinsicKey, id):
        outDict = OrderedDict(
        {
            "key": key,
            "value": {
                "ptr_wrapper":{
                    "id": id,
                    "data": {
                        "local_path": "/",
                        "filename": filename,
                        "width": exifDict["ExifImageWidth"],
                        "height": exifDict["ExifImageHeight"] ,
                        "id_view": key,
                        "id_intrinsic": intrinsicKey,
                        "id_pose": key
                    }
                }
            }
        })
        return outDict

    def getSensorWidth(self, make, model):
        with open(self.projectStatus.openMVGSensorWidthFile) as f:
            dbContent = f.read()

            sensorLines = self.findCameraLines(make, model, dbContent)
            if sensorLines:
                parts = sensorLines[0].split(';')
                if len(parts) == 2:
                    if  parts[1].replace('.','').strip().isdigit(): #if it's a number
                        return ast.literal_eval(parts[1])
        if self.log:
            self.log(["Error:Could not find MAKE = %s MODEL = %s CCD sensor width in file %s" % (make, model, self.projectStatus.openMVGSensorWidthFile)])
        return None

    def findCameraLines(self, make, model, dbContent):
        options     = [" ".join([make, model])]
        options.append(" ".join([make, model.lower()]))
        options.append(" ".join([make, model.upper()]))
        options.append(" ".join([make, model.title()]))

        options.append(" ".join([make.lower(), model]))
        options.append(" ".join([make.lower(), model.lower()]))
        options.append(" ".join([make.lower(), model.upper()]))
        options.append(" ".join([make.lower(), model.title()]))

        options.append(" ".join([make.upper(), model]))
        options.append(" ".join([make.upper(), model.lower()]))
        options.append(" ".join([make.upper(), model.upper()]))
        options.append(" ".join([make.upper(), model.title()]))

        options.append(" ".join([make.title(), model]))
        options.append(" ".join([make.title(), model.lower()]))
        options.append(" ".join([make.title(), model.upper()]))
        options.append(" ".join([make.title(), model.title()]))

        options.append(model)
        options.append(model.lower())
        options.append(model.upper())
        options.append(model.title())

        for option in options:
            sensorLines = re.findall(option + ".*$", dbContent, re.MULTILINE)
            if len(sensorLines) >0:
                return sensorLines
        return None

    #TODO
    def generateIncrementalSfMData(self, oldSfMDataFileUrl, newPhotoList):
        with open(oldSfMDataFileUrl) as f:
            oldSfMData      = json.load(f)
            folderPath      = oldSfMData["root_path"]
            oldViewList     = oldSfMData["views"]
            oldIntrinsics   = oldSfMData["intrinsics"]
            oldOptics       = oldSfMData["optics"] #[{"CAMERA MODEL":focal}, {"CAMERA MODEL1":focal1}]

        #return incrementedSfMData
        return None
