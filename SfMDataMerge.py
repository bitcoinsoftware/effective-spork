import json
import copy
import numpy as np
import math

class SfMDataMerge:

    def __init__(self, (sfm1, sfm2, sfm_out), root_path):
        self.first_polymorphic_id = 2147483649
        self.sfm1 = sfm1
        self.sfm2 = sfm2
        self.sfm_out = sfm_out
        self.SFM_JSON_OUT = {}
        self.SFM_JSON_OUT['root_path'] = root_path
        self.SFM_JSON_OUT['sfm_data_version'] = '0.2'
        self.SFM_JSON_OUT["control_points"] = []

    def getRelationDict(self, name_relation_dict):
        """Get a dictionary showing the relation between doubled photos,  project1 --> project2     {3:0, 4:1, 5:2, 6:3}"""
        self.relation_dict, self.inverse_relation_dict = {}, {}
        """Get list of twin view keys from first file"""
        pso_1_twin_keys, pso_1_twin_names = [], []
        with open(self.sfm1) as f1:
            #print "with open(self.sfm1) as f1:"
            views = json.load(f1)["views"]
            for view in views:
                filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                if filename in name_relation_dict.keys():
                    pso_1_twin_keys.append(view["key"])
                    pso_1_twin_names.append(filename)
                    print filename, view["key"]

            """Get list of twin view keys from second file"""
            pso_2_twin_keys, pso_2_twin_names = [], []
            with open(self.sfm2) as f2:
                #print "with open(self.sfm2) as f2:"
                views = json.load(f2)["views"]
                for view in views:
                    filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                    if filename in name_relation_dict.values():
                        pso_2_twin_keys.append(view["key"])
                        pso_2_twin_names.append(filename)
                        #print filename, view["key"]

                """Get a dict {pso1_key:pso2_key , ...} showing the relation between the views"""
                for i in xrange(len(pso_1_twin_names)):
                    filename = pso_1_twin_names[i]
                    key = pso_1_twin_keys[i]
                    pso_2_key = pso_2_twin_keys[pso_2_twin_names.index(name_relation_dict[filename])]
                    self.relation_dict[key] = pso_2_key
                    self.inverse_relation_dict[pso_2_key] = key


    def getIntrinsicTransformationDict(self, sfm_JSON, sfm_JSON_2, name_trans_dict):
        photo_name_intrinsic_relation_dict_1 = self._getIntrinsicRelatedPhotoNames(sfm_JSON)
        photo_name_intrinsic_relation_dict_2 = self._getIntrinsicRelatedPhotoNames(sfm_JSON_2)
        self.intrinsic_transformation_dict         = {}
        self.inverse_intrinsic_transformation_dict = {}
        for pso1_photo_name in name_trans_dict.keys():
            self.intrinsic_transformation_dict[photo_name_intrinsic_relation_dict_1[pso1_photo_name]]                          = photo_name_intrinsic_relation_dict_2[name_trans_dict[pso1_photo_name]]
            self.inverse_intrinsic_transformation_dict[photo_name_intrinsic_relation_dict_2[name_trans_dict[pso1_photo_name]]] = photo_name_intrinsic_relation_dict_1[pso1_photo_name]

    def _getIntrinsicRelatedPhotoNames(self, sfm_JSON):
        """Return a dict of {"PHOTONAME_0":0, "PHOTONAME_1":0}"""
        intr_rel_dict ={} #initialize
        for view in sfm_JSON["views"]:
            intr_rel_dict[view["value"]["ptr_wrapper"]["data"]["filename"]] = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
        return intr_rel_dict


    def getMergedViews(self, sfm_JSON, sfm_JSON_2, doubled_names_transformation_dict):
        """1. Iterate over proj1 and modify the intrinsic fields if required
           2. Iterate over proj2, if it's a dubbled view, pass it else change the keys, id_pose, id_view and id_intrinsic"""
        # 1. Iterate over proj1, modify the intrinsic key if in project2 there are more photos related to the same intrinsic
        intr_rel_views_1 = self._getIntrinsicRelatedViews(sfm_JSON)
        intr_rel_views_2 = self._getIntrinsicRelatedViews(sfm_JSON_2)
        views_last_key = sfm_JSON["views"][-1]["key"]
        views_last_id = sfm_JSON["views"][-1]["value"]["ptr_wrapper"]["id"]
        views_out = sfm_JSON["views"]
        i = 0
        for view in sfm_JSON["views"]: # Iterate over proj1 and modify the intrinsic fields if required
            intr_id = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
            if intr_id in self.intrinsic_transformation_dict.keys():  # if there are more photos made with the same intrinsic in the first project than choose this intrinsic
                if len(intr_rel_views_2[intr_id]) > len(intr_rel_views_1[self.intrinsic_transformation_dict[intr_id]]):
                    view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] = self.intrinsic_transformation_dict[intr_id] + len(self.intrinsic_transformation_dict.keys())
        i = 0
        for view in sfm_JSON_2["views"]:
            if view["key"] not in self.relation_dict.values(): #if it's not a doubled photo than we must append it
                i+=1
                view["key"]                                             = views_last_key + i
                view["value"]["ptr_wrapper"]["id"]                      = views_last_id + i
                view["value"]["ptr_wrapper"]["data"]["id_pose"]         = view["key"]
                view["value"]["ptr_wrapper"]["data"]["id_view"]         = view["key"]
                if view["value"]["ptr_wrapper"]["data"]["filename"] in doubled_names_transformation_dict.keys():
                    view["value"]["ptr_wrapper"]["data"]["filename"] = doubled_names_transformation_dict[view["value"]["ptr_wrapper"]["data"]["filename"]]
                intr_id = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
                if intr_id in self.inverse_intrinsic_transformation_dict.keys(): #if there are more photos made with the same intrinsic in the first project than choose this intrinsic
                    if len(intr_rel_views_2[intr_id]) <= len(intr_rel_views_1[self.inverse_intrinsic_transformation_dict[intr_id]]):
                        view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]    = self.inverse_intrinsic_transformation_dict[intr_id]
                    else:
                        view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]    = len(sfm_JSON["intrinsics"]) + view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
                views_out.append(view)

        self.SFM_JSON_OUT["views"] = views_out

    def _getIntrinsicRelatedViews(self, sfm_JSON):
        """ Return a dictionary like {0:[1,2,3,4,5], 1:[6,7,8,9]}"""
        intr_rel_dict = {} #initialize
        for intr in sfm_JSON["intrinsics"]:
            intr_rel_dict[intr["key"]] = []
        for view in sfm_JSON["views"]: #increase the number of views that share this intrinsic id
            intr_rel_dict[view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]].append(view["key"])
        return intr_rel_dict


    def addIntrinsiscs(self, sfm_JSON, sfm_JSON_2, doubled_photos_numb):
        """ 1. Iterate over the doubled views, note the intrinsic id's  """
        sfm_JSON_copy, sfm_JSON_2_copy = copy.deepcopy(sfm_JSON), copy.deepcopy(sfm_JSON_2)
        ps1_views_first_id = sfm_JSON_copy["views"][0]["value"]["ptr_wrapper"]["id"]

        ps_out_views_last_id = ps1_views_first_id + len(sfm_JSON_copy["views"]) + len(sfm_JSON_2_copy["views"]) - 2*doubled_photos_numb - 2
        k = 0
        for intrinsic in sfm_JSON_copy["intrinsics"]:
            intrinsic["value"]["ptr_wrapper"]["id"] = ps_out_views_last_id + k
            k += 1
        intrinsics_last_ptr_wrapper = sfm_JSON_copy["intrinsics"][-1]["value"]["ptr_wrapper"]["id"]
        intrinsics_last_key = sfm_JSON_copy["intrinsics"][-1]["key"]
        k = 0
        for intrinsic in sfm_JSON_2_copy["intrinsics"]:
            k += 1
            intrinsic["value"]["ptr_wrapper"]["id"] = intrinsics_last_ptr_wrapper + k
            intrinsic["key"] = intrinsics_last_key + k

            if len(sfm_JSON_copy["intrinsics"])> 0 :
                intrinsic["value"]["polymorphic_id"] = 1
            else:
                intrinsic["value"]["polymorphic_id"] = self.first_polymorphic_id
            sfm_JSON_copy["intrinsics"].append(intrinsic)
        self.SFM_JSON_OUT["intrinsics"] = sfm_JSON_copy["intrinsics"]



    def computeTransformations(self, sfm_JSON, sfm_JSON_2):
        """Analyse two sfm_data files and find points that ware generated by the same set of photos.
        Verify them by checking if they relate to the same pixeles on the 2D photos"""
        """ Create a relation dict pso1_view_id -> pso2_view_id """
        pso_1_twin_keys, pso_2_twin_keys = self.relation_dict.keys(), self.relation_dict.values()
        observation_dict, i = {}, 0
        for point in sfm_JSON_2["structure"]:
            """ Check if the structure point was generated from twin photos """
            views_intersection = set(pso_2_twin_keys).intersection(self._getObservationKeys(point["value"]["observations"]))
            if len(views_intersection) >= 3:
                for observation in point["value"]["observations"]:
                    if observation["key"] in views_intersection:
                        observation_key = "%d:(%.2f,%.2f)" % (observation["key"], observation["value"]["x"][0], observation["value"]["x"][1])
                        observation_dict[observation_key] = [point["value"]["X"], point["key"]]
                        break
                sfm_JSON_2["structure"].pop(i) #remove the doubled points
            i+=1

        """ Iterate the spo1 points and look for points from spo2 related to them"""
        pso_1_point_matrix, pso_2_point_matrix = [], []
        limit = 100000 # the maximum number of points for rotation
        for point in sfm_JSON["structure"]:
            if limit < 0:
                break
            for observation in point["value"]["observations"]:
                key = observation["key"]
                if key in pso_1_twin_keys:
                    observation_key = "%d:(%.2f,%.2f)" % (self.relation_dict[key], observation["value"]["x"][0], observation["value"]["x"][1])
                    if observation_key in observation_dict:
                        result = observation_dict[observation_key]
                        pso_1_point_matrix.append(point["value"]["X"] + [1])
                        pso_2_point_matrix.append(result[0] + [1])
                        limit -= 1
                        break
        extrinsics_1, extrinsics_2 = sfm_JSON["extrinsics"], sfm_JSON_2["extrinsics"]
        for extrinsic_ps_1_id in self.relation_dict.keys():
            pso_1_point_matrix.append(extrinsics_1[extrinsic_ps_1_id]["value"]["center"] + [1])
            pso_2_point_matrix.append(extrinsics_2[self.relation_dict[extrinsic_ps_1_id]]["value"]["center"] + [1])

        self.transformationMatrix = np.linalg.lstsq( np.array(pso_2_point_matrix), np.array(pso_1_point_matrix))[0]

    def _getObservationKeys(self, point_observations):
        photo_indexes = []
        for observation in point_observations:
            photo_indexes.append(observation["key"])
        return photo_indexes



    def getMergedStructure(self, sfm_JSON, sfm_JSON_2):
        structure_out = sfm_JSON["structure"]
        structure_last_key = sfm_JSON["structure"][-1]["key"]
        m = 0
        ps1_view_number = len(sfm_JSON["views"]) - len(sfm_JSON_2["views"])
        doubled_photos_number = len(self.relation_dict.keys())
        for point in sfm_JSON_2["structure"]: # iterate over project 2 points and transform the coordinates, rotations and observation ids
            m += 1
            point["key"] = structure_last_key + m
            point["value"]["X"] = self._getCoordinates(point["value"]["X"])
            for observation in point["value"]["observations"]:
                k = observation["key"]
                if k in self.relation_dict.values(): #if it's a doubled photo
                    observation["key"] = self.inverse_relation_dict[observation["key"]]
                else:
                    observation["key"] = ps1_view_number + k - doubled_photos_number
            structure_out.append(point)
        self.SFM_JSON_OUT["structure"] = structure_out

    def _getCoordinates(self, coordVect):
        vect = np.array(coordVect+[1])
        outputVec = np.dot(vect, self.transformationMatrix)
        return outputVec[0:3].tolist()



    def getMergedExtrinsics(self, sfm_JSON, sfm_JSON_2):
        """ Change the extrinsic from the second project """
        extrinsics_last_key = sfm_JSON["extrinsics"][-1]["key"]
        l = 0
        for extrinsic in sfm_JSON_2["extrinsics"]:
            if extrinsic["key"] not in self.relation_dict.values(): #if it's not a doubled photo
                l += 1
                extrinsic["key"] = extrinsics_last_key + l
                extrinsic["value"]["rotation"]  = self._getExtrinsicRotation(extrinsic["value"]["rotation"])
                extrinsic["value"]["center"]    = self._getCoordinates(extrinsic["value"]["center"])
                sfm_JSON["extrinsics"].append(extrinsic)
        self.SFM_JSON_OUT['extrinsics'] = sfm_JSON["extrinsics"]

    def _getExtrinsicRotation(self, rotationMat):
        rm = np.array(rotationMat)
        rm_out = np.dot(rm, self.transformationMatrix[:3,:3])
        scale = [1,1,1]
        scale[0] = math.sqrt(np.dot(rm_out[0], rm_out[0]))
        scale[1] = math.sqrt(np.dot(rm_out[1], rm_out[1]))
        scale[2] = math.sqrt(np.dot(rm_out[2], rm_out[2]))
        rm_out[0] = rm_out[0]/ scale[0]
        rm_out[1] = rm_out[1]/ scale[1]
        rm_out[2] = rm_out[2]/ scale[2]
        return rm_out.tolist()


    def removeOrphanedIntrinsics(self):
        """It is required to remove the intrinsics that are not related to any views"""
        intr_rel_dict = self._getIntrinsicRelatedViews(self.SFM_JSON_OUT)
        i = 0
        for intr_key in intr_rel_dict.keys():
            if len(intr_rel_dict[intr_key]) == 0:
                self.SFM_JSON_OUT["intrinsics"].pop(intr_key - i)
                i+=1
        # make order in the intrinsics --> intrinsics can look like this { key:1, key:2 , key:5}
        # we should order them so ---> {key:0 , key:1, key:2}
        index, last_view_id = 0, self.SFM_JSON_OUT["views"][-1]["value"]["ptr_wrapper"]["id"]
        for intr in self.SFM_JSON_OUT["intrinsics"]:
            if intr["key"] != index:
                intr["value"]["ptr_wrapper"]["id"] = last_view_id + 1 + index
                for view in self.SFM_JSON_OUT["views"]: #change views intr id
                    if view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] == intr["key"]:
                        view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] = index
                intr["key"] = index
            index += 1
        # if we deleted some intrinsics ant ther's only one left, than change all views poly_id to first_polymorphic_id
        if len(self.SFM_JSON_OUT["intrinsics"]) == 1:
            self.SFM_JSON_OUT["intrinsics"][0]["value"]["polymorphic_id"] = self.first_polymorphic_id


    def mergeSfMFiles(self, name_relation_dict, changed_name_dict):
        self.getRelationDict(name_relation_dict)
        with open(self.sfm1) as f1:
            sfm_JSON = json.load(f1)
            with open(self.sfm2) as f2:
                sfm_JSON_2 = json.load(f2)
                self.getIntrinsicTransformationDict(sfm_JSON, sfm_JSON_2, name_relation_dict)
                self.getMergedViews(sfm_JSON, sfm_JSON_2, changed_name_dict)
                self.addIntrinsiscs(sfm_JSON, sfm_JSON_2, len(name_relation_dict))
                self.computeTransformations(sfm_JSON, sfm_JSON_2)
                self.getMergedStructure(sfm_JSON, sfm_JSON_2)
                self.getMergedExtrinsics(sfm_JSON, sfm_JSON_2)
                self.removeOrphanedIntrinsics()
                with open(self.sfm_out, "w") as of:
                    json.dump(self.SFM_JSON_OUT, of, indent=4)