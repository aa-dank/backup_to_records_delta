def build_file_list(someDir, fileList = [], ignoreThumbs = True):
    for root, dirs, files in os.walk(someDir):
        if files:
            for file in files:
                filePath = os.path.join(root, file)
                if ignoreThumbs:
                    if filePath not in fileList and file.split('.')[0] != "Thumbs":
                        fileList.append(filePath)
                else:
                    if filePath not in fileList:
                        fileList.append(filePath)
    return fileList

def glob_file_list(someDir):
    return set(f.name for f in Path(someDir).rglob('*'))



def cmp_file_lists(dir1, dir2):
    dir1List = build_file_list(dir1, fileList = [], ignoreThumbs = True)
    dir2List = build_file_list(dir2, fileList = [], ignoreThumbs = True)
    same = 0
    for dir2file in dir2List:
        for dir1file in dir1List:
            if filecmp.cmp(dir1file, dir2file):
                dir1List.remove(dir1file)
                dir2List.remove(dir2file)
                same +=1
                break
    print("Same: " + str(same))
    return (dir1List, dir2List)


def file_df_discrepancies(targetDF, currentDF):
    '''targetDF is dataframe of backup which shou;ld have no different files from most current server as represented in currentDF'''
    def filepath_is_similar(filepath1, filepath2):
        similar = False
        path1List = splitall(filepath1)[1:-1]
        path2List = splitall(filepath2)[1:-1]
        if len(path1List) == len(path2List):
            try:
                if path2List[-1] == path1List[-1] and path2List[-2] == path1List[-2]:
                    similar = True
            except:
                pass
        return similar

    for targetIndex, targetRow in targetDF.iterrows():
        currentSameType = currentDF[currentDF["Extension"] == targetRow['Extension']]
        if targetRow["Name"] in currentSameType["Name"].values:

            currentSameName = currentSameType[currentSameType["Name"] == targetRow["Name"]]
            for currentIndex, currentRow in currentSameName.iterrows():
                # check if filesize is within 550bits or they share same last two directories in directory path
                if (abs(float(currentRow["Filesize"]) - float(targetRow["Filesize"])) < 550) or (filepath_is_similar(
                    targetRow["Filepath"], currentRow["Filepath"])):
                    currentDF.drop(currentIndex, inplace=True)
                    targetDF.drop(targetIndex, inplace=True)
                    break
                else:
                    pass
    return targetDF
'''
        #legacy code 
        for currentIndex, currentRow in currentSameType.iterrows():
            #compare filename and filesize to see if same file
            if currentRow["Name"] == targetRow["Name"] :
                #check if filesize is within 550bits or they have same last two directories in directory path
                if abs(float(currentRow["Filesize"]) - float(targetRow["Filesize"])) < 550 or filepath_is_similar(targetRow["Filepath"], currentRow["Filepath"]):
                    currentDF.drop(currentIndex, inplace=True)
                    targetDF.drop(targetIndex, inplace=True)
                    break
                else:
                    pass
    return targetDF'''