import unittest, os, json

from .. import ProjectStatus
from .. import ProjectMerge

class Test_ProjectMerge(unittest.TestCase):
    pso1_url = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "projectMerge", "part1", "output", "projectStatus.json")
    pso1 = ProjectStatus.ProjectStatus(pso1_url)

    pso2_url = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "projectMerge", "part2", "output", "projectStatus.json")
    pso2 = ProjectStatus.ProjectStatus(pso2_url)

    output_url = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/merged"

    def test_getMode(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        mode = pm.getMode(self.pso1, self.pso2)
        self.assertEqual(mode , "HIGH")

    def test_verifyCameraRedundancy(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        isDoubled = pm.verifyCameraRedundancy(os.path.join(self.output_url, "DJI_0001.JPG"), os.path.join(self.output_url, "DSC_0179.JPG"))
        self.assertEqual(isDoubled, False)
        url  = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/part1"
        url2 = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/part2"
        isDoubled = pm.verifyCameraRedundancy(os.path.join(url, "DJI_0006.JPG"),os.path.join(url2, "DJI_0006.JPG"))
        self.assertEqual(isDoubled, True)


    def test_getTwinNames(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        tn, tnOE = pm.getTwinNames()
        theo_ans = [u'DJI_0004.JPG', u'DJI_0006.JPG', u'DJI_0005.JPG', u'DSC_0179.JPG']
        self.assertEqual(tn, theo_ans)


    def test_getIntrinsicRelatedViews(self):
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            pm  = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
            irv = pm.getIntrinsicRelatedViews(sfmJSON)
            theo_ans = {0:[0,1,2,3,4,5], 1:[6]}
            self.assertEqual(theo_ans, irv)


    def test_getIntrinsicRelatedPhotoNames(self):
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            pm  = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
            irpn = pm.getIntrinsicRelatedPhotoNames(sfmJSON)
            theo_ans = {u'DJI_0001.JPG':0,u'DJI_0002.JPG':0,u'DJI_0003.JPG':0,u'DJI_0004.JPG':0,u'DJI_0005.JPG':0,u'DJI_0006.JPG':0, u'DSC_0179.JPG':1}
            self.assertEqual(theo_ans, irpn)


    def test_getIntrinsicTransformationDict(self):
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
                sfmJSON_2 = json.load(f2)
                pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
                tn, tnOE = pm.getTwinNames()
                itd = pm.getIntrinsicTransformationDict(sfmJSON, sfmJSON_2, tn)
                theo_ans = {0:0, 1:1}
                self.assertEqual(itd, theo_ans )


    def test_getRelationDict(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        tn, tnOE = pm.getTwinNames()
        rd = pm.getRelationDict(tn)
        theo_ans = {3:0, 4:1, 5:2, 6:3}
        self.assertEquals(theo_ans, rd)


    def test_addIntrinsics(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
                sfmJSON_2 = json.load(f2)
                intr = pm.addIntrinsiscs(sfmJSON, sfmJSON_2, pm.getTwinNames())
                theo_ans = [
        {
            u"key": 0,
            u"value": {
                u"polymorphic_id": 2147483649,
                u"polymorphic_name": u"pinhole_radial_k3",
                u"ptr_wrapper": {
                    u"id": 2147483659,
                    u"data": {
                        u"width": 4000,
                        u"height": 3000,
                        u"focal_length": 2320.7751431748384,
                        u"principal_point": [
                            2041.4128165549462,
                            1488.0649496997025
                        ],
                        u"disto_k3": [
                            0.0013636565538295599,
                            -0.028123325754963405,
                            0.029768404230051403
                        ]
                    }
                }
            }
        },
        {
            u"key": 1,
            u"value": {
                u"polymorphic_id": 1,
                u"ptr_wrapper": {
                    u"id": 2147483660,
                    u"data": {
                        u"width": 4496,
                        u"height": 3000,
                        u"focal_length": 2997.7743577066062,
                        u"principal_point": [
                            2510.7497791332335,
                            1756.943091049834
                        ],
                        u"disto_k3": [
                            -0.086813719746706153,
                            0.029995541745990527,
                            -0.021619581284865054
                        ]
                    }
                },
            }

        },
        {
            u"key": 2,
            u"value":{
                u"polymorphic_id": 1,
                u"polymorphic_name": u"pinhole_radial_k3",
                u"ptr_wrapper": {
                    u"id": 2147483661,
                    u"data": {
                        u"width": 4000,
                        u"height": 3000,
                        u"focal_length": 2324.4662981017054,
                        u"principal_point": [
                            2025.1565497253002,
                            1484.626109327932
                                ],
                        u"disto_k3": [
                            -0.004851133861251552,
                            -0.0038897061689192602,
                            0.00956874826210494
                            ]
                            }
                        },
                    }

        },
        {

            u"key": 3,
            u"value": {
                u"polymorphic_id": 1,
                u"ptr_wrapper": {
                    u"id": 2147483662,
                    u"data": {
                        u"width": 4496,
                        u"height": 3000,
                        u"focal_length": 3542.9579540551554,
                        u"principal_point": [
                            2259.830829213586,
                            1495.9504782669449
                        ],
                        u"disto_k3": [
                            -0.09259562538396089,
                            0.009749858367327039,
                            0.011226976801141141
                        ]
                    }
                },
            }
        }
        ]
        self.maxDiff = None
        self.assertEqual(intr, theo_ans)


    def test_getMergedExtrinsics(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
                sfmJSON_2 = json.load(f2)
                tn, tnOE = pm.getTwinNames()
                rd = pm.getRelationDict(tn)
                pm.computeTransformations(sfmJSON, sfmJSON_2)
                pm.getMergedExtrinsics(sfmJSON, sfmJSON_2)


    def test_getMergedStructure(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
                sfmJSON_2 = json.load(f2)
                tn, tnOE = pm.getTwinNames()
                rd = pm.getRelationDict(tn)
                pm.computeTransformations(sfmJSON, sfmJSON_2)
                pm.getMergedStructure(sfmJSON, sfmJSON_2)

    def test_getMergedViews(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
                sfmJSON_2 = json.load(f2)
                tn, tnOE = pm.getTwinNames()
                rd = pm.getRelationDict(tn)
                pm.getIntrinsicTransformationDict(sfmJSON, sfmJSON_2, tn)
                pm.getMergedViews(sfmJSON, sfmJSON_2, name_trans_dict = {})

    def test_mergeSfMFiles(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        pm.mergeSfMFiles(self.pso1.openMVGSfMJSONOutputFile, self.pso2.openMVGSfMJSONOutputFile, os.path.join(self.output_url, 'output', 'reconstruction_global','sfm_data.json'), self.output_url, )

    def test_computeTransformations(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2, self.output_url)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            sfmJSON = json.load(f1)
            with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
                sfmJSON_2 = json.load(f2)
                tn, tnOE = pm.getTwinNames()
                rd = pm.getRelationDict(tn)
                pm.computeTransformations(sfmJSON, sfmJSON_2)

    def test_mergeProjects(self):
        url_out = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/merged"
        pso1 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part1/output/projectStatus.json")
        pso2 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part2/output/projectStatus.json")
        pm = ProjectMerge.ProjectMerge(pso1, pso2, url_out)
        pm.mergeProjects(mode = "NORMAL")