import os
import json
import subprocess
import sys
import psutil
import threading
import re
import random
import ast

#import time


import SfMDataGenerator
import support_functions

#TODO match photos one by one
#TODO interface with SD CARD
class Photogrammetry:
    def __init__(self, projecStatusObject, log = None, required_matches = 8):
        #TODO move these variables to projectStatus
        #script_path = os.path.abspath(os.path.dirname(__name__))
        self.OPENMVG_SFM_BIN = os.path.join(projecStatusObject.scriptDir, "../openMVG/openMVG_Build/Linux-x86_64-RELEASE") # Indicate the openMVG binary directory
        self.MVE_BIN = os.path.join(projecStatusObject.scriptDir,"../mve/apps")
        self.TEXRECON_BIN = os.path.join(projecStatusObject.scriptDir,"../mvs-texturing/build/apps/texrecon/texrecon")
        self.CAMERA_DB_FILE = os.path.join(projecStatusObject.scriptDir, "sensor_width_camera_database.txt")
        self.maxRam=0
        self.code=0
        if log == None:
            self.log = support_functions.writeToStdout
        else:
            self.log = log
        self.projectStatusObject = projecStatusObject
        self.required_matches = required_matches
        self.sfmg = SfMDataGenerator.SfMDataGenerator(self.projectStatusObject, self.log)

    class myThread (threading.Thread):
        def __init__(self, pid, pg):
            threading.Thread.__init__(self)
            self.Rpid = pid
            self.pg = pg
            self.running=True
            self.pg.maxRam=0
        def run(self):
            p=psutil.Process(self.Rpid)
            try:
                while self.running:
                    actual_ram=p.memory_percent()
                    if actual_ram>self.pg.maxRam:
                        self.pg.maxRam = actual_ram
            except :
                return None
    
    def RAM_scan(self, p):
        Rthread = self.myThread(p.pid, self)
        Rthread.start()
        code = p.wait()
        Rthread.runing=False
        Rthread.join(5)
        return code
    
    def run_imageListing(self, input_dir, matches_dir, args=[]):
        arg = [os.path.join(self.OPENMVG_SFM_BIN, "openMVG_main_SfMInit_ImageListing"),  "-i", input_dir, "-o", matches_dir, "-d", self.CAMERA_DB_FILE]+args
        self.log(["1. Intrinsics analysis"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_computeFeatures(self, args):
        arg = [os.path.join(self.OPENMVG_SFM_BIN, "openMVG_main_ComputeFeatures")]+args
        self.log(['2.computeFeatures'])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_computeMatches(self, args):
        arg = [os.path.join(self.OPENMVG_SFM_BIN, "openMVG_main_ComputeMatches")]+args
        self.log(['3.computeMatches'])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_globalSfM(self, args):
        arg = [os.path.join(self.OPENMVG_SFM_BIN, "openMVG_main_GlobalSfM")]+args
        self.log(['4.Global Structure from Motion'])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_DataColor(self, args):
        arg = [os.path.join(self.OPENMVG_SFM_BIN, "openMVG_main_ComputeSfM_DataColor")]+args
        self.log(["5. Colorize Structure"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_MVG2MVE2(self, args):
        arg = [os.path.join(self.OPENMVG_SFM_BIN, "openMVG_main_openMVG2MVE2")]+args
        self.log(['6. Transfer to MVE format'])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)

    def run_dmrecon(self, args):
        arg = [os.path.join(self.MVE_BIN, "dmrecon", "dmrecon")]+args
        self.log(["7. Run MVE::dmrecon"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
        
    def run_scene2pset(self, args):
        arg = [os.path.join(self.MVE_BIN, "scene2pset", "scene2pset"),] + args
        self.log(["8. Generate point set with MVE::scene2pset"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_fssrecon(self, args):
        arg = [os.path.join(self.MVE_BIN, "fssrecon", "fssrecon")] + args
        self.log(["9. Surface reconstruction with MVE::fssrecon"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_meshclean(self, args):
        arg = [os.path.join(self.MVE_BIN, "meshclean", "meshclean")] + args
        self.log(["10. Surface cleaning with MVE::meshclean"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)
    
    def run_texrecon(self, args):
        arg = [self.TEXRECON_BIN]+args
        self.log(["11. Surface texturing with texrecon::texrecon"])
        p = subprocess.Popen(arg)
        return self.RAM_scan(p)

    """Generate the sparse model from the data"""
    def getSparseReconstruction(self):
        self.log(["Generate the sparse model from the data"])
        if support_functions.fileNotEmpty(self.projectStatusObject.matchesFile):
            self.run_globalSfM(["-i", self.projectStatusObject.imageListingFile, "-o", self.projectStatusObject.reconstructionDir, "-m", self.projectStatusObject.matchesDir])
            if support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMOutputFile) or support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMJSONOutputFile):
                if support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMOutputFile):
                    sfmFileUrl = self.projectStatusObject.openMVGSfMOutputFile
                else:
                    sfmFileUrl = self.projectStatusObject.openMVGSfMJSONOutputFile
                self.run_DataColor(["-i", sfmFileUrl, "-o", self.projectStatusObject.openMVGSfMColorizedOutputFile])
                colorized_ply_generated = support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMColorizedOutputFile)
                if colorized_ply_generated:
                    self.projectStatusObject.sparse_reconstruction = True
                self.projectStatusObject.saveCurrentStatus()
        return self.projectStatusObject.sparse_reconstruction

    """Generate the dense point cloud from data """
    def getDenseReconstruction(self, scale):
        self.log(["Generate the dense point cloud from data"])
        if support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMOutputFile):
            sfmFileUrl = self.projectStatusObject.openMVGSfMOutputFile
        else:
            sfmFileUrl = self.projectStatusObject.openMVGSfMJSONOutputFile

        if support_functions.fileNotEmpty(sfmFileUrl):
            self.run_MVG2MVE2(["-i", sfmFileUrl, "-o", self.projectStatusObject.reconstructionDir])
            if support_functions.fileNotEmpty(self.projectStatusObject.mveMainFile):
                if self.projectStatusObject.roi_scale:
                    roi = self.getROI(self.projectStatusObject.roi_scale)
                    roi_option_str = '--bounding-box=' + ','.join(map(str,roi)) # argument of the bounding box
                    print "ROI OPTION STR", roi_option_str
                else:
                    roi_option_str = ''
                if not self.run_dmrecon(["--force", "--scale="+str(scale), roi_option_str, self.projectStatusObject.mveDir]):
                    self.run_scene2pset([self.projectStatusObject.mveDir, "-pcsn", "-F"+str(scale), self.projectStatusObject.mveScene2PsetOutputFile])
                    if support_functions.fileNotEmpty(self.projectStatusObject.mveScene2PsetOutputFile):
                        self.log(["Clean the point set"])
                        self.run_meshclean(["--threshold=0.99", "--component-size=0", "--no-clean", self.projectStatusObject.mveScene2PsetOutputFile, self.projectStatusObject.mvePsetCleanOutputFile])
                        return True

    """Generate the mesh from point cloud """
    def getMesh(self, scale):
        if support_functions.fileNotEmpty(self.projectStatusObject.mvePsetCleanOutputFile):
            self.run_fssrecon(["--interpolation=cubic", "--scale-factor=" + str(float(scale)), self.projectStatusObject.mvePsetCleanOutputFile, self.projectStatusObject.mveFSSReconOutputFile])
            if support_functions.fileNotEmpty(self.projectStatusObject.mveFSSReconOutputFile):
                self.run_meshclean(["--percentile=10", "--delete-scale", "--delete-conf", self.projectStatusObject.mveFSSReconOutputFile, self.projectStatusObject.mveMeshCleanOutputFile])
                if support_functions.fileNotEmpty(self.projectStatusObject.mveMeshCleanOutputFile):
                    self.projectStatusObject.dense_reconstruction = True
                    self.projectStatusObject.saveCurrentStatus()
                    return True

    """Generate the final mesh model from data """
    def getFinalReconstruction(self, scale):
        if self.getDenseReconstruction(scale):
            if self.getMesh(scale):
                return True
        """
        if self.fileNotEmpty(self.projectStatusObject.openMVGSfMOutputFile):
            self.run_MVG2MVE2(["-i", self.projectStatusObject.openMVGSfMOutputFile, "-o", self.projectStatusObject.reconstructionDir])
            if self.fileNotEmpty(self.projectStatusObject.mveMainFile):
                if self.projectStatusObject.roi_scale:
                    roi = self.getROI(self.projectStatusObject.roi_scale)
                    roi_option_str = '--bounding-box=' + ','.join(map(str,roi)) # argument of the bounding box
                    print "ROI OPTION STR", roi_option_str
                else:
                    roi_option_str = ''
                if not self.run_dmrecon(["--force","--scale="+str(scale), roi_option_str, self.projectStatusObject.mveDir]):
                    self.run_scene2pset([self.projectStatusObject.mveDir, "-pcsn", "-F"+str(scale), self.projectStatusObject.mveScene2PsetOutputFile])
                    if self.fileNotEmpty(self.projectStatusObject.mveScene2PsetOutputFile):
                        self.run_fssrecon(["--interpolation=cubic", "--scale-factor="+str(float(scale)), self.projectStatusObject.mveScene2PsetOutputFile, self.projectStatusObject.mveFSSReconOutputFile])
                        if self.fileNotEmpty(self.projectStatusObject.mveFSSReconOutputFile):
                            self.run_meshclean(["--percentile=10", "--delete-scale", "--delete-conf", "--delete-color", self.projectStatusObject.mveFSSReconOutputFile, self.projectStatusObject.mveMeshCleanOutputFile])
                            if self.fileNotEmpty(self.projectStatusObject.mveMeshCleanOutputFile):
                                self.projectStatusObject.dense_reconstruction = True
                                self.projectStatusObject.saveCurrentStatus()
                                return True
        """

    """ Texture the output mesh"""
    def getTexturedReconstruction(self):
        if support_functions.fileNotEmpty(self.projectStatusObject.mveMeshCleanOutputFile):
            self.run_texrecon(["","--no_intermediate_results","--keep_unseen_faces",self.projectStatusObject.mveDir + "::undistorted", self.projectStatusObject.mveMeshCleanOutputFile, self.projectStatusObject.mveTextureOutputFileNoExtension])
            if support_functions.fileNotEmpty(self.projectStatusObject.mveTextureOutputFile):
                self.projectStatusObject.textured_reconstruction = True
                self.projectStatusObject.saveCurrentStatus()
                return True

    """Incremental initialization"""
    def getIncrementalInitialization(self):
        self.log(["Initializing...", "Working directory:", self.projectStatusObject.outputDir, "Please be patient", "You can view the progress in the terminal..."])
        """ List the images, compute the features and matches """
        #self.run_imageListing(self.projectStatusObject.inputDir, self.projectStatusObject.featuresDir)
        self.sfmg.getSfMData()
        photo_names = self.getListedPhotoNames(self.projectStatusObject.imageListingFile)
        self.run_computeFeatures(["-i", self.projectStatusObject.imageListingFile, "-o", self.projectStatusObject.featuresDir, "-p", self.projectStatusObject.mode, "-m", "SIFT", "-f", "1", "--numThreads", "3"])
        self.run_computeMatches(["-i", self.projectStatusObject.imageListingFile, "-g", "e", "-f", "1", "-o", self.projectStatusObject.matchesDir])
        """ Check if the matching process was successful """
        status = support_functions.fileNotEmpty(os.path.join(self.projectStatusObject.matchesDir, 'matches.e.txt'))
        if status:
            self.run_globalSfM(["-i", self.projectStatusObject.imageListingFile, "-o", self.projectStatusObject.reconstructionDir, "-m", self.projectStatusObject.matchesDir])
            self.log(["Photos matched succesfully"])
        status = support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMOutputFile) or support_functions.fileNotEmpty(self.projectStatusObject.openMVGSfMJSONOutputFile)
        """ Get the good and bad photo list """
        wrong_photo_names                       = self.getWrongPhotoNames(self.projectStatusObject.imageListingFile, self.projectStatusObject.geoMatchesFile)
        good_photo_names                        = list(set(photo_names) - set(wrong_photo_names)) #remove wrong photos from good photos
        self.log(["Correct photos:"] + photo_names + ["Wrong photos:"] + wrong_photo_names)
        self.projectStatusObject.successful     = status
        self.projectStatusObject.photos         = good_photo_names
        self.projectStatusObject.wrong_photos   = wrong_photo_names
        self.log(["Project saved"])
        self.projectStatusObject.saveCurrentStatus()
        return status

    def getWrongPhotoNames(self, sfm_json_file_url, geo_matches_file_url):
        self.log(["Get wrong photo names"])
        node_symbol_img_name_list = self.getNodeSymbolsAndImgNamesFromSfMJson(sfm_json_file_url)
        matches_symbol_list       = self.getMatchLines(geo_matches_file_url)
        isolated_nodes_list       = []
        for node_symbol_and_img_name in node_symbol_img_name_list: #find the nodes that are not connected with other
            nodeSymbolFound = False
            for matchSymbol in matches_symbol_list:
                if node_symbol_and_img_name[0] in matchSymbol:
                    nodeSymbolFound = True
                    break
            if not nodeSymbolFound:
                img_name = '.'.join([node_symbol_and_img_name[1], node_symbol_and_img_name[2]])
                isolated_nodes_list.append(img_name)
        return isolated_nodes_list

    def getWeakNodes(self, new_reused_photos_list):
        """ List nodes according to the number of their matches.
         Returnes a list of photo name. """
        self.log(["List nodes according to the number of their matches. Returnes a list of photo name."])
        pre_list, output_list = [], []
        matches_sum = 0
        node_symbols_name_extension = self.getNodeSymbolsAndImgNamesFromSfMJson(self.projectStatusObject.imageListingFile)
        with open(self.projectStatusObject.geoMatchesFile) as f:
            geo_matches_file_str =  f.read()
            for record in node_symbols_name_extension:
                node_symbol = record[0] + ' '
                """ Add the occurences in front of the line """
                occurences = len([m.start() for m in re.finditer(node_symbol, geo_matches_file_str)])
                node_symbol = record[0] + '\n'
                """ Add the occurences at the end of the line """
                occurences += len([m.start() for m in re.finditer(node_symbol, geo_matches_file_str)])
                """ Decrease the number of occurences by one, because of the node symbol at the begining of the file """
                occurences -= 1
                matches_sum += occurences
                pre_list.append(['.'.join([record[1],record[2]]), occurences])
            pre_list.sort(key = lambda tup: tup[1]) #sort according to occurence
        n = len(pre_list)
        putative_average = (n-1)/2
        geometric_average = matches_sum/n
        self.log(["Putative matching average: ", str(putative_average)])
        self.log(["Geometric matching average: ", str(geometric_average)])
        for element in pre_list:
            if element[1] == 0: #checking if it's not a wrong_photo
                self.projectStatusObject.wrong_photos = list(set(self.projectStatusObject.wrong_photos + [element[0]]))
                self.projectStatusObject.photos = list(set(self.projectStatusObject.photos) - set([element[0]]))
            elif element[1] < geometric_average:
                output_list.append(element[0])

        output_list = list(set(output_list) - set(self.projectStatusObject.wrong_photos) - set(new_reused_photos_list))
        self.log(["Weak node photos:"]+ output_list)
        self.projectStatusObject.saveCurrentStatus()
        return output_list

    def getNodeSymbolsAndImgNamesFromSfMJson(self, url):
        self.log(["Get node symbols and image names from Structure from Motion JSON"])
        name_list = []
        with open(url) as f:
            jsonDat = json.loads(f.read())
            for view in jsonDat["views"]:
                name_list.append([self.projectStatusObject.nodePrefix + str(view["key"])]+str(view["value"]["ptr_wrapper"]["data"]["filename"]).split('.'))
        return name_list

    def getIncrementalAppend(self, new_reused_photos_list, selected_photo_names=[], matchingOption = "toAllNodes"):
        """ Compute new photos and merge them to the final project"""
        self.log(["Compute new photos and merge them to the final project"])
        """ Get rid of the reused photos"""
        old_listed_photos = self.getListedPhotoNames(self.projectStatusObject.imageListingFile)
        new_photos_list = list(set(new_reused_photos_list) - set(old_listed_photos))
        print "DUPA UDPA", len(new_photos_list)
        if len(new_photos_list) > 0:
            """ Make an image listing from only the new photos just for feature computing """
            #self.getIncrementalOpenMVGImageListing(new_photos_list)
            self.sfmg.getIncrementalSfMData(new_photos_list, self.projectStatusObject.imageListingFile, self.projectStatusObject.inputDir, self.projectStatusObject.incrImageListingFile, newPhotosOnly = True)
            """ Compute the features of the new photos """
            self.run_computeFeatures(["-i", self.projectStatusObject.incrImageListingFile, "-o", self.projectStatusObject.featuresDir, "-p", self.projectStatusObject.mode, "-m", "SIFT", "-f", "1", "--numThreads", "3"])
            #""" Get a list of weak photo nodes before we make a list containing the new images"""
            #weak_photo_names = self.getWeakNodes(new_reused_photos_list)
            """ Than make a listing of all photos """
            #new_nodes_list = self.getExtendedOpenMVGImageListingUrl(self.projectStatusObject.imageListingFile, new_photos_list)
            #newPhotoList, oldSfMDataUrl, inputPhotoDir, outputSfMDataUrl
            new_nodes_list = self.sfmg.getIncrementalSfMData(new_photos_list, self.projectStatusObject.imageListingFile, self.projectStatusObject.inputDir, self.projectStatusObject.imageListingFile)
            #print "NEW NODES LIST", new_nodes_list
            #exit()

        else:
            new_nodes_list =[]
        #time.sleep(5)
        """ Next make a pairlist to match only the new photos to old photos or reinforce old photos. Returnes a list of (node_number, PhotoName) """
        incrementalOpenMVGPairListUrl = self.getIncrementalPairListUrl(matchingOption, selected_photo_names)
        #time.sleep(5)
        """ Now match new photos to old ones. We don't match new photos between each other"""
        self.run_computeMatches(["-i", self.projectStatusObject.imageListingFile, "-g", "e", "-f", "1", "-o", self.projectStatusObject.incrMatchesDir, "--pair_list", incrementalOpenMVGPairListUrl])
        """ If the result is non 0 bytes big, merge it with the old result """
        wrong_new_photos, good_new_photos = new_reused_photos_list, []
        if self.mergeMatchingResults2(old_listed_photos): #if some of the new photos ware successfully matched with the old photos
            """ Get the good and wrong nodes """
            reused_node_list = self.getReusedNodesList(list(set(new_reused_photos_list) - set(new_photos_list) ))
            good_new_photos, wrong_new_photos = self.getGoodWrongPhotos(self.projectStatusObject.incrGeoMatchesFile, new_nodes_list+reused_node_list)
            """ Update good photos in project status """
            self.projectStatusObject.photos = self.projectStatusObject.photos + good_new_photos
        """ Update wrong photos in project status """
        self.projectStatusObject.wrong_photos += wrong_new_photos
        """ Save the project state """
        self.log(["Saving project state"])
        json_status = self.projectStatusObject.saveCurrentStatus()
        #TODO check the len
        if len(new_nodes_list) == 1:
            json_status["connections"] = len(self.getNodeMatches(new_nodes_list[0][0]))#, self.projectStatusObject.geoMatchesFile))
        """ Return the status """
        return json_status

    def getIncrementalPairListUrl(self, matchingMode, selected_photo_names = []):
        self.log(["Generates a file with a list of nodes to be matched "])
        good_nodes, wrong_nodes, new_nodes, weak_nodes, selected_nodes = [], [], [], [], []
        #goes along the features/sfm_data.json file and classifies the nodes as wrong/good/weak
        with open(self.projectStatusObject.imageListingFile) as f:
            jsonImageListing = json.load(f)
            for view in jsonImageListing['views']:
                filename = str(view["value"]["ptr_wrapper"]["data"]["filename"])
                """ Good photos are stored in the projectStatus.photos list"""
                if filename in self.projectStatusObject.photos:
                    good_nodes.append(view["key"])
                    #""" We asume that weak nodes are a part of the good nodes"""
                    #if filename in weak_photo_names:
                    #    weak_nodes.append(view["key"])
                    """ Selected photos are a part of the good nodes too """
                    if filename in selected_photo_names:
                        selected_nodes.append(view["key"])
                elif filename in self.projectStatusObject.wrong_photos:
                    wrong_nodes.append(view["key"])
                else:
                    new_nodes.append(view["key"])
        #print "MATCHING MODE", matchingMode
        #print "NEW NODES", new_nodes
        #print "WRONG NODES", wrong_nodes
        #print "GOOD NODES",  good_nodes
        #time.sleep(5)
        if matchingMode == "toAllNodes":
            return self.getIncrementalPairList(good_nodes + new_nodes, new_nodes)
        #elif matchingMode == "toWeakNodes":
        #    self.log(["Generates a file with a list of weak nodes to be matched with new photos"])
        #    return self.getIncrementalPairList(weak_nodes + new_nodes, new_nodes)
        #elif matchingMode == "toSmartChoosenNodes":
        #    self.log(["Generates a file with a list of smart choosen nodes to be matched with new photos"])
        #    """ Smart chosen node set consists of weak_nodes, new_nodes and some random choosen nodes from the best_good photos"""
        #    smartList = list(set(weak_nodes + self.getRandomSubsample(good_nodes) + new_nodes))
        #    return self.getIncrementalPairList(smartList, new_nodes)
        elif matchingMode == "toSelectedPhotos":
            """ Generate a file with a list of selected nodes and corresponding matches """
            self.log(["Generates a file with a list of selected nodes and corresponding matches"])
            selected_nodes_and_matches = list(set(self.getMatchesList(selected_nodes) + selected_nodes))
            print "SELECTED NODES", selected_nodes
            print "SELECTED NODES AND MATCHES", selected_nodes_and_matches
            return self.getIncrementalPairList(selected_nodes_and_matches, new_nodes)
        elif matchingMode == "toNewestPhotos":
            self.log(["Generates a file with a list of newest nodes and corresponding matches"])
            newest_nodes = self.getNewestNodes(self.projectStatusObject.newPhotosMatchingNumber)
            newest_nodes_and_matches = self.getMatchesList(newest_nodes)
            selected_nodes_and_matches = list(set(self.getMatchesList(selected_nodes) + selected_nodes))
            return self.getIncrementalPairList(newest_nodes_and_matches + selected_nodes_and_matches, new_nodes)
        elif matchingMode == "reinforceStructure":
            self.log(["Generate a file with a list of nodes and corresponding matches that dont occure in the geometric matches"])
            return self.getReinforcingPairList(good_nodes+new_nodes)

    def getMatchesList(self, nodes):
        """ Returnes a list of nodes that are matching the nodes from the provided list """
        self.log(["Returnes a list of nodes that are matching the nodes from the provided list"])
        matches_list = []
        for node in nodes:
            matches_list += self.getNodeMatches(node)
        return list(set(matches_list + nodes))

    def getNodeMatches(self, node, graph = None):
        """ Returnes a list of matches corresponding to the provided node"""
        self.log(["Returnes a list of matches corresponding to the %s node" % str(node)])
        if graph == None:
            graph = self.projectStatusObject.geoMatchesFile
        matching_lines = self.getMatchLines(graph)
        node_symbol = self.projectStatusObject.nodePrefix + str(node)
        node_matches = []
        for match_line in matching_lines:
            match_line = match_line + ' '
            if match_line.find(node_symbol+' ') != -1:
                matching_number = match_line.replace(node_symbol, '').replace('--','').replace('n','')
                matching_number = matching_number.rstrip().lstrip()
                #self.log(["Extaracted:", matching_number])
                matching_number = ast.literal_eval(matching_number)
                node_matches.append(matching_number)
        return node_matches

    def mergeMatchingResults2(self, old_listed_photos):
        self.log(["Merge the matching results 2"])
        if support_functions.fileNotEmpty(self.projectStatusObject.incrMatchesFile): #if there was at least one match
            old_node_symbols = self.photoNames2NodeSymbols(old_listed_photos)
            match_lines      = self.getMatchLines(self.projectStatusObject.incrGeoMatchesFile)
            """ Check if ther's at least one match between the new nodes and old nodes """
            old_node_matched = False
            self.log(["Check if there is at least one match between the new nodes and old nodes"])
            #self.log(match_lines)
            #self.log(old_node_symbols)
            for match_line in match_lines:
                for old_node_symbol in old_node_symbols:
                    if match_line.find(old_node_symbol + ' ') != -1: #a match with the old node found at the begining of the line
                        old_node_matched = True
                        break
                    elif  match_line.find(old_node_symbol + '\n'): #a match with the old node found at the end of the line
                        old_node_matched = True
                        break
                if old_node_matched == True:
                    break
            if old_node_matched :
                self.log(["At least one match between the new node and the old ones found"])
                self.log(["Merge the matches.e.txt files"])
                with open(self.projectStatusObject.matchesFile, 'a') as fbw:  # open for appending the base matches file
                    with open(self.projectStatusObject.incrMatchesFile) as fi:  # open for reading the incremented matches file
                        fbw.write(fi.read())
                self.log(["Merge the geometric matches files "])
                self.mergeGeometricMatches()
                return True
            else:
                self.log(["No matches between the new node and the old ones found"])
        return False

    def photoNames2NodeSymbols(self, photo_names_list):
        self.log(["Generate node symbol list from phot names list"]+ photo_names_list)
        node_symbols_image_names_extensions = self.getNodeSymbolsAndImgNamesFromSfMJson(self.projectStatusObject.imageListingFile)
        node_symbol_list = []
        for record in node_symbols_image_names_extensions:
            file_name = '.'.join(record[1:])
            if file_name in photo_names_list:
                node_symbol_list.append(record[0])
        return node_symbol_list

    def getRandomSubsample(self, elem_list):
        """ Choose a random subset of photos from the provided list """
        self.log(["Choose a random subset of photos from the provided list"])
        max_sample_size = len(elem_list)
        indexes = random.sample(range(max_sample_size), min(self.projectStatusObject.newPhotosMatchingNumber, max_sample_size))
        output_list = []
        for index in indexes:
            output_list.append(elem_list[index])
        return output_list

    def getIncrementalPairList(self, good_nodes, new_nodes):
        """ Generate a pair list file that matches all new images to all good old images """
        self.log(["Generate a pair list file that matches all new images to all good old images"])
        output_str = ''
        with open(self.projectStatusObject.incrPairListFile, 'w') as f:
            for good_node in good_nodes:
                for new_node in new_nodes:
                    if new_node != good_node:
                        output_str += str(good_node) + ' ' + str(new_node)+'\n'
            f.write(output_str)
        #self.log(["Pair matching: ", output_str])
        return self.projectStatusObject.incrPairListFile

    def getReinforcingPairList(self, nodes):
        self.log(['Generate a pair list that reinforces the structure'])
        output_str = ''
        with open(self.projectStatusObject.incrPairListFile, 'w') as f:
            output_str = self.getReinforcingPairListString(nodes)
            f.write(output_str)
        #self.log(["Pair matching: ", output_str])
        return self.projectStatusObject.incrPairListFile

    def getReinforcingPairListString(self, nodes):
        output_str =''
        pair_list = []
        for node in nodes:
            node_matches = self.getMatchesList([node])
            nodes_to_be_matched = list(set(nodes) - set(node_matches) - set([node]))
            for to_match_node in nodes_to_be_matched:
                pair = set([node, to_match_node])
                if pair not in pair_list:
                    pair_list.append(pair)
                    output_str += str(node) + ' ' + str(to_match_node) + '\n'
        return output_str

    def getReusedNodesList(self, reused_photos_list):
        self.log(["Get a list of nodes that ware reused (node_number, photo_name)"])
        reused_node_list = []
        with open(self.projectStatusObject.imageListingFile) as f:
            image_listing = json.load(f)
            views = image_listing['views']
            for view in views:
                file_name = str(view["value"]["ptr_wrapper"]["data"]["filename"])
                id = view["key"]
                if file_name in reused_photos_list:
                    reused_node_list.append((id, file_name))
        return reused_node_list

    def getGoodWrongPhotos(self, incrGeoMatchesFileUrl ,new_nodes_list):
        self.log(["Based on matching data decide if the photo was matched or not"])
        matching_lines = self.getMatchLines(incrGeoMatchesFileUrl)
        matching_str = ''.join(matching_lines)
        good_photos , bad_photos = [], []
        for new_node in new_nodes_list:
            #TODO white sign at the end of the line
            node_symbol = self.projectStatusObject.nodePrefix + str(new_node[0])
            if matching_str.find(node_symbol + ' ') != -1 or matching_str.find(node_symbol + '\n') != -1:
                good_photos.append(new_node[1])
            else:
                bad_photos.append(new_node[1])
        return good_photos, bad_photos

    def mergeMatchingResults(self):
        self.log(["Merge the matching results"])
        if support_functions.fileNotEmpty(self.projectStatusObject.incrMatchesFile):
            self.log(["Merge the matches.e.txt files"])
            with open(self.projectStatusObject.matchesFile, 'a') as fbw:   #open for appending the base matches file
                with open(self.projectStatusObject.incrMatchesFile) as fi: #open for reading the incremented matches file
                    fbw.write(fi.read())
            self.log(["Merge the geometric matches files "])
            self.mergeGeometricMatches()
            return True
        else:
            return False

    def mergeGeometricMatches(self):
        self.log(["Merges two geometric_matches files "])
        mergedFileContent, dash_found = '', False
        with open(self.projectStatusObject.incrGeoMatchesFile,'rb') as incrementalFile:
            for line in incrementalFile:
                if line.find('--') != -1 and not dash_found:
                    dash_found=True
                    mergedFileContent += '\n'.join(self.getMatchLines(self.projectStatusObject.geoMatchesFile))+'\n'  # write new matches at the end
                mergedFileContent += line
        if mergedFileContent != '':
            with open(self.projectStatusObject.geoMatchesFile, 'wb') as baseFile:
                baseFile.write(mergedFileContent)

    def getMatchLines(self, url):
        self.log(["Return a list containing lines with -- "])
        matchesSymbolList = []
        with open(url) as f:
            for line in f:
                if line.find('--') != -1:
                    matchesSymbolList.append(line.rstrip())
        return matchesSymbolList

    def getExtendedOpenMVGImageListingUrl(self, image_listing_file_url, new_photos_list):
        self.log(["Make an extended image listing from the old listing and the new list of photos "])
        new_node_list = []
        with open(image_listing_file_url) as f:
            image_listing = json.load(f)
            views = image_listing['views']
            i = len(views)
            for photo_name in new_photos_list:
                views.append(self.generateViewFromTemplate(photo_name, views[0], i))
                new_node_list.append((i, photo_name))
                i+=1
            image_listing['views'] = views
            with open(image_listing_file_url, 'w') as fw:
                json.dump(image_listing, fw, sort_keys=True, indent = 4)
        return new_node_list

    def getIncrementalOpenMVGImageListing(self, new_photos_list):
        self.log(["Make an image listing from a new photos list. This listing is only used for computing features of new photos"])
        img_listing = {"sfm_data_version" : "0.2", "root_path" : self.projectStatusObject.inputDir, "extrinsics": [], "structure": [], "control_points": []}
        self.log(["Get intrinsic field from the base image listing file"])
        img_listing["intrinsics"] = self.getIntrinsicField(self.projectStatusObject.imageListingFile)
        if len(img_listing["intrinsics"]) == 0 : return None
        else:
            self.log(["Get a view json template from the old image listing, use the first element as a template"])
            first_old_view = self.getViewField(self.projectStatusObject.imageListingFile, 0)
            if first_old_view == None: return None
            else:
                self.log(["Iterate over the new photos list and append the views"])
                new_views, i = [], 0
                for new_photo in new_photos_list:
                    new_view = self.generateViewFromTemplate(new_photo, first_old_view, i)
                    new_views.append(new_view)
                    i+=1
                img_listing["views"] = new_views
                self.log(["Save the views "])
                with open(self.projectStatusObject.incrImageListingFile, 'w') as f:
                    json.dump(img_listing, f, sort_keys=True, indent = 4)
                #return self.projectStatusObject.incrImageListingFile
                return img_listing

    def getListedPhotoNames(self, listing_file_url):
        self.log(["Get listed photo names"])
        photo_name_list = []
        with open(listing_file_url) as f:
            listing_json = json.load(f)
            views = listing_json['views']
            for view in views:
                photo_name_list.append(str(view["value"]["ptr_wrapper"]["data"]["filename"]))
        return  photo_name_list

    def generateViewFromTemplate(self, photo_name, sample_view, i):
        self.log(["Based on an example view json, generate a new view"])
        sample_height       = sample_view["value"]["ptr_wrapper"]["data"]["height"]
        sample_width        = sample_view["value"]["ptr_wrapper"]["data"]["width"]
        sample_local_path   = sample_view["value"]["ptr_wrapper"]["data"]["local_path"]
        sample_id           = sample_view['value']['ptr_wrapper']['id']
        output_view   =       {
            "key": i,
            "value": {
                "ptr_wrapper": {
                    "data": {
                        "filename": photo_name,
                        "height": sample_height,
                        "id_intrinsic": 0,
                        "id_pose": i,
                        "id_view": i,
                        "local_path": sample_local_path,
                        "width": sample_width
                    },
                    "id": sample_id + i
                }
            }
        }
        return output_view

    def getIntrinsicField(self, imageListingFileUrl):
        self.log(["Extract the intrinsic field from the image listing"])
        intrinsinc_json = []
        with open(imageListingFileUrl) as f:
            image_listing_json = json.load(f)
            intrinsinc_json = image_listing_json["intrinsics"]
        return intrinsinc_json

    def getViewField(self, imageListingFileUrl, index):
        self.log(["Extract the view field from the image listing file"])
        view_json = None
        with open(imageListingFileUrl) as f:
            image_listing_json = json.load(f)
            if len(image_listing_json['views']) > index:
                view_json = image_listing_json['views'][index]
        return view_json

    #unused
    def generateNamedMatchesGraph(self):
        """ Reads a file with node matches and outputs a url to a file with the node names changed into photo names """
        with open(self.projectStatusObject.geoMatchesFile) as gmf:
            nodesList = self.getNodeSymbolsAndImgNamesFromSfMJson(self.projectStatusObject.imageListingFile)
            gmStr = gmf.read()
            for node in nodesList:
                gmStr = gmStr.replace(node[0], node[1])
            with open(self.projectStatusObject.namedGeoMatchesFile, "w") as fw:
                fw.write(gmStr)
            return self.projectStatusObject.namedGeoMatchesFile

    def getNewestNodes(self, nodeAmount):
        """ Return a list of nodes """
        newestPhotoNames = self.projectStatusObject.photos[-nodeAmount:]
        photoNames = []
        for photoName in newestPhotoNames:
            photoNames.append(str(photoName).split('.')[0])

        nodeSymbolsNamesExten   = self.getNodeSymbolsAndImgNamesFromSfMJson(self.projectStatusObject.imageListingFile)
        nodeNumbers =[]
        for record in nodeSymbolsNamesExten:
            if record[1] in photoNames:
                nodeNumber = ast.literal_eval(record[0].replace(self.projectStatusObject.nodePrefix, ''))
                nodeNumbers.append(nodeNumber)
        return nodeNumbers

    def getROI(self, scale):
        roiValue = [None,None, None,None, None,None] #minX, maxX, minY, maxY, minZ, maxZ
        viewFolderList = os.listdir(self.projectStatusObject.mveViewsDir)
        for folderName in viewFolderList:
            with open(os.path.join(self.projectStatusObject.mveViewsDir, folderName, self.projectStatusObject.mveMetaDataFileName)) as f:
                content = f.read()
                translationLine = re.findall("translation.*$", content, re.MULTILINE)[0].replace('translation =','').rstrip().lstrip()
                viewPos = []
                for str in translationLine.split():
                    viewPos.append(ast.literal_eval(str))

                    """Xmin"""
                if viewPos[0] < roiValue[0] or roiValue[0] == None:
                    roiValue[0] = viewPos[0]
                    """Xmax"""
                elif viewPos[0] > roiValue[3] or roiValue[3] == None:
                    roiValue[3] = viewPos[0]

                    """Ymin"""
                if viewPos[1] < roiValue[1] or roiValue[1] == None:
                    roiValue[1] = viewPos[1]
                    """Ymax"""
                if viewPos[1] > roiValue[4] or roiValue[4] == None:
                    roiValue[4] = viewPos[1]
                    print "NEW MAXIMUM", viewPos[1]

                    """Zmin"""
                if viewPos[2] < roiValue[2] or roiValue[2] == None:
                    roiValue[2] = viewPos[2]
                    """Zmax"""
                elif viewPos[2] > roiValue[5] or roiValue[5] == None:
                    roiValue[5] = viewPos[2]

        if scale == 1:
            return roiValue
        else:
            roiMiddle = [(roiValue[0]+roiValue[3])/2 , (roiValue[1]+roiValue[4])/2, (roiValue[2]+roiValue[5])/2]

            roiSize   = [abs(roiValue[3]-roiValue[0]),       abs(roiValue[4]-roiValue[1]),    abs(roiValue[5]-roiValue[2])]

            scaledROI = [roiMiddle[0] - round(scale* roiSize[0]/2, 4),
                         roiMiddle[1] - round(scale* roiSize[1]/2, 4),
                         roiMiddle[2] - round(scale* roiSize[2]/2, 4),
                         roiMiddle[0] + round(scale* roiSize[0]/2, 4),
                         roiMiddle[1] + round(scale* roiSize[1]/2, 4),
                         roiMiddle[2] + round(scale* roiSize[2]/2, 4)]


            return  scaledROI
