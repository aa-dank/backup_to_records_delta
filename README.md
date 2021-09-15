# backup_to_records_delta
 Script that compares a mounted UCSC Construction file server to a mounted backup image to create spreadsheet of files in the backup that are not in their corresponding directory in the current server.<br/>
 Note that this script is "greedy" and is intended to error on the side of false positives, so expect many files in the resulting spreadsheet to be in both back up image and current state of the drive.<br/>
 The project has a development_files directory with files generated while building the main functions of the backup_to_records_delta and testing.<br/>
 There is also an environment.yml with the necessary libraries needed to run the script.<br/>
 Notable Functions:<br/>

 -  convert_backup_path(backUpPath, mainPath)<br/>
    -  This function takes a directory path from the backup image (backUpPath) and the path to the current file server to return the equivalent path of backUpPath on the current records server. This function is necessary because major directories on the file server were subtly renamed.
 -  file_df_discrepancies(targetDF, currentDF)
      -  This function takes two dataframes of files and their attributes and eliminates directories on the targetDF that are very similar to a file represented in the currentDF dataframe.
 -  build_file_dataframe(chosenDir, DF=None, ignoreThumbs=True)
      -  This function scrapes files and their attributes into a dataframe.<br/>
  <br/>
  Foremost on the wishlist for this script is to include a way to include a spreadsheet of files missing from current file server that are supposed to be missing. These would be eliminated from the resulting spreadsheet. There are some references to this feature in the code (acceptable_missing)





