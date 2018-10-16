import configparser
import os
import datetime

# #Sample ini file
# [FilePaths]
# LogPath = r"C:\CustomLogPath"

ZampConfig=configparser.SafeConfigParser()

# Put in some default values
ZampConfig.add_section('FilePaths')

if "APPDATA" in os.environ:
    # For Windows
    ZampConfig.set('FilePaths', 'LogPath', os.path.realpath(os.path.join(os.environ["APPDATA"], "Zamp")))
elif "HOME" in os.environ:
    # For *nix (untested)
    ZampConfig.set('FilePaths', 'LogPath', os.path.realpath(os.path.join(os.environ["HOME"], ".Zamp")))
else:
    ZampConfig.set('FilePaths', 'LogPath', os.path.realpath(os.path.join('.', ".Zamp")))

# And read from the ini file
try:
    ZampConfig.read(['Zamp.ini', os.path.join(ZampConfig.get('FilePaths', 'LogPath'),'Zamp.ini')])
except:
    pass
    
if not os.path.isdir(ZampConfig.get('FilePaths', 'LogPath')):
    os.makedirs(ZampConfig.get('FilePaths', 'LogPath'))

