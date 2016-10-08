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


    def test_experiment(self):
        pass
        """
        import numpy as np
        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, - 1.15654966e-16])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02,   2.22044605e-16])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00,   1.66533454e-16])
        tm.append([1.24976956e-01,  - 6.12366254e-02, - 9.27338090e-01,   1.00000000e+00])
        tm = np.array(tm)
        print "Begining: \n", tm

        print "Transposed: \n", np.transpose(tm)

        tm1 = np.transpose(tm)
        sx = np.dot(tm1[0], tm1[0])
        sy = np.dot(tm1[1], tm1[1])
        sz = np.dot(tm1[2], tm1[2])
        print "S1. sx=%f sy=%f sz=%f" % (sx, sy, sz)

        tm1[0] = np.array(tm1[0])/sx
        tm1[1] = np.array(tm1[1])/sy
        tm1[2] = np.array(tm1[2])/sz
        print "Scaled 1: \n", tm1
        print"#####################################"

        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, - 1.15654966e-16])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02,   2.22044605e-16])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00,   1.66533454e-16])
        tm.append([1.24976956e-01,  - 6.12366254e-02, - 9.27338090e-01,   1.00000000e+00])
        tm = np.array(tm)

        tm1 = tm
        sx = np.dot(tm1[0], tm1[0])
        sy = np.dot(tm1[1], tm1[1])
        sz = np.dot(tm1[2], tm1[2])
        print "S2. sx=%f sy=%f sz=%f" % (sx, sy, sz)

        tm1[0] = np.array(tm1[0])/sx
        tm1[1] = np.array(tm1[1])/sy
        tm1[2] = np.array(tm1[2])/sz
        print "Scaled 2: \n", tm1

        print"#####################################"

        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, 0])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02, 0])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00, 0])
        tm.append([0,           0,              0,            1.00000000e+00])
        tm = np.array(tm)

        tm1 = tm
        sx = np.dot(tm1[0], tm1[0])
        sy = np.dot(tm1[1], tm1[1])
        sz = np.dot(tm1[2], tm1[2])
        print "S3. sx=%f sy=%f sz=%f" % (sx, sy, sz)

        tm1[0] = np.array(tm1[0])/sx
        tm1[1] = np.array(tm1[1])/sy
        tm1[2] = np.array(tm1[2])/sz
        print "Scaled 3: \n", tm1


        print"#####################################"

        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, 0])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02, 0])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00, 0])
        tm.append([0,           0,              0,            1.00000000e+00])
        tm = np.array(tm)

        tm1 = np.transpose(tm)
        sx = np.dot(tm1[0], tm1[0])
        sy = np.dot(tm1[1], tm1[1])
        sz = np.dot(tm1[2], tm1[2])
        print "S4. sx=%f sy=%f sz=%f" % (sx, sy, sz)

        tm1[0] = np.array(tm1[0])/sx
        tm1[1] = np.array(tm1[1])/sy
        tm1[2] = np.array(tm1[2])/sz
        print "Scaled 4: \n", tm1


        print"#####################################"

        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, 0])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02, 0])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00, 0])
        tm.append([0,           0,              0,            1.00000000e+00])
        tm = np.array(tm)

        tm1 = np.transpose(tm)
        #sx = np.dot(tm1[0], tm1[0])
        #sy = np.dot(tm1[1], tm1[1])
        #sz = np.dot(tm1[2], tm1[2])
        #print "S5. sx=%f sy=%f sz=%f" % (sx, sy, sz)

        tm1[0] = np.array(tm1[0])/sx
        tm1[1] = np.array(tm1[1])/sy
        tm1[2] = np.array(tm1[2])/sz
        print "Not Scaled 5: \n", tm1


        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, 0])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02, 0])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00, 0])
        tm.append([0,           0,              0,            1.00000000e+00])
        tm = np.array(tm)

        rm = np.array(
            [[0.99862614278660422, 0.0043208250668095331, -0.05222219273346012,   0],
             [-0.0052536207562669263, 0.99982886671926186, -0.017738002813899093, 0],
             [0.052136612971096868, 0.01798798892646427, 0.99847794459481343,     0],
             [   1,                  1,                      1,                  1]])

        #print "np.dot(rm, tm1[:3,:3]) \n",np.dot(rm, tm1[:3,:3])
        print tm1.shape, rm.shape
        print "$$$ ---> 1 \n", np.dot(np.transpose(tm), rm)
        print "$$$ ---> 2 \n", np.dot(tm, rm)
        print "$$$ ---> 3 \n", np.dot(rm, tm)
        print "$$$ ---> 4 \n", np.dot(np.transpose(rm), tm)
        print "$$$ ---> 5 \n", np.dot(np.transpose(rm), np.transpose(tm))

        print "####################"
        tm = []
        tm.append([7.84106293e-01, 6.98229290e-02, 2.68352754e-01, 0])
        tm.append([-8.59905447e-02, 8.39704868e-01, 2.75990766e-02, 0])
        tm.append([-2.49929837e-01, 6.56019049e-02, 1.37056303e+00, 0])
        tm.append([0, 0, 0, 1.00000000e+00])
        tm = np.array(tm)

        rm = np.array(
            [[0.99862614278660422, 0.0043208250668095331, -0.05222219273346012, 0],
             [-0.0052536207562669263, 0.99982886671926186, -0.017738002813899093, 0],
             [0.052136612971096868, 0.01798798892646427, 0.99847794459481343, 0],
             [0, 0, 0, 1]])

        # print "np.dot(rm, tm1[:3,:3]) \n",np.dot(rm, tm1[:3,:3])
        print tm1.shape, rm.shape
        print "$$$ ---> 1 \n", np.dot(np.transpose(tm), rm)
        print "$$$ ---> 2 \n", np.dot(tm, rm)
        print "$$$ ---> 3 \n", np.dot(rm, tm)
        print "$$$ ---> 4 \n", np.dot(np.transpose(rm), tm)
        print "$$$ ---> 5 \n", np.dot(np.transpose(rm), np.transpose(tm))
        """

    def test_experiment2(self):
        import numpy as np
        tm =[]
        tm.append([7.84106293e-01,    6.98229290e-02,   2.68352754e-01, 0])
        tm.append([-8.59905447e-02,   8.39704868e-01,   2.75990766e-02, 0])
        tm.append([-2.49929837e-01,   6.56019049e-02,   1.37056303e+00, 0])
        tm.append([1.24976956e-01,  - 6.12366254e-02, - 9.27338090e-01, 1])
        tm = np.array(tm)


        #print "Begining: \n", tm

        #sx = np.dot([tm[0,0], tm[0,1], tm[0,2] ], [tm[0,0], tm[0,1], tm[0,2] ])
        #sy = np.dot([tm[1,0], tm[1,1], tm[1,2] ], [tm[1,0], tm[1,1], tm[1,2] ])
        #sz = np.dot([tm[2,0], tm[2,1], tm[2,2] ], [tm[2,0], tm[2,1], tm[2,2] ])
        #print "S1. sx=%f sy=%f sz=%f" % (sx, sy, sz)

        tx = tm[:3,:3]
        #print tx

        g = np.linalg.svd(tx)
        #print "SVD\n", g

        rm = np.array(
            [[0.99862614278660422, 0.0043208250668095331, -0.05222219273346012      ],
             [-0.0052536207562669263, 0.99982886671926186, -0.017738002813899093    ],
             [0.052136612971096868, 0.01798798892646427, 0.99847794459481343        ]
             ])
        #print "RM\n", rm
        #print "XXXXX 1\n", np.dot(g[0], rm)
        #print "XXXXX 2\n", np.dot(g[2], rm)
        #print "XXXXX 3\n", np.dot(np.transpose(g[0]), rm)
        #print "XXXXX 4\n", np.dot(np.transpose(g[2]), rm)



    def test_mergeProjects(self):
        pso1 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part1/output/projectStatus.json")
        pso2 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part2/output/projectStatus.json")
        pm = ProjectMerge.ProjectMerge(pso1, pso2)
        output_sfm_url = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/merged"
        pm.mergeProjects(pso1.url, pso2.url, output_sfm_url)

