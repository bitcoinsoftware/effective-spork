import unittest
import os, json
import numpy as np
from .. import ProjectMerge
from .. import ProjectStatus

class Test_ProjectMerge(unittest.TestCase):
    pso1_url = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "projectMerge", "part1", "output", "projectStatus.json")
    pso1 = ProjectStatus.ProjectStatus(pso1_url)

    pso2_url = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "projectMerge", "part2", "output", "projectStatus.json")
    pso2 = ProjectStatus.ProjectStatus(pso2_url)


    def test_getViewIntrinsicParams(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            pso_1_listing = json.load(f1)

            views = pso_1_listing['views']
            intrinsics = pso_1_listing['intrinsics']

            v0 = views[0]
            intrinsic_params = pm.getViewIntrinsicParams(v0, intrinsics)
            self.assertEqual([2320.7751431748384, 4000, 3000], intrinsic_params)

            vk = views[-1]
            intrinsic_params = pm.getViewIntrinsicParams(vk, intrinsics)
            self.assertEqual([2997.774357706606, 4496, 3000], intrinsic_params)

    def test_getViewsParamsList(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            pso_1_listing = json.load(f1)

            views_params = pm.getViewsParamsList(pso_1_listing)
            theoretical_answer = [
             '["DJI_0001.JPG", [4000, 3000]]',
             '["DJI_0002.JPG", [4000, 3000]]',
             '["DJI_0003.JPG", [4000, 3000]]',
             '["DJI_0004.JPG", [4000, 3000]]',
             '["DJI_0005.JPG", [4000, 3000]]',
             '["DJI_0006.JPG", [4000, 3000]]',
             '["DSC_0179.JPG", [4496, 3000]]']

            self.assertEqual(views_params, theoretical_answer)

    def test_getTwinPhotoNames(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        twin_photo_names = pm.getTwinPhotoNames()
        theoretical_answer = [u'DJI_0004.JPG', u'DJI_0006.JPG', u'DJI_0005.JPG', u'DSC_0179.JPG']
        self.assertEqual(twin_photo_names, theoretical_answer)

    def test_getTwinPhotos(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        twin_photo_names = pm.getTwinPhotos()
        theoretical_answer = [u'DJI_0004.JPG', u'DJI_0006.JPG', u'DJI_0005.JPG', u'DSC_0179.JPG']
        self.assertEqual(twin_photo_names, theoretical_answer)

    def test_getViewIdAndPoseId(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            pso_1_listing = json.load(f1)
            #print pm.getViewIdAndPoseId("DSC_0179.JPG", pso_1_listing["views"])
        with open(self.pso2.openMVGSfMJSONOutputFile) as f2:
            pso_2_listing = json.load(f2)
            #print pm.getViewIdAndPoseId("DSC_0179.JPG", pso_2_listing["views"])

    def test_getPoseCenterAndRotation(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        with open(self.pso1.openMVGSfMJSONOutputFile) as f1:
            pso_1_listing = json.load(f1)
            #print pm.getPoseCenterAndRotation(1, pso_1_listing['extrinsics'])

    def test_getViewData(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        twinPhotoName = pm.getTwinPhotoNames()[0]
        #print pm.getViewData(twinPhotoName)

    def test_getTwinPoses(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        twinPoses = pm.getTwinPoses()
        #print twinPoses

    def test_getTransformationMatrix(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        twinPoses = pm.getTwinPoses()
        """
        s_p1 = np.array(twinPoses[0]['pose_center'][0] )
        s_p1.shape = (3,1)
        p_p1 = np.array(twinPoses[0]['pose_center'][1] )
        p_p1.shape = (3,1)
        print twinPoses[0]["name"],  p_p1 - s_p1

        s_p2 = np.array(twinPoses[1]['pose_center'][0])
        s_p2.shape = (3,1)
        p_p2 = np.array(twinPoses[1]['pose_center'][1])
        p_p2.shape = (3,1)
        print twinPoses[1]["name"], p_p2 - s_p2

        s_p3 = np.array(twinPoses[2]['pose_center'][0])
        s_p3.shape = (3,1)
        p_p3 = np.array(twinPoses[2]['pose_center'][1])
        p_p3.shape = (3,1)
        print twinPoses[2]["name"], p_p3 - s_p3

        s_p4 = np.array(twinPoses[3]['pose_center'][0])
        s_p4.shape = (3,1)
        p_p4 = np.array(twinPoses[3]['pose_center'][1])
        p_p4.shape = (3,1)
        print twinPoses[3]["name"], p_p4 - s_p4
        """


        #substractMatrix = np.array([twinPoses[0]['pose_center'][0] + [0], twinPoses[1]['pose_center'][0] + [0], twinPoses[2]['pose_center'][0] + [0], np.array([0,0,0,1])], dtype=np.float64)
        #productMatrix   = np.array([twinPoses[0]['pose_center'][1] + [0], twinPoses[1]['pose_center'][1] + [0], twinPoses[2]['pose_center'][1] + [0], np.array([0,0,0,1])], dtype=np.float64)


    def test_getTransformationMatrix(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        twinNames = pm.getTwinPhotos()
        tm= pm.getTransformationMatrix(twinNames)


        v = [
                -0.021046670260812347,
                0.27156776791372739,
                1.7699788350567121,
                0
            ]

        print np.dot(tm, v)

        v = [
            -0.34307160550124544,
            0.29449522610308648,
            1.4909544294837009,
            0
        ]

        print np.dot(tm, v)

    def test_mergeProjects(self):
        pm = ProjectMerge.ProjectMerge(self.pso1, self.pso2)
        output_sfm_url = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/merged"
        pm.mergeProjects(self.pso1.url, self.pso2.url, output_sfm_url)

