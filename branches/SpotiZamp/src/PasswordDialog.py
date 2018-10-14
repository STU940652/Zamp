import wx
import pickle
import codecs
from Settings import *
import traceback
import time
from Credentials import Credentials
import urllib.parse
import io
import spotipy
import spotipy.util
import spotipy.oauth2

# Selenium for Spotify
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions


def SaveCredentials ():
    global Credentials
    
    with open(os.path.join(ZampConfig.get('FilePaths', 'LogPath'),'Zamp.pwl'), "wb") as f:
        f.write(codecs.encode(pickle.dumps(Credentials), "base64"))
    
class PasswordDialog(wx.Dialog):
    def __init__ (self):
        wx.Dialog.__init__(self, None, title="Update Passwords", style=wx.DEFAULT_DIALOG_STYLE)
        
        Sizer=wx.BoxSizer(wx.VERTICAL)
                
        # Spotify
        Sizer.Add(wx.StaticText(self, -1, "Spotify Client ID"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Spotify_Client_Id = wx.TextCtrl(self, value=Credentials["Spotify_Client_Id"])
        Sizer.Add(self.Spotify_Client_Id, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "Spotify Client Secret"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        self.Spotify_Client_Secret = wx.TextCtrl(self, style=wx.TE_PASSWORD, value=Credentials["Spotify_Client_Secret"])
        Sizer.Add(self.Spotify_Client_Secret, 0, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)

        Sizer.Add(wx.StaticText(self, -1, "Spotify User Token"), 0, flag=wx.TOP|wx.LEFT, border = 10)
        
        rowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Spotify_User_Token = wx.TextCtrl(self, value=Credentials["Spotify_User_Token"])
        rowSizer.Add(self.Spotify_User_Token, 1, flag=wx.EXPAND|wx.BOTTOM|wx.LEFT|wx.RIGHT, border = 10)
        self.SpotifyAuthenticate = wx.Button (self, -1, "Authenticate")
        rowSizer.Add(self.SpotifyAuthenticate, 0)
        self.Bind(wx.EVT_BUTTON, self.OnSpotifyAuthenticate, self.SpotifyAuthenticate)        
        Sizer.Add(rowSizer, flag=wx.EXPAND)

        Sizer.Add(wx.StaticLine(self), 0, flag=wx.EXPAND)
        
        #Buttons
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer()
        self.OK = wx.Button (self, -1, "OK")
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.OK)
        buttonSizer.Add(self.OK, 0)
        self.CANCEL = wx.Button (self, -1, "Cancel")
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.CANCEL)
        buttonSizer.Add(self.CANCEL, 0)
        
        Sizer.Add(buttonSizer, 0, flag=wx.EXPAND)
        
        Sizer.Fit(self)
        self.SetSizer(Sizer)
        
    def OnOK (self, evt):
        global Credentials
        Credentials["Spotify_Client_Id"] = self.Spotify_Client_Id.GetValue()
        Credentials["Spotify_Client_Secret"] = self.Spotify_Client_Secret.GetValue()
        Credentials["Spotify_User_Token"] = self.Spotify_User_Token.GetValue()
        
        SaveCredentials()
        self.Close()
        
    def OnCancel (self, evt):
        self.Close()
        
    def OnSpotifyAuthenticate (self, evt):
        end_url = "http://localhost/AuthEnd/"
        try:
        
            sp_oauth = spotipy.oauth2.SpotifyOAuth(
                Credentials["Spotify_Client_Id"], 
                Credentials["Spotify_Client_Secret"], 
                end_url, scope='user-library-read')
                
            Spotify_authorization_url = sp_oauth.get_authorize_url()
             
            #spotipy.util.prompt_for_user_token(
            #    username="andyndeanna@gmail.com",
            #    scope='user-library-read',
            #    client_id=Credentials["Spotify_Client_Id"],
            #    client_secret=Credentials["Spotify_Client_Secret"],
            #    redirect_uri=end_url)
            #    
            code_from_url = ""

            # Your application should now redirect to Spotify_authorization_url.
            # options = webdriver.ChromeOptions()
            # options.add_argument("--user-data-dir=/home/username/.config/google-chrome")
            browser = webdriver.Chrome()
            # Visit URL
            browser.get(Spotify_authorization_url)
            
            # Wait until URL = end_url
            still_going = True
            while still_going:
                time.sleep(0.5)
                if end_url.split(":", 1)[-1] in browser.current_url:
                    authorized_url = browser.current_url
                    browser.quit()
                    still_going = False 

            authorized_params = urllib.parse.parse_qs(urllib.parse.urlparse(authorized_url).query)
            print (authorized_params)
            if 'code' in authorized_params:
                code_from_url = authorized_params['code']
                print (code_from_url)

            """This section completes the authentication for the user."""
            # You should retrieve the "code" from the URL string Spotify redirected to.  Here that's named CODE_FROM_URL
            try:
                token, user, scope = v.exchange_code(code_from_url, end_url)
                #print(token, user, scope)
                self.Spotify_User_Token.SetValue(token)
                
            except Spotify.auth.GrantFailed:
                m = wx.MessageDialog(self, traceback.format_exc(), "Spotify Authentication Error", wx.OK)
                m.ShowModal()

        except:
            m = wx.MessageDialog(self, traceback.format_exc(), "Spotify Authentication Error", wx.OK)
            m.ShowModal()
