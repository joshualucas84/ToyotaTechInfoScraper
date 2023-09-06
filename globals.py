
import yaml
from pathlib import Path


def setRootUrl(str):
    global rootUrl
    rootUrl = str

def setRootDir(str):
    global rootDir
    rootDir = str

def setTitleForDir(str):
    global titleForDir
    titleForDir = str

def setDirectory(str):
    global directory
    directory = str

def setDefaultDownloadDir(str):
    global defaultDownloadDir
    defaultDownloadDir = str

def setUsername(str):
    global username
    username = str

def setPassword(str):
    global password
    password = str
def getRootUrl():
    return rootUrl
def getRootDir():
    return rootDir

def getDefaultDownloadDir():
    return defaultDownloadDir

def getTitleForDir():
    try: titleForDir
    except NameError:
       setTitleForDir("")
       return titleForDir
    if (len(titleForDir) > 0):
       return titleForDir
    else:
        return titleForDir

def getFullRootDirectory():
    return rootDir + getTitleForDir()
def getDirectory():
    return directory

def getUsername():
    return username
def getPassword():
    return password

def getSettings():
    full_file_path = Path(__file__).parent.joinpath('settings.yaml')
    with open(full_file_path) as settings:
        settings_data = yaml.load(settings, Loader=yaml.Loader)
    return settings_data


