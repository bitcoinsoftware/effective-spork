import os, json, math
import numpy as np
import support_functions
import ProjectStatus
import SfMDataGenerator

class ProjectMerge:
    def __init__(self, psObject1, psObject2, outputDirUrl, log = None):
        self.psObject1 = psObject1
        self.psObject2 = psObject2
        self.outputDirUrl = outputDirUrl
        if log:
            self.log = log
        self.transformationMatrix = np.identity(4)

    def log(self, txt_array):
        for txt in txt_array:
            print(txt)

    def mergeProjects(self, mode = None):
        if os.path.isdir(self.outputDirUrl):
            if mode == None:
                mode = self.getMode(self.psObject1, self.psObject2)
            if self.psObject1.successful and self.psObject2.successful:
                self.psObjectOut = ProjectStatus.ProjectStatus(self.outputDirUrl, mode)
                self.psObjectOut.successful = True
                if self.psObject1.sparse_reconstruction and self.psObject2.sparse_reconstruction:
                    self.psObjectOut.sparse_reconstruction = True
                    #TODO
                    twinNames, twinNamesWithOtherEXIF = self.getTwinNames()
                    name_trans_dict = self.getPhotoNameTransformationDict(twinNamesWithOtherEXIF)
                    support_functions.copyImages(self.psObject1.inputDir, self.psObjectOut.inputDir)
                    support_functions.copyImages(self.psObject2.inputDir, self.psObjectOut.inputDir, dont_copy = twinNames, change_name_dict = name_trans_dict)

                    self.psObjectOut.photos = support_functions.getImagesList(self.outputDirUrl) #list(set(self.psObject1.photos + self.psObject2.photos))

                    if support_functions.fileNotEmpty(self.psObject1.openMVGSfMOutputFile) or support_functions.fileNotEmpty(self.psObject2.openMVGSfMJSONOutputFile):
                        psObject1_SfmUrl, psObject2_SfmUrl, outputSfmFileUrl = self.getSfmUrls()
                        self.mergeSfMFiles(psObject1_SfmUrl, psObject2_SfmUrl, outputSfmFileUrl, self.outputDirUrl , name_trans_dict)
                        self.psObjectOut.saveCurrentStatus()
                else:
                    self.log(["You must provide projects with computed sparse reconstruction"])
            else:
                self.log(["You must provide projects that ware successfuly initialized !!"])
        else:
            self.log(["Provided output project URL doesnt exist", self.outputDirUrl])

    def getPhotoNameTransformationDict(self, twinNamesWithOtherEXIF):
        tr_dict = {}
        if twinNamesWithOtherEXIF:
            for twName in twinNamesWithOtherEXIF:
                tr_dict[twName] = support_functions.modifyFileName(twName)
        return tr_dict


    def mergeSfMFiles(self, psObject1_SfmUrl, psObject2_SfmUrl, outputSfmFileUrl, output_base_folder, name_trans_dict ={}):
        with open(psObject1_SfmUrl) as f1:
            sfm_JSON = json.load(f1)
            sfm_JSON_out = {"sfm_data_version": "0.2"}
            sfm_JSON_out["root_path"]      = output_base_folder
            sfm_JSON_out["control_points"] = []
            with open(psObject2_SfmUrl) as f2:
                twin_names, twinNamesWithOtherEXIF = self.getTwinNames()
                self.getRelationDict(twin_names)
                sfm_JSON_2 = json.load(f2)
                self.getIntrinsicTransformationDict(sfm_JSON, sfm_JSON_2, twin_names)
                #first add intrinsics
                sfm_JSON_out["views"]       = self.getMergedViews(sfm_JSON, sfm_JSON_2, name_trans_dict)
                sfm_JSON_out["intrinsics"]  = self.addIntrinsiscs(sfm_JSON, sfm_JSON_2, twin_names)
                #than iterate over the views and choose the intrinsic that relates to more photos  - the more photos the better optics estimation
                self.computeTransformations(sfm_JSON, sfm_JSON_2)

                sfm_JSON_out["structure"]   = self.getMergedStructure(sfm_JSON, sfm_JSON_2)
                #sfm_JSON_out["structure"] = sfm_JSON["structure"]
                sfm_JSON_out["extrinsics"]  = self.getMergedExtrinsics(sfm_JSON, sfm_JSON_2)
                self.removeOrphanedIntrinsics(sfm_JSON_out)
                with open(outputSfmFileUrl, "w") as of:
                    json.dump(sfm_JSON_out, of, indent=4)


    def removeOrphanedIntrinsics(self, sfmJSON):
        intr_rel_dict = self.getIntrinsicRelatedViews(sfmJSON)
        i = 0
        for intr_key in intr_rel_dict.keys():
            if len(intr_rel_dict[intr_key]) == 0:
                sfmJSON["intrinsics"].pop(intr_key - i)
                i+=1
        return sfmJSON


    def getMergedViews(self, sfm_JSON, sfm_JSON_2, name_trans_dict = {}):
        """1. Iterate over proj1 and modify the intrinsic fields if required
           2. Iterate over proj2, if it's a dubbled view, pass it else change the keys, id_pose, id_view and id_intrinsic"""
        # 1. Iterate over proj1, modify the intrinsic key if in project2 there are more photos related to the same intrinsic
        intr_rel_views_1 = self.getIntrinsicRelatedViews(sfm_JSON)
        intr_rel_views_2 = self.getIntrinsicRelatedViews(sfm_JSON_2)

        views_last_key = sfm_JSON["views"][-1]["key"]
        views_last_id = sfm_JSON["views"][-1]["value"]["ptr_wrapper"]["id"]
        views_out = sfm_JSON["views"]
        i = 0
        for view in sfm_JSON["views"]:
            intr_id = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
            if intr_id in self.intrinsic_transformation_dict.keys():  # if there are more photos made with the same intrinsic in the first project than choose this intrinsic
                if len(intr_rel_views_2[intr_id]) > len(intr_rel_views_1[self.intrinsic_transformation_dict[intr_id]]):
                    view["value"]["ptr_wrapper"]["data"]["id_intrinsic"] = self.intrinsic_transformation_dict[intr_id] + len(self.intrinsic_transformation_dict.keys())

        i = 0
        for view in sfm_JSON_2["views"]:
            if view["key"] not in self.relation_dict.values(): #if it's not a doubled photo
                i+=1
                view["key"]                                             = views_last_key + i
                view["value"]["ptr_wrapper"]["id"]                      = views_last_id + i
                view["value"]["ptr_wrapper"]["data"]["id_pose"]         = view["key"]
                view["value"]["ptr_wrapper"]["data"]["id_view"]         = view["key"]

                if view["value"]["ptr_wrapper"]["data"]["filename"] in name_trans_dict.keys():
                    view["value"]["ptr_wrapper"]["data"]["filename"] = name_trans_dict[view["value"]["ptr_wrapper"]["data"]["filename"]]

                intr_id = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
                #TODO Naprawic Intrinsics
                if intr_id in self.inverse_intrinsic_transformation_dict.keys(): #if there are more photos made with the same intrinsic in the first project than choose this intrinsic
                    if len(intr_rel_views_2[intr_id]) < len(intr_rel_views_1[self.inverse_intrinsic_transformation_dict[intr_id]]):
                        view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]    = self.inverse_intrinsic_transformation_dict[intr_id]
                    else:
                        view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]    = len(sfm_JSON["intrinsics"]) + view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
                views_out.append(view)

        return views_out


    def getMergedStructure(self, sfm_JSON, sfm_JSON_2):
        structure_out = sfm_JSON["structure"]
        structure_last_key = sfm_JSON["structure"][-1]["key"]
        m = 0

        ps1_view_number = len(sfm_JSON["views"]) - len(sfm_JSON_2["views"])
        #print " ps1_view_number",  ps1_view_number
        doubled_photos_number = len(self.relation_dict.keys())
        #print "doubled_photos_number", doubled_photos_number
        #print "computed last view id =", ps1_view_number - len(sfm_JSON_2["views"]) - 2*doubled_photos_number
        #print "ps1_view_number %d , ps2_views_len %d , 2*doubled_photos %d" % ( ps1_view_number , len(sfm_JSON_2["views"]) , 2*doubled_photos_number )

        #iterate over project 2 points and transform the coordinates, rotations and observation ids
        for point in sfm_JSON_2["structure"]:#[6891:6892]:
            m += 1
            point["key"] = structure_last_key + m
            point["value"]["X"] = self.getCoordinates(point["value"]["X"])
            for observation in point["value"]["observations"]:
                k = observation["key"]
                if k in self.relation_dict.values(): #if it's a doubled photo
                    observation["key"] = self.inverse_relation_dict[observation["key"]]
                    #print "TRANSLATED >>>>\n", observation
                else:
                    observation["key"] = ps1_view_number + k - doubled_photos_number
            structure_out.append(point)
        return structure_out


    def getMergedExtrinsics(self, sfm_JSON, sfm_JSON_2):
        """ Change the extrinsic from the second project """
        extrinsics_last_key = sfm_JSON["extrinsics"][-1]["key"]
        l = 0
        for extrinsic in sfm_JSON_2["extrinsics"]:
            if extrinsic["key"] not in self.relation_dict.values(): #if it's not a doubled photo
                l += 1
                extrinsic["key"] = extrinsics_last_key + l
                extrinsic["value"]["rotation"]  = self.getExtrinsicRotation(extrinsic["value"]["rotation"])
                extrinsic["value"]["center"]    = self.getCoordinates(extrinsic["value"]["center"])
                #extrinsic["value"]["center"]    = self.getCoordinates(extrinsic["value"]["center"])
                sfm_JSON["extrinsics"].append(extrinsic)
        return sfm_JSON["extrinsics"]

    """
    def getExtrinsicTransformationMatrix(self, sfm_JSON, sfm_JSON_2, relation_dict):
        centers_1 , centers_2 = [], []
        extrinsics_1 = sfm_JSON["extrinsics"]
        extrinsics_2 = sfm_JSON_2["extrinsics"]
        for extrinsic_ps_1_id in relation_dict.keys():
            centers_1.append(extrinsics_1[extrinsic_ps_1_id]["value"]["center"] + [1])
            centers_2.append(extrinsics_2[relation_dict[extrinsic_ps_1_id]]["value"]["center"] + [1])
        return np.linalg.lstsq(np.array(centers_2), np.array(centers_1))[0]
    """

    def getCoordinates(self, coordVect):
        vect = np.array(coordVect+[1])
        outputVec = np.dot(vect, self.transformationMatrix)
        #outputVec = np.dot(np.transpose(self.transformationMatrix), vect)
        return outputVec[0:3].tolist()

    def getExtrinsicCoordinates(self, coordVect):
        vect = np.array(coordVect+[1])
        outputVec = np.dot(vect, self.extrinsicTransformationMatrix)
        #print "TRANSFORMATION FROM >>>> \n", vect
        #print "TO >>>>> \n", outputVec
        return outputVec[0:3].tolist()

    def getExtrinsicRotation(self, rotationMat):
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

    def computeTransformations(self, sfm_JSON, sfm_JSON_2):
        """Analyse two sfm_data files and find points that ware generated by the same set of photos.
        Verify them by checking if they relate to the same pixeles on the 2D photos"""
        """ Create a relation dict pso1_view_id -> pso2_view_id """
        pso_1_twin_keys = self.relation_dict.keys()
        pso_2_twin_keys = self.relation_dict.values()

        observation_dict = {}
        structure = sfm_JSON_2["structure"]
        i =0
        for point in structure:
            """ Check if the structure point was generated from twin photos """
            views_intersection = set(pso_2_twin_keys).intersection(self.getObservationKeys(point["value"]["observations"]))
            if len(views_intersection) >= 3:
                for observation in point["value"]["observations"]:
                    if observation["key"] in views_intersection:
                        observation_key = "%d:(%.2f,%.2f)" % (observation["key"], observation["value"]["x"][0], observation["value"]["x"][1])
                        observation_dict[observation_key] = [point["value"]["X"], point["key"]]
                        break
                sfm_JSON_2["structure"].pop(i)
        i+=1

        """ Iterate the spo1 points and look for points from spo2 related to them"""
        pso_1_point_matrix = []
        pso_2_point_matrix = []


        limit = 100000 # the maximum number of points for rotation
        structure = sfm_JSON["structure"]
        for point in structure:
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

        extrinsics_1 = sfm_JSON["extrinsics"]
        extrinsics_2 = sfm_JSON_2["extrinsics"]
        for extrinsic_ps_1_id in self.relation_dict.keys():
            pso_1_point_matrix.append(extrinsics_1[extrinsic_ps_1_id]["value"]["center"] + [1])
            pso_2_point_matrix.append(extrinsics_2[self.relation_dict[extrinsic_ps_1_id]]["value"]["center"] + [1])

        self.transformationMatrix = np.linalg.lstsq( np.array(pso_2_point_matrix), np.array(pso_1_point_matrix))[0]

        #scale, tm = [1,1,1], self.transformationMatrix
        #scale[0] = math.sqrt(np.dot(tm[0], tm[0]))
        #scale[1] = math.sqrt(np.dot(tm[1], tm[1]))
        #scale[2] = math.sqrt(np.dot(tm[2], tm[2]))

        #tm[0] = tm[0]/ scale[0]
        #tm[1] = tm[1]/ scale[1]
        #tm[2] = tm[2]/ scale[2]
        #self.extrinsicTransformationMatrix = tm

        #self.getExtrinsicTransformationMatrix(sfm_JSON, sfm_JSON_2, self.relation_dict)

        print "trans Mat >>>\n", self.transformationMatrix
        #print "SCALE (x , y , z)>>>\n", (np.dot(self.transformationMatrix[0], self.transformationMatrix[0]), np.dot(self.transformationMatrix[1], self.transformationMatrix[1]), np.dot(self.transformationMatrix[2], self.transformationMatrix[2]))
        #print "extr Mat >>>>\n", self.extrinsicTransformationMatrix


    def getObservationKeys(self, point_observations):
        photo_indexes = []
        for observation in point_observations:
            photo_indexes.append(observation["key"])
        return photo_indexes


    def addIntrinsiscs(self, sfm_JSON, sfm_JSON_2, twinNames):
        """ 1. Iterate over the doubled views, note the intrinsic id's  """
        ps1_views_first_id = sfm_JSON["views"][0]["value"]["ptr_wrapper"]["id"]

        ps_out_views_last_id = ps1_views_first_id + len(sfm_JSON["views"]) + len(sfm_JSON_2["views"]) - len(twinNames) - 2
        k = 0
        for intrinsic in sfm_JSON["intrinsics"]:
            intrinsic["value"]["ptr_wrapper"]["id"] = ps_out_views_last_id + k
            k += 1


        intrinsics_last_ptr_wrapper = sfm_JSON["intrinsics"][-1]["value"]["ptr_wrapper"]["id"]
        intrinsics_last_key = sfm_JSON["intrinsics"][-1]["key"]

        k = 0
        for intrinsic in sfm_JSON_2["intrinsics"]:
            k += 1
            intrinsic["value"]["ptr_wrapper"]["id"] = intrinsics_last_ptr_wrapper + k
            intrinsic["key"] = intrinsics_last_key + k
            if len(sfm_JSON["intrinsics"])> 0 :
                intrinsic["value"]["polymorphic_id"] = 1
            else:
                intrinsic["value"]["polymorphic_id"] = 2147483649
            sfm_JSON["intrinsics"].append(intrinsic)
        return sfm_JSON["intrinsics"]



    def getRelationDict(self, twinNames):
        """Get a dictionary showing the relation between doubled photos,  project1 --> project2"""
        pso_1_twin_keys , pso_1_twin_names = [], []
        with open(self.psObject1.openMVGSfMJSONOutputFile) as f1:
            views = json.load(f1)["views"]
            for view in views:
                filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                if filename in twinNames:
                    pso_1_twin_keys.append(view["key"])
                    pso_1_twin_names.append(filename)
            """Get the twin points from project 2"""
            pso_2_twin_keys , pso_2_twin_names = [], []
            with open(self.psObject2.openMVGSfMJSONOutputFile) as f2:
                views = json.load(f2)["views"]
                for view in views:
                    filename = view["value"]["ptr_wrapper"]["data"]["filename"]
                    if filename in twinNames:
                        pso_2_twin_keys.append(view["key"])
                        pso_2_twin_names.append(filename)
                self.relation_dict, self.inverse_relation_dict = {}, {}
                for i in xrange(len(pso_1_twin_names)):
                    filename = pso_1_twin_names[i]
                    key = pso_1_twin_keys[i]
                    pso_2_key = pso_2_twin_keys[pso_2_twin_names.index(filename)]
                    self.relation_dict[key] = pso_2_key
                    self.inverse_relation_dict[pso_2_key] = key

                print "REALTION DICT>>>\n", self.relation_dict
                print "INVERSE RELATION DICT>>>\n", self.inverse_relation_dict
                return self.relation_dict


    def getIntrinsicTransformationDict(self, sfm_JSON, sfm_JSON_2, twinNames):
        photo_name_intrinsic_relation_dict_1 = self.getIntrinsicRelatedPhotoNames(sfm_JSON)
        photo_name_intrinsic_relation_dict_2 = self.getIntrinsicRelatedPhotoNames(sfm_JSON_2)
        self.intrinsic_transformation_dict   = {}
        self.inverse_intrinsic_transformation_dict   = {}
        for twinName in twinNames:
            self.intrinsic_transformation_dict[photo_name_intrinsic_relation_dict_1[twinName]] = photo_name_intrinsic_relation_dict_2[twinName]
            self.inverse_intrinsic_transformation_dict[photo_name_intrinsic_relation_dict_1[twinName]] = photo_name_intrinsic_relation_dict_2[twinName]
        return self.intrinsic_transformation_dict


    def getIntrinsicRelatedViews(self, sfm_JSON):
        """ Return a dictionary like {0:[1,2,3,4,5], 1:[6,7,8,9]}"""
        intr_rel_dict = {} #initialize
        for i in xrange(len(sfm_JSON["intrinsics"])):
            intr_rel_dict[i] = []
        for view in sfm_JSON["views"]: #increase the number of views that share this intrinsic id
            #print view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
            intr_rel_dict[view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]].append(view["key"])
        return intr_rel_dict


    def getIntrinsicRelatedPhotoNames(self, sfm_JSON):
        intr_rel_dict ={} #initialize
        for view in sfm_JSON["views"]:
            intr_rel_dict[view["value"]["ptr_wrapper"]["data"]["filename"]] = view["value"]["ptr_wrapper"]["data"]["id_intrinsic"]
        return intr_rel_dict


    def getTwinNames(self):
        """ Iterate over the twin photo names and check if the EXIF match"""
        with open(self.psObject1.url) as f1:
            pso_1_listing = json.load(f1)
            with open(self.psObject2.url) as f2:
                pso_2_listing = json.load(f2)
                doubled_photo_names = list(set(pso_1_listing['photos']).intersection(pso_2_listing["photos"]))
                verifiedTwinPhotoNames = []
                twinNamesWithOtherEXIF = []
                for photoName in doubled_photo_names:
                    if self.verifyCameraRedundancy(os.path.join(self.psObject1.inputDir, photoName), os.path.join(self.psObject2.inputDir, photoName)):
                        verifiedTwinPhotoNames.append(photoName)
                    else:
                        twinNamesWithOtherEXIF.append(photoName)
                return verifiedTwinPhotoNames, twinNamesWithOtherEXIF
        return None, None


    def verifyCameraRedundancy(self, url1, url2):
        """Checks if photos ware made with the same camera and the same parameters"""
        exif_keys = ['Make', 'Model', 'ExifImageWidth', 'ExifImageHeight', 'FocalLength', 'DateTime']
        sfmDG = SfMDataGenerator.SfMDataGenerator(log = self.log)
        exif_1 = sfmDG.getExifDict(url1, exif_keys)
        exif_2 = sfmDG.getExifDict(url2, exif_keys)
        if exif_1 == exif_2:
            return True
        return False


    def getMode(self, psObject1, psObject2):
        """Chooses the mode from the project containing more photos"""
        if len(psObject1.photos) >= len(psObject2.photos):
            return psObject1.mode
        else:
            return psObject2.mode

    def getSfmUrls(self):
        if support_functions.fileNotEmpty(self.psObjectOut.openMVGSfMOutputFile):
            psObject1_SfmUrl = self.psObject1.openMVGSfMOutputFile
            psObject2_SfmUrl = self.psObject2.openMVGSfMOutputFile
            outputSfmFileUrl = self.psObjectOut.openMVGSfMOutputFile
        else:
            psObject1_SfmUrl = self.psObject1.openMVGSfMJSONOutputFile
            psObject2_SfmUrl = self.psObject2.openMVGSfMJSONOutputFile
            outputSfmFileUrl = self.psObjectOut.openMVGSfMJSONOutputFile
        return psObject1_SfmUrl, psObject2_SfmUrl, outputSfmFileUrl

if __name__ =="__main__":
    url_out = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/merged"
    pso1 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part1/output/projectStatus.json")
    pso2 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part2/output/projectStatus.json")
    #url_out = "/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/merged"
    #pso1 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/part1/output/projectStatus.json")
    #pso2 = ProjectStatus.ProjectStatus("/home/array/Dokumenty/Gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/part2/output/projectStatus.json")
    pm = ProjectMerge(pso1, pso2, url_out)
    pm.mergeProjects(mode="NORMAL")