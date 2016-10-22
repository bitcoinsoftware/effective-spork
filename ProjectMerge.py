import os, json
import support_functions
import ProjectStatus
import SfMDataGenerator
import SfMDataMerge

class ProjectMerge:
    def __init__(self, psObject1, psObject2, outputDirUrl, log = None):
        self.first_polymorphic_id = 2147483649
        self.EXIF_keys = ['ImageDescription', 'ExifImageWidth', 'ExifImageHeight', 'Make', 'Model', 'FocalLength', 'DateTime']
        self.psObject1 = psObject1
        self.psObject2 = psObject2
        self.outputDirUrl = outputDirUrl
        if log:
            self.log = log
        else:
            self.log = support_functions.log

        self.psObjectOut = ProjectStatus.ProjectStatus(self.outputDirUrl, self.getMode(self.psObject1, self.psObject2)) # get the mode of the bigger subproject
        #self.transformationMatrix = np.identity(4)


    def getMode(self, psObject1, psObject2):
        """Chooses the mode from the project containing more photos"""
        return psObject1.mode if len(psObject1.photos) >= len(psObject2.photos) else psObject2.mode


    def getTwinPhotosRelationDict(self):
        """Some photos can be identical in both projects but they can have different names.
        This function finds identical photos in two projects based on their EXIF data. The file name is not important.
        This function returnes a dictionary of NameInProj1 : NameInProj2 """
        self.name_relation_dict, self.inverse_name_relation_dict = {}, {}
        with open(self.psObject1.url) as f1:
            pso_1_photos = json.load(f1)['photos']
            with open(self.psObject2.url) as f2:
                pso_2_photos = json.load(f2)['photos']
                sfmDG = SfMDataGenerator.SfMDataGenerator(log=self.log)
                pso_1_exif_dict = {}
                for img_name in pso_1_photos: #Generate a dictionary with the above EXIF tags {'PhotoName1':{'Make':'DJI' ...}, 'PhotoName2':{....}} from project 1
                    pso_1_exif_dict[img_name] = sfmDG.getExifDict(os.path.join(self.psObject1.inputDir, img_name), exifTags = self.EXIF_keys)
                pso_2_exif_dict = {}
                for img_name in pso_2_photos: #Generate a dictionary with the above EXIF tags {'PhotoName1':{'Make':'DJI' ...}, 'PhotoName2':{....}} from project 2
                    pso_2_exif_dict[img_name] = sfmDG.getExifDict(os.path.join(self.psObject2.inputDir, img_name), exifTags = self.EXIF_keys)
                for p1_key in pso_1_exif_dict.keys(): #iterate over the first dict
                    p1_val = pso_1_exif_dict[p1_key]
                    if p1_val in pso_2_exif_dict.values(): #find the index in the second dict
                        ind = pso_2_exif_dict.values().index(p1_val)
                        p2_key = pso_2_exif_dict.keys()[ind]
                        self.name_relation_dict[p1_key]         = p2_key #add to dictionary a field "photoNameinProj1":"photoNameinProj2"
                        self.inverse_name_relation_dict[p2_key] = p1_key
        return self.name_relation_dict, self.inverse_name_relation_dict


    def getDoubledNames(self):
        """ Iterate over the twin photo names and check if the EXIF match. Return (verifiedTwinPhotoNames, twinNamesWithOtherEXIF) """
        verifiedTwinPhotoNames, twinNamesWithOtherEXIF = [], []
        with open(self.psObject1.url) as f1:
            pso_1_listing = json.load(f1)
            with open(self.psObject2.url) as f2:
                pso_2_listing = json.load(f2)
                doubled_photo_names = list(set(pso_1_listing['photos']).intersection(pso_2_listing["photos"]))
                for photoName in doubled_photo_names:
                    if self.verifyCameraRedundancy(os.path.join(self.psObject1.inputDir, photoName), os.path.join(self.psObject2.inputDir, photoName)):
                        verifiedTwinPhotoNames.append(photoName)
                    else:
                        twinNamesWithOtherEXIF.append(photoName)
                return verifiedTwinPhotoNames, twinNamesWithOtherEXIF
        return verifiedTwinPhotoNames, twinNamesWithOtherEXIF

    def verifyCameraRedundancy(self, url1, url2):
        """Checks if photos ware made with the same camera and the same parameters"""
        sfmDG = SfMDataGenerator.SfMDataGenerator(log = self.log)
        if sfmDG.getExifDict(url1, self.EXIF_keys) == sfmDG.getExifDict(url2, self.EXIF_keys):
            return True
        return False

    def getPhotoNameTransformationDict(self, doubledNamesWithOtherEXIF):
        """Generate a new name list for the provided file names"""
        tr_dict = {}
        for twName in doubledNamesWithOtherEXIF:
            tr_dict[twName] = support_functions.modifyFileName(twName)
        return tr_dict

    def mergeProjects(self):
        if os.path.isdir(self.outputDirUrl):
            if self.psObject1.successful and self.psObject2.successful or self.psObject1.sparse_reconstruction and self.psObject2.sparse_reconstruction:
                self.psObjectOut.successful = True
                if self.psObject1.sparse_reconstruction and self.psObject2.sparse_reconstruction:
                    self.psObjectOut.sparse_reconstruction = True
                    self.name_relation_dict, self.inverse_name_relation_dict = self.getTwinPhotosRelationDict()
                    if len(self.name_relation_dict) >= 3: #we require at least 3 identical photos to merge two projects
                        support_functions.copyImages(self.psObject1.inputDir, self.psObjectOut.inputDir) #copy all photos from the first project
                        """ What if different photos have the same name?"""
                        doubledNamesWithTheSameEXIF, doubledNamesWithOtherEXIF = self.getDoubledNames() #find the doubled photo names
                        pso2_name_trans_dict = self.getPhotoNameTransformationDict(doubledNamesWithOtherEXIF) #modify the names of different photos with the same name
                        """Copy the images, but change the name of some files. Photos already existing and copied from proj_1 are not copied"""

                        support_functions.copyImages(self.psObject2.inputDir, self.psObjectOut.inputDir, dont_copy=self.name_relation_dict.values(), change_name_dict=pso2_name_trans_dict)

                        self.psObjectOut.photos = support_functions.getImagesList(self.outputDirUrl) #make a list of all files copied to the folder
                        if support_functions.fileNotEmpty( self.psObject1.openMVGSfMOutputFile) or support_functions.fileNotEmpty(self.psObject2.openMVGSfMJSONOutputFile):
                            sfmDM = SfMDataMerge.SfMDataMerge(self._getSfmUrls(), root_path=self.outputDirUrl)
                            sfmDM.mergeSfMFiles(self.name_relation_dict, pso2_name_trans_dict)

                            self.psObjectOut.successful = False  # it is a merged project so incremetal photogrammetry is not allowed
                            self.psObjectOut.sparse_reconstruction = True  # but allow to compute the dense reconstruction
                            self.psObjectOut.saveCurrentStatus()
                            return self.psObjectOut.openMVGSfMJSONOutputFile
                        else:
                            self.log(["Could not save the project"])
                    # TODO: try to merge the project by computing features and doing the matching
                    else:
                        self.log(["mergeWarning"])  # popup with a warning that projects contain less identical photos than 3
                else:
                    self.log(["You must provide projects with computed sparse reconstruction"])
            else:
                self.log(["You must provide projects that ware successfuly initialized !!"])
        else:
            self.log(["Provided output project URL doesnt exist", self.outputDirUrl])


    def _getSfmUrls(self):
        """Choose the ascii or bin sfm_data.json file"""
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
    #url_out = "/home/string/Documents/gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/merged"
    #pso1 = ProjectStatus.ProjectStatus("/home/string/Documents/gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part1/output/projectStatus.json")
    #pso2 = ProjectStatus.ProjectStatus("/home/string/Documents/gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/Mirow/part2/output/projectStatus.json")
    url_out = "/home/string/Documents/gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/twinPhotos/merged"
    pso1 = ProjectStatus.ProjectStatus("/home/string/Documents/gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/twinPhotos/part1/output/projectStatus.json")
    pso2 = ProjectStatus.ProjectStatus("/home/string/Documents/gritworld/Incremental3DRecon/GritRena/test/data/projectMerge/twinPhotos/part2/output/projectStatus.json")
    pm = ProjectMerge(pso1, pso2, url_out)
    pm.mergeProjects(mode="NORMAL")