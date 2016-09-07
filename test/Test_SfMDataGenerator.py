import unittest
import os
import json

from .. import support_functions
from .. import ProjectStatus
from .. import SfMDataGenerator

class Test_SfMDataGenerator(unittest.TestCase):
    projectStatusUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "meadow", "output", "projectStatus.json")
    ps = ProjectStatus.ProjectStatus(projectStatusUrl)
    sfmdg = SfMDataGenerator.SfMDataGenerator(ps)

    def test_getSensorWidth(self):
        make, model = "Nikon", "D3300"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        theoreticalAnswer = 23.5
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "NIKON", "D3300"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "nikon", "D3300"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "NIKON CORPORATION", "NIKON D3300"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "DJI", "FC300X"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        theoreticalAnswer = 6.16
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "", "FC300X"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "dji", "FC300X"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "", "fc300x"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        self.assertEqual(theoreticalAnswer, sensorWidth)

        make, model = "krecone", "kalkulatorem"
        sensorWidth = self.sfmdg.getSensorWidth(make, model)
        theoreticalAnswer = None
        self.assertEqual(theoreticalAnswer, sensorWidth)

    def test_getExifDict(self):
        exifDict = self.sfmdg.getExifDict(os.path.join(self.ps.inputDir, 'test1.JPG'))
        theoreticalAnswer = {'FocalLength': [610, 100], 'ExifImageWidth': 2304, 'Make': 'FUJIFILM', 'ExifImageHeight': 1728, 'Model': 'A850'}
        self.assertEqual(theoreticalAnswer, exifDict)

        exifDict = self.sfmdg.getExifDict(os.path.join(self.ps.inputDir, 'DJI_000D.JPG'))
        theoreticalAnswer = {'FocalLength': [361, 100], 'ExifImageWidth': 4000, 'Make': 'DJI', 'ExifImageHeight': 3000, 'Model': 'FC300X'}
        self.assertEqual(theoreticalAnswer, exifDict)

        exifDict = self.sfmdg.getExifDict(os.path.join(self.ps.inputDir, 'chuj.JPG'))
        theoreticalAnswer = None
        self.assertEqual(theoreticalAnswer, exifDict)

    def test_getIntrinsic(self):
        exifDict = self.sfmdg.getExifDict(os.path.join(self.ps.inputDir, 'test1.JPG'))
        intrinsic = self.sfmdg.getIntrinsic(exifDict, 4 , 0)
        theoreticalAnswer = {
            'value':
             {'ptr_wrapper':
                       {'data':
                            {'width': 2304,
                             'principal_point': [1152, 864],
                             'disto_k3': [0, 0, 0],
                             'focal_length': 2444.2434782608693,
                             'height': 1728
                             },
                        'id': 2147483653
                        },
                   'polymorphic_name': 'pinhole_radial_k3',
                   'polymorphic_id': 2147483649
                   },
         'key': 0}
        self.assertEqual(theoreticalAnswer, intrinsic)


    def test_getView(self):
        filename = 'test1.JPG'
        key = 0
        intrinsicKey = 0
        exifDict = self.sfmdg.getExifDict(os.path.join(self.ps.inputDir, 'test1.JPG'))
        view = self.sfmdg.getView(filename, exifDict, key, intrinsicKey)
        theoreticalAnswer = {
            'value': {
                'ptr_wrapper': {
                    'data': {
                        'filename': 'test1.JPG',
                        'height': 1728,
                        'width': 2304,
                        'local_path': '/',
                        'id_view': 0,
                        'id_intrinsic': 0,
                        'id_pose': 0},
                    'id': 2147483649}
                },
            'key': 0
        }
        self.assertEqual(view, theoreticalAnswer, None)


    def log(self, strArray):
        for msg in strArray:
            print msg

    #TODO
    def test_getSfMData(self):
        projectStatusUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sfmDataGenerator_Test", "output", "projectStatus.json")
        ps = ProjectStatus.ProjectStatus(projectStatusUrl)
        sfmdg = SfMDataGenerator.SfMDataGenerator(ps, self.log)
        sfmdata = sfmdg.getSfMData()

        #print "DATA:", sfmdata


    #TODO
    def test_getIncrementalSfMData(self):
        projectStatusUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sfmDataGenerator_Test_incrementalListing",
                                        "output", "projectStatus.json")
        print projectStatusUrl
        ps = ProjectStatus.ProjectStatus(projectStatusUrl)
        sfmdg = SfMDataGenerator.SfMDataGenerator(ps, self.log)
        sfmdata = sfmdg.getIncrementalSfMData(['DJI_000B.JPG'], oldSfMDataUrl = ps.imageListingFile, inputPhotoDir = ps.inputDir, )
        #getIncrementalSfMData(self, newPhotoList, oldSfMDataUrl, inputPhotoDir, outputSfMDataUrl=None)

        print  json.dumps(sfmdata, indent=4)
