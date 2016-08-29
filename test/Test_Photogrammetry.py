import unittest
import os
from .. import Photogrammetry
from .. import ProjectStatus

class Test_Photogrammetry(unittest.TestCase):
    projectStatusUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "meadow", "output", "projectStatus.json")
    ps = ProjectStatus.ProjectStatus(projectStatusUrl)
    pg = Photogrammetry.Photogrammetry(ps)

    def test_fileNotEmpty(self):
        testFileUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "test_file")
        self.assertEqual(self.pg.fileNotEmpty(testFileUrl), True)
        testFileUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "empty_test_file")
        self.assertEqual(self.pg.fileNotEmpty(testFileUrl), False)
        testFileUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "FALSEURL")
        self.assertEqual(self.pg.fileNotEmpty(testFileUrl), False)

    def test_getNodeSymbolsAndImgNamesFromSfMJson(self):
        sfmJsonUrl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "meadow", "output", "features", "sfm_data.json")
        name_list = self.pg.getNodeSymbolsAndImgNamesFromSfMJson(sfmJsonUrl)
        #print name_list
        theoreticalAnswer = [['n0', 'DJI_000?', 'JPG'], ['n1', 'DJI_000@', 'JPG'], ['n2', 'DJI_000A', 'JPG'], ['n3', 'DJI_000B', 'JPG'], ['n4', 'DJI_000C', 'JPG'], ['n5', 'DJI_000D', 'JPG']]
        self.assertEqual(theoreticalAnswer, name_list)

    def test_getNodeMatches(self):
        node_matches = self.pg.getNodeMatches(0)
        theoreticalAnswer = [1, 3, 4, 5]
        self.assertEqual(theoreticalAnswer, node_matches)

    def test_getMatchesList(self):
        node_matches = self.pg.getMatchesList([0, 1])
        theoreticalAnswer = [0,1,2,3,4,5]
        self.assertEqual(node_matches, theoreticalAnswer)

    def test_getNewestNodes(self):
        nodes = self.pg.getNewestNodes(3)
        self.assertEquals([1,3,4], nodes)

    def test_getROI(self):
        roi =  self.pg.getROI(1)
        theoreticalAnswer = [-0.384887, -0.0354083, -0.376969, -0.00582268, 0.353022, -0.16858]
        self.assertEqual(roi, theoreticalAnswer)

        #roi = self.pg.getROI(scale = 2)
        #theoreticalAnswer = [-0.5681362050000001, 0.18083261499999997, -0.23808439999999997, 0.5398988, -0.465235, -0.07111499999999998]
        #self.assertEqual(roi, theoreticalAnswer)

    def test_getReinforcingPairListString(self):
        pair_list = self.pg.getReinforcingPairListString([0,1,2,3,4,5])
        self.assertEqual('0 2\n', pair_list)
