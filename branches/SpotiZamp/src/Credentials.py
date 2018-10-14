import os.path
from Settings import *
import traceback
import pickle
import codecs

Credentials = {}
Credentials["Spotify_Client_Id"] = ""
Credentials["Spotify_Client_Secret"] = ""
Credentials["Spotify_User_Token"] = ""

# LoadCredentials ():
try:
    with open(os.path.join(ZampConfig.get('FilePaths', 'LogPath'),'Zamp.pwl'), "rb") as f:
        newCredentials = pickle.loads(codecs.decode(f.read(), "base64"))
        Credentials.update(newCredentials)
    
except:
    print (traceback.format_exc())

