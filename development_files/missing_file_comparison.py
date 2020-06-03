import os, csv
import pandas as pd
from datetime import datetime
from pprint import pprint

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
    if DF != None:
        fileDF = DF.append(fileDF)
        fileDF.drop_duplicates(subset="Filepath", keep='first', inplace=True)
    return fileDF

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



if __name__ == '__main__':
    targetDir = ''
    otherDir = ''
    csvFile = "missing_files.csv"

    while not os.path.isdir(targetDir):
        targetDir = input("Enter path to backup directory: ")
        if targetDir == 'td':
            targetDir = r'F:\29xx   University House - Copy'
            otherDir =  r'F:\29xx   University House'

    while not os.path.isdir(otherDir):
        otherDir = input("Enter path to directory that might be missing files: ")

    csvPrompt = "Use %s as list of issues?" % csvFile

    if not user_chooses_yes(csvPrompt):
        csvFile = user_csv_choice()
    csvPath = os.path.join(os.getcwd(), csvFile)

    if not os.path.isfile(csvPath):
        blankCSVdf = pd.DataFrame(columns=["Filepath", "File", "Name", "Extension", "Filesize", "Created", "Modified", "Retrieved", "Error"])
        blankCSVdf.to_csv(csvPath, index=False, quoting=csv.QUOTE_NONNUMERIC)

    targetDF = build_file_dataframe(targetDir)
    otherDF = build_file_dataframe(otherDir)

    deltaDF = file_df_discrepancies(targetDF, otherDF)

    legacyDF = pd.read_csv(csvPath)
    legacyDF = legacyDF.append(deltaDF)
    legacyDF.drop_duplicates(subset=["Name", "Extension", "Modified"], keep='first', inplace=True)
    legacyDF.to_csv(csvPath, index=False, quoting=csv.QUOTE_NONNUMERIC)
    print("Issues saved to following file: " + csvFile)
