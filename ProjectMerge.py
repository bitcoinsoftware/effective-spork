import numpy as np
import json
import os
import shutil

import SfMDataGenerator
import ProjectStatus
import support_functions

class ProjectMerge:
    def __init__(self, firstProjectStatusObject, secondProjectStatusObject, log = None):
        self.pso_1 = firstProjectStatusObject
        self.pso_2 = secondProjectStatusObject

        if log:
            self.log = log

    def log(self, txt_array):
        for txt in txt_array:
            print(txt)

    def getViewIdAndPoseId(self, photoName, views):
        for view in views:
            if view["value"]["ptr_wrapper"]["data"]["filename"] == photoName:
                return view["value"]["ptr_wrapper"]["data"]["id_view"] , view["value"]["ptr_wrapper"]["data"]["id_pose"]
        return None, None

    def getPoseCenterAndRotation(self, poseId, poses):
        for extrinsic in poses:
            if extrinsic["key"] == poseId:
                return extrinsic["value"]["center"] , extrinsic["value"]["rotation"]
        return None, None

    def getViewData(self, photoName):
        """ Returnes photoName:"name", viewIDs:(id_0, id_1), poseIDs:(id0, id1) ,center:[0,0,0], rotation """
        with open(self.pso_1.openMVGSfMJSONOutputFile) as f1:
            with open(self.pso_2.openMVGSfMJSONOutputFile) as f2:
                pso_1_listing = json.load(f1)
                pso_2_listing = json.load(f2)

                pso_1_view_id, pso_1_pose_id            = self.getViewIdAndPoseId(photoName, pso_1_listing[u'views'])
                pso_2_view_id, pso_2_pose_id            = self.getViewIdAndPoseId(photoName, pso_2_listing[u'views'])

                pso_1_pose_center, pso_1_pose_rotation  = self.getPoseCenterAndRotation(pso_1_view_id, pso_1_listing['extrinsics'])
                pso_2_pose_center, pso_2_pose_rotation  = self.getPoseCenterAndRotation(pso_2_view_id, pso_2_listing['extrinsics'])
                return {"name":photoName, "view_id":(pso_1_view_id, pso_2_view_id), "pose_center":(pso_1_pose_center, pso_2_pose_center), "pose_rotation":(pso_1_pose_rotation, pso_2_pose_rotation)}

    def getTwinPoses(self):
        twinPhotoNames = self.getTwinPhotos()
        twinPoses = []
        for twinPhoto in twinPhotoNames:
            twinPoses.append(self.getViewData(twinPhoto))
        return twinPoses

    def getTwinPhotos(self):
        """ Iterate over the twin photo names and check if the EXIF match"""
        sfmDG_1 = SfMDataGenerator.SfMDataGenerator(self.pso_1)
        sfmDG_2 = SfMDataGenerator.SfMDataGenerator(self.pso_2)
        twinPhotoNames = self.getTwinPhotoNames()
        verifiedTwinPhotoNames = []
        exif_keys = ['Make', 'Model', 'ExifImageWidth', 'ExifImageHeight', 'FocalLength', 'DateTime']
        for photoName in twinPhotoNames:
            exif_1 = sfmDG_1.getExifDict(os.path.join(self.pso_1.inputDir, photoName), exif_keys)
            exif_2 = sfmDG_2.getExifDict(os.path.join(self.pso_2.inputDir, photoName), exif_keys)
            if exif_1 == exif_2:
                verifiedTwinPhotoNames.append(photoName)
        return verifiedTwinPhotoNames

    def getTwinPhotoNames(self):
        """ Finds images that are a common part of two projects"""
        with open(self.pso_1.url) as f1:
            pso_1_listing = json.load(f1)
            with open(self.pso_2.url) as f2:
                pso_2_listing = json.load(f2)
                return list(set(pso_1_listing['photos']).intersection(pso_2_listing["photos"]))

    def getViewsParamsList(self, listing):
        views = listing['views']
        views_data = []
        for view in views:
            photo_name   = view["value"]["ptr_wrapper"]["data"]["filename"]
            photo_size   = (view["value"]["ptr_wrapper"]["data"]["width"], view["value"]["ptr_wrapper"]["data"]["height"])

            views_data.append(json.dumps([photo_name, photo_size]))
        return views_data

    def getViewIntrinsicParams(self, view, intrinsics):
        intrinsic_id = view['value']["ptr_wrapper"]['data']['id_intrinsic']
        intrinsic = None
        for intri in intrinsics:
            if intri['key'] == intrinsic_id:
                intrinsic = intri
                break
        if intrinsic != None:
            intrinsic_params = []
            intrinsic_params.append(intrinsic['value']["ptr_wrapper"]['data']['focal_length'])
            intrinsic_params.append(intrinsic['value']["ptr_wrapper"]['data']['width'])
            intrinsic_params.append(intrinsic['value']["ptr_wrapper"]['data']['height'])
            return intrinsic_params

    def getObservationKeys(self, point_observations):
        photo_indexes = []
        for observation in point_observations:
            photo_indexes.append(observation["key"])
        return photo_indexes


    def getRelationDict(self, twinNames):
        """Get the twin points from project 1"""
        pso_1_twin_keys , pso_1_twin_names = [], []
        with open(self.pso_1.openMVGSfMJSONOutputFile) as f1:
            views = json.load(f1)["views"]
            for view in views:
                filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                if filename in twinNames:
                    pso_1_twin_keys.append(view["key"])
                    pso_1_twin_names.append(filename)

        """Get the twin points from project 2"""
        pso_2_twin_keys , pso_2_twin_names = [], []
        with open(self.pso_2.openMVGSfMJSONOutputFile) as f2:
            views = json.load(f2)["views"]
            for view in views:
                filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                if filename in twinNames:
                    pso_2_twin_keys.append(view["key"])
                    pso_2_twin_names.append(filename)

        relation_dict = {}
        for i in xrange(len(pso_1_twin_names)):
            filename = pso_1_twin_names[i]
            key = pso_1_twin_keys[i]
            pso_2_key = pso_2_twin_keys[pso_2_twin_names.index(filename)]
            relation_dict[key] = pso_2_key
        return relation_dict

    def getInvertedRealtionDict(self, twinNames):
        """Get the twin points from project 1"""
        pso_1_twin_keys , pso_1_twin_names = [], []
        with open(self.pso_1.openMVGSfMJSONOutputFile) as f1:
            views = json.load(f1)["views"]
            for view in views:
                filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                if filename in twinNames:
                    pso_1_twin_keys.append(view["key"])
                    pso_1_twin_names.append(filename)

        """Get the twin points from project 2"""
        pso_2_twin_keys , pso_2_twin_names = [], []
        with open(self.pso_2.openMVGSfMJSONOutputFile) as f2:
            views = json.load(f2)["views"]
            for view in views:
                filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                if filename in twinNames:
                    pso_2_twin_keys.append(view["key"])
                    pso_2_twin_names.append(filename)

        relation_dict = {}
        for i in xrange(len(pso_1_twin_names)):
            filename = pso_1_twin_names[i]
            key = pso_1_twin_keys[i]
            pso_2_key = pso_2_twin_keys[pso_2_twin_names.index(filename)]
            relation_dict[pso_2_key] = key
        return relation_dict


    def getTransformationMatrix(self, twinNames):
        """Analyse two sfm_data files and find points that ware generated by the same set of photos.
        Verify them by checking if they relate to the same pixeles on the 2D photos"""

        """ Create a relation dict pso1_view_id -> pso2_view_id """
        relation_dict = self.getRelationDict(twinNames)
        pso_1_twin_keys = relation_dict.keys()
        pso_2_twin_keys = relation_dict.values()

        observation_dict = {}
        with open(self.pso_2.openMVGSfMJSONOutputFile) as f2:
            structure = json.load(f2)["structure"]
            for point in structure:
                """ Check if the structure point was generated from twin photos """
                views_intersection = set(pso_2_twin_keys).intersection(self.getObservationKeys(point["value"]["observations"]))
                if len(views_intersection) >= 3:
                    for observation in point["value"]["observations"]:
                        if observation["key"] in views_intersection:
                            observation_key = "%d:(%.2f,%.2f)" % (observation["key"], observation["value"]["x"][0], observation["value"]["x"][1])
                            observation_dict[observation_key] = [point["value"]["X"], point["key"]]
                            break

            """ Iterate the spo1 points and look for points from spo2 related to them"""
            pso_1_point_matrix = []
            pso_2_point_matrix = []

            with open(self.pso_1.openMVGSfMJSONOutputFile) as f1:
                structure = json.load(f1)["structure"]
                for point in structure:
                    for observation in point["value"]["observations"]:
                        key = observation["key"]
                        if key in pso_1_twin_keys:
                            observation_key = "%d:(%.2f,%.2f)" % (relation_dict[key], observation["value"]["x"][0], observation["value"]["x"][1])
                            if observation_key in observation_dict:
                                result = observation_dict[observation_key]
                                #point_relation_dict[point["key"]] = {"X":point["value"]["X"], "X_prim" : result[0], "key_prim" : result[1]}
                                pso_1_point_matrix.append(point["value"]["X"]+[1])
                                pso_2_point_matrix.append(result[0]+[1])
                                #print point["key"], "  -->  ", result[1]
                                break

            #transpose(pso_2_point_matrix) = transpose(pso_1_point_matrix) * transformationMatrix
            #transformationMatrix = np.invert(transpose(pso_1_point_matrix)) * transpose(pso_2_point_matrix)

            transformationMatrix = np.dot( np.linalg.pinv( np.array(pso_1_point_matrix) ) , np.array(pso_2_point_matrix) )
            return transformationMatrix

    def getMaxMode(self, mode1, mode2):
        mode2int = {"NORMAL":0, "HIGH":1, "ULTRA":2}
        int2mode = ["NORMAL", "HIGH", "ULTRA"]
        if mode1 in int2mode:
            if mode2 in int2mode:
                maxint = max(mode2int[mode1], mode2int[mode2])
                return int2mode[maxint]
            else:
                self.log([mode2, "Not in available modes."])
        else:
            self.log([mode1, "Not in available modes"])

    def copyImages(self, inputUrl, outputUrl):
        imagesList = support_functions.getImagesList(inputUrl)
        for fileName in imagesList:
            outputFilePath = os.path.join(outputUrl, fileName)
            if not os.path.exists(outputFilePath):
                shutil.copyfile(os.path.join(inputUrl, fileName), outputFilePath)
                print "Copied photo :", outputFilePath

    def mergeSfMFiles(self, sfm1, sfm2, outputSfM, rootPath):
        with open(sfm1) as f1:
            sfm_JSON = json.load(f1)

            sfm_JSON["root_path"]          = rootPath

            views_last_key                 = sfm_JSON["views"][-1]["key"]
            views_last_id                  = sfm_JSON["views"][-1]["value"]["ptr_wrapper"]["id"]
            views_last_id_intrinsic        = sfm_JSON["views"][-1]["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
            views_last_id_pose             = sfm_JSON["views"][-1]["value"]["ptr_wrapper"]["data"]["id_pose"]
            views_last_id_view             = sfm_JSON["views"][-1]["value"]["ptr_wrapper"]["data"]["id_view"]

            intrinsics_last_key            = sfm_JSON["intrinsics"][-1]["key"]
            #intrinsics_last_polymorphic_id = sfm_JSON["intrinsics"][-1]["value"]["polymorphic_id"]

            extrinsics_last_key            = sfm_JSON["extrinsics"][-1]["key"]

            structure_last_key             = sfm_JSON["structure"][-1]["key"]

            control_points = []

            with open(sfm2) as f2:
                sfm_JSON_2 = json.load(f2)
                i = 0
                """ Change the views indexes from the second project """
                for view in sfm_JSON_2["views"]:
                    i += 1
                    view["key"]                                          = views_last_key + i
                    view["value"]["ptr_wrapper"]["id"]                   = views_last_id + i
                    view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] = views_last_id_intrinsic + view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] + 1
                    view["value"]["ptr_wrapper"]["data"]["id_pose"]      = views_last_id_pose + i
                    view["value"]["ptr_wrapper"]["data"]["id_view"]      = views_last_id_view + i

                    sfm_JSON["views"].append(view)

                """ Change the intrinsic indexes from the first project """
                k = 0
                for intrinsic in sfm_JSON["intrinsics"]:
                    k += 1
                    intrinsic["value"]["ptr_wrapper"]["id"]     = views_last_id + i + k

                """ Change the intrinsic indexes from the second project """
                j = 0
                for intrinsic in sfm_JSON_2["intrinsics"]:
                    j += 1
                    intrinsic["key"]                            = intrinsics_last_key + j
                    intrinsic["value"]["ptr_wrapper"]["id"]     = views_last_id + i + k + j
                    intrinsic["value"]["polymorphic_id"]        = 1

                    sfm_JSON["intrinsics"].append(intrinsic)

                """ Change the extrinsic  from the second project """
                l = 0
                for extrinsic in sfm_JSON_2["extrinsics"]:
                    l += 1
                    extrinsic["key"] = extrinsics_last_key + l
                    #TODO
                    extrinsic["value"]["rotation"]  = self.getExtrinsicRotation(extrinsic["value"]["rotation"])
                    #TODO
                    extrinsic["value"]["center"]    = self.getCoordinates(extrinsic["value"]["center"])

                    sfm_JSON["extrinsics"].append(extrinsic)

                """ Change the structure points from the second project """

                m = 0
                for point in sfm_JSON_2["structure"]:
                    m+=1
                    point["key"] = structure_last_key + m
                    point["value"]["X"] = self.getCoordinates(point["value"]["X"])

                    for observation in point["value"]["observations"]:
                        observation["key"] = views_last_id_view + observation["key"] + 1

                    sfm_JSON["structure"].append(point)


                with open(outputSfM, "w") as of:
                    json.dump(sfm_JSON, of, indent=4)


    #TODO
    def getCoordinates(self, coordVect):
        return coordVect


    #TODO
    def getExtrinsicRotation(self, eulerAngles):
        return eulerAngles


    def mergeProjects(self, project_1_url, project_2_url, output_project_url):
        if os.path.exists(project_1_url):
            ps_1 = ProjectStatus.ProjectStatus(project_1_url)
            if os.path.exists(project_2_url):
                ps_2 = ProjectStatus.ProjectStatus(project_2_url)
                if os.path.isdir(output_project_url):
                    mode = self.getMaxMode(ps_1.mode, ps_2.mode)
                    if ps_1.successful and ps_2.successful:
                        output_ps_object = ProjectStatus.ProjectStatus(output_project_url, mode)
                        #output_ps_object.status = True
                        output_ps_object.successful = True
                        if ps_1.sparse_reconstruction and ps_2.sparse_reconstruction:
                            output_ps_object.sparse_reconstruction = True
                            self.copyImages(ps_1.inputDir, output_ps_object.inputDir)
                            self.copyImages(ps_2.inputDir, output_ps_object.inputDir)
                            output_ps_object.photos = ps_1.photos + ps_2.photos

                            if support_functions.fileNotEmpty(ps_1.openMVGSfMOutputFile) or support_functions.fileNotEmpty(ps_2.openMVGSfMJSONOutputFile):
                                if support_functions.fileNotEmpty(output_ps_object.openMVGSfMOutputFile):
                                    ps_1_SfmFileUrl = ps_1.openMVGSfMOutputFile
                                    ps_2_SfmFileUrl = ps_2.openMVGSfMOutputFile
                                    outputSfmFileUrl = output_ps_object.openMVGSfMOutputFile
                                else:
                                    ps_1_SfmFileUrl  = ps_1.openMVGSfMJSONOutputFile
                                    ps_2_SfmFileUrl  = ps_2.openMVGSfMJSONOutputFile
                                    outputSfmFileUrl = output_ps_object.openMVGSfMJSONOutputFile

                                self.mergeSfMFiles(ps_1_SfmFileUrl, ps_2_SfmFileUrl, outputSfmFileUrl, output_ps_object.inputDir)

                                output_ps_object.saveCurrentStatus()

                        else:
                            self.log(["You must provide projects with computed sparse reconstruction"])
                    else:
                        self.log(["You must provide projects that ware successfuly initialized !!"])
                else:
                    self.log(["Provided output project URL doesnt exist", output_project_url])
            else:
                self.log(["Provided project doesnt exist :", project_2_url])
        else:
            self.log(["Provided project doesnt exist :", project_1_url])