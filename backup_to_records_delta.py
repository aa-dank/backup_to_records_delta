import os, csv
import pandas as pd
from pprint import pprint
from pathlib import Path
from datetime import datetime

def user_csv_choice():
    '''Prompts user for csv file and checks that the user string corresponds to a file in current directory'''
    aPrompt = "Enter csv filename including its extension." + os.linesep + "(The file must be in same directory as this script.)"
    userStr = input(aPrompt)
    try:
        os.path.isfile(os.path.join(os.getcwd(), userStr))
    except:
        print("error occured with that filename. Try again.")
        user_csv_choice()

    return userStr

def user_chooses_yes(promptText):
    '''asks yes or no question to user and returns 'True' for a yes answer and 'False' for a no answer'''
    yesNo = ['yes', 'y', 'Yes', 'Y', 'No', 'no', 'n', 'N']
    response = ''
    while response not in yesNo:
        response = input(promptText)
    if response in yesNo[4:]:
        return False
    else:
        return True

def establish_csv(defaultName, columnNamesList):
    csvPrompt = "Use %s?" % defaultName

    if user_chooses_yes(csvPrompt):
        csvFile = defaultName
    else:
        csvFile = user_csv_choice()
    csvPath = os.path.join(os.getcwd(), csvFile)

    if not os.path.isfile(csvPath):
        blankCSVdf = pd.DataFrame(columns=columnNamesList)
        blankCSVdf.to_csv(csvPath, index=False, quoting=csv.QUOTE_NONNUMERIC)
    return csvPath

def remove_chars_from_str(toRemove, someChars):
    '''Removes every character in string, someChars, from other string, someStr. Returns string with removed characters
    Also accepts lists of strings.'''
    if type(toRemove) == list:
        return [i.translate({ord(i): None for i in someChars}) for i in toRemove]
    if type(toRemove) == str:
        return toRemove.translate({ord(i): None for i in someChars})
    else:
        print("Error: Wrong Type")

def splitall(path):
    '''splits a path into each piece that corresponds to a mount point, directory name, or file'''
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def build_file_dataframe(chosenDir, DF=None, ignoreThumbs=True):
    '''Scrapes file attributes from the chosenDir path and returns them in a dataframe.'''
    def timestamp_to_date(timestamp):
        DT = datetime.fromtimestamp(timestamp)
        return DT.strftime("%m/%d/%Y, %H:%M:%S")

    def file_data_to_list(root, file):
        filePath = os.path.join(root, file)
        extension = file.split('.')[-1]
        extension = extension.lower()
        name = '.'.join(file.split('.')[:-1])
        now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        try:
            fileStats = os.stat(filePath)
            fileSize = str(fileStats.st_size)
            fileSize.zfill(15)
            fileCreationTime = timestamp_to_date(fileStats.st_ctime)
            fileModifiedTime = timestamp_to_date(fileStats.st_mtime)
            error = None
            retrieved = now
        except:
            fileSize = "123456789"
            fileSize.zfill(15)
            fileCreationTime = now
            fileModifiedTime = now
            error = "error getting file metadata"
            retrieved = now
        return [filePath, file, name, extension, fileSize, fileCreationTime, fileModifiedTime, retrieved, error]


    fileList = []
    for root, dirs, files in os.walk(chosenDir):
        if files:
            for file in files:
                if ignoreThumbs:
                    if file.split('.')[0] != "Thumbs":
                        fileList.append(file_data_to_list(root,file))
                else:
                    fileList.append(file_data_to_list(root, file))

    fileDF = pd.DataFrame(fileList,
                          columns=["Filepath", "File", "Name", "Extension", "Filesize", "Created", "Modified", "Retrieved", "Error"])
    if DF is not None:
        fileDF = DF.append(fileDF)
        fileDF.drop_duplicates(subset="Filepath", keep='first', inplace=True)
    return fileDF

def file_df_discrepancies(targetDF, currentDF):
    '''targetDF is dataframe of backup which should have no different files from most current server as represented in currentDF'''
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

def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


def convert_backup_path(backUpPath, mainPath):
    '''Converts path in backup drive to its equivalent on the records server. If no equivalent directory is found,
    it returns None'''
    mainMount = splitall(mainPath)[0]
    mainPath = os.path.normpath(mainMount)
    mainSubDirs = get_immediate_subdirectories(mainPath)
    backUpPathList = splitall(backUpPath)
    shareStartIndex = None
    backUpMainEquivalent = ""
    converted = []
    dirEquivalentTracking = {}
    equivalenceList = [] #list that keeps number of equivalence numbers
    #look through list of back up directories to see which is most likely the equivalent in main server
    for pathDir in backUpPathList:
        dirEquivalentTracking[pathDir] = {}
        backUpDirNameEdit = remove_chars_from_str(pathDir, ' .,')
        for someDir in mainSubDirs:
            #count number of equal characters in each part of back up path and the directories in the first directory of the main drive
            dirNameEdit = remove_chars_from_str(someDir, ' .,')
            charsEqual = 0
            for i in range(0, len(dirNameEdit) - 1):
                if (len(backUpDirNameEdit) > i) and (dirNameEdit[i] == backUpDirNameEdit[i]):
                    charsEqual += 1
                else:
                    break
            dirEquivalentTracking[pathDir][someDir] = charsEqual
            equivalenceList.append(charsEqual)
    maxEqual = {"backUpDir":"", "mainDir": "", "Max":0}
    if not all([x == 0 for x in equivalenceList]): #if there were any equivalent chars in the directories...
        for backupDir, mainDirsDict in dirEquivalentTracking.items():
            for mainDir, charsEqual in mainDirsDict.items():
                if charsEqual > maxEqual["Max"]:
                    maxEqual["backUpDir"] = backupDir
                    maxEqual["mainDir"] = mainDir
                    maxEqual["Max"] = charsEqual
        shareStartIndex = backUpPath.index(maxEqual["backUpDir"])
        backUpMainEquivalent = maxEqual["backUpDir"]
        for mainSubDir in mainSubDirs: #dunno what purpose this serves
            if (len(backUpMainEquivalent) <= 4) and (backUpMainEquivalent == mainSubDir):
                converted = [mainMount, mainSubDir] + backUpPathList[shareStartIndex - 1:]
            if (len(backUpMainEquivalent) >= 4) and (mainSubDir.startswith(backUpMainEquivalent[:4])):
                converted = [mainMount, mainSubDir] + backUpPathList[shareStartIndex - 1:]
            if (len(backUpMainEquivalent) <= 4) and (backUpMainEquivalent.upper() == mainSubDir):
                converted = [mainMount, mainSubDir] + backUpPathList[shareStartIndex - 1:]
            if (len(backUpMainEquivalent) >= 4) and (mainSubDir.startswith(backUpMainEquivalent[:4].upper())):
                converted = [mainMount, mainSubDir] + backUpPathList[shareStartIndex - 1:]
    else:
        converted = [mainMount]
    if not converted:
        print("error converting backup path to records server path: " + str(backUpPath))
        return None
    return os.path.join(*converted)


def csv_for_use(csvDF, recordsMount, destination):
    resultsDF = csvDF

    recordsColumn = []

    for index, row in resultsDF.iterrows():
        missingFile = row["Filepath"]
        missingFileDirPath = splitall(missingFile)[:-1]
        dirLoc = os.path.join(*missingFileDirPath)
        recordsColumn.append(convert_backup_path(dirLoc, recordsMount))

    resultsDF["Records Drive Loc"] = pd.Series(recordsColumn)
    resultsDF.drop(["Name", "Extension", "Retrieved", "Error" ], axis = 1, inplace = True)
    resultsDF.to_csv(destination, index=False, quoting=csv.QUOTE_NONNUMERIC)
    return resultsDF

def main(backupDir, csvPath, acceptedMissingPath, mainDirectoryMountLetter, columns):
    '''
    backupDir is the path to the backup directory.
    csvPath is the folder where you want csv results to be saved.
    acceptedMissingPath is the complete path including filename to the csv file of acceptable missing files.
    mainDirectoryMountLetter is single char string where the records drive is mounted.
    columns is the list of columns for the dataframes used in the analysis.
    '''
    mainDirectoryMountPoint = mainDirectoryMountLetter + r":\\"
    rawCSVFileName = "raw_missing_DF.csv"
    usableCSVName = "missing_files_records_location.csv"
    mainSubDirs = get_immediate_subdirectories(mainDirectoryMountPoint)
    rawCSVPath = os.path.join(csvPath, rawCSVFileName)
    usableCSVPath = os.path.join(csvPath, usableCSVName)
    #search backup directory for path to the directory that corresponds with the main directory of the records server
    backupDirStart = ''
    for backUpRoot, backUpDirs, backUpFiles in os.walk(backupDir):
        backUpStart = False
        ii = 0

        #check by seeing if at least 8 directory names are the same (without spaces, commas, or periods)
        for dirName in [remove_chars_from_str(i, ' .,') for i in mainSubDirs]:
            if ii > 8:
                backUpStart = True
                break
            if dirName in [remove_chars_from_str(i, ' .,') for i in backUpDirs]:
                ii += 1

        if backUpStart:
            backupDirStart = backUpRoot
            break

    mainBackUpDirs = get_immediate_subdirectories(backupDirStart)
    backUpStartPathLen = len(splitall(backupDirStart))
    if os.path.isfile( rawCSVPath):
        legacyDF = pd.read_csv(rawCSVPath)
    else:
        legacyDF = pd.DataFrame(columns=columns)

    for backUpRoot, backUpDirs, backUpFiles in os.walk(backupDirStart):
        mainPathEquivalent = convert_backup_path(backUpRoot, mainDirectoryMountPoint)
        #if no equivalent path is found in records server
        if not mainPathEquivalent:
            backUpParentList = splitall(backUpRoot)#[:-1]
            backUpFileDF = build_file_dataframe(os.path.join(*backUpParentList))
            legacyDF = legacyDF.append(backUpFileDF)
            legacyDF.drop_duplicates(subset=["Name", "Extension", "Modified"], keep='first', inplace=True)
        else:
            #  If the files and dirs in both the backup directory and working directory are not the same we start the comparison
            #  of the files at the parent directories
            if remove_chars_from_str(os.listdir(backUpRoot), ' .,') != remove_chars_from_str(os.listdir(mainPathEquivalent), ' .,') and backUpRoot != backupDirStart:
                backUpParentList = splitall(backUpRoot)#[:-1]
                mainParentList = splitall(mainPathEquivalent)#[:-1]

                tries = 0
                while tries < 5:
                    tries += 1
                    try:
                        backUpFileDF = build_file_dataframe(os.path.join(*backUpParentList))
                        mainFileDF = build_file_dataframe(os.path.join(*mainParentList))
                        break
                    except: print("error trying to make dataframes for files in")

                deltaDF = file_df_discrepancies(backUpFileDF, mainFileDF)
                backUpDirs[:] = [d for d in backUpDirs if d not in os.listdir(backUpRoot)]
                legacyDF = legacyDF.append(deltaDF)
                legacyDF.drop_duplicates(subset=["Name", "Extension", "Modified"], keep='first', inplace=True)
    if acceptedMissingPath:
        AcceptableMissingDF = pd.read_csv(acceptedMissingPath)
        finalDF = file_df_discrepancies(legacyDF, AcceptableMissingDF)
    finalDF.to_csv(rawCSVPath, index=False, quoting=csv.QUOTE_NONNUMERIC)
    csv_for_use(finalDF, mainDirectoryMountPoint,usableCSVName)
    print("Comparison Complete")



if __name__ == '__main__':
    acceptableMissingCSV = "acceptable_missing.csv"
    #resultsFile = "files_delta.csv"
    columnNames = ["Filepath", "File", "Name", "Extension", "Filesize", "Created", "Modified", "Retrieved", "Error"]
    directoryMount = 'R'
    backUp = ''
    acceptedMissPath = establish_csv(acceptableMissingCSV, columnNames)
    #resultsPath = establish_csv(resultsFile, columnNames)
    while not os.path.isdir(backUp):
        backUp = input("Enter path to backup directory: ")
        if backUp == 'test': #For quick, sloppyu testing
            print("Testing Commencing...")
            backUp = r'F:\29xx   University House - Copy'
            otherDir =  r'F:\29xx   University House'

    #main(backupDir, csvPath, acceptedMissingPath, mainDirectoryMountLetter, columns):
    main(backUp, os.getcwd(), acceptedMissPath, directoryMount, columnNames)
    print("Comparison Completed.")


#TODO: accreptable_missing needs to eliminate acceptable missing files from dataframe
#TODO: Process dataframes into single dataframe
#TODO: Remove rows for files that should be missing






