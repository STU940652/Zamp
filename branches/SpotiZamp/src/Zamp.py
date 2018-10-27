#! /usr/local/bin/python3
# -*- coding: utf-8 -*-
#

# import standard libraries
import wx 
import sys
import os
import os.path
import queue
import subprocess
import datetime
import json
import license
import platform
import spotipy
import spotipy.oauth2
import traceback
from FileDragList import FileDragList
from PasswordDialog import PasswordDialog
from Credentials import Credentials
from Settings import *

# Make sure we are in the correct directory
application_path = ''
VERSION = ''
try:
    from version import VERSION
except:
    pass

if (getattr(sys, 'frozen', False)):
    application_path = os.path.dirname( os.path.abspath(sys.executable))
elif __file__:
    application_path = os.path.dirname( os.path.abspath(__file__))
if application_path:
    os.chdir( application_path)
    os.environ["PATH"] = application_path + ":" + os.environ["PATH"]

# Helper functions
def ms_to_hms (ms):
    try:
        h = int(ms/(60*60*1000))
        msl = ms - h*60*60*1000
        m = int(msl/(60*1000))
        msl = msl - m*60*1000
        s = msl/1000.0
        return "%02i:%02i:%06.3f" % (h,m,s)
    except:
        return ""
    
def hms_to_ms (s):
    d = s.split(':')
    mult = 1000.0
    ms = 0
    try:
        while len (d):
            ms = ms + float(d.pop(-1))*mult
            mult = mult * 60.0
        return int(ms)
    except:
        return 0
    

class ZampMain (wx.Frame):
    def __init__ (self, title):
        wx.Frame.__init__(self, None, -1, title,
                          pos=wx.DefaultPosition, size=(400,300))

        # Some variables
        self.delay_between_songs = datetime.timedelta(seconds=0)
        self.IsPlayingToEndTime = False
        self.DisableDuringPlayList = []
        self.TimerBlank = 0
        
        # Menu Bar
        #   File Menu
        self.frame_menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        # self.file_menu.Append(1, "&Load File", "Load file to playlist..")
        # self.file_menu.Append(2, "Load &Folder", "Load folder to playlist..")
        self.file_menu.Append(3, "Load &Playlist", "Load playlist from Spotify")
        #self.file_menu.AppendSeparator()
        #self.file_menu.Append(4, "&Save Playlist", "Save playlist to file")
        #self.file_menu.AppendSeparator()
        self.file_menu.Append(5, "&Clear Playlist", "Remove all files from playlist")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(6, "&Update Passwords", "Update user names and passwords")
        self.file_menu.Append(100, "&Close", "Quit")
        #self.Bind(wx.EVT_MENU, self.OnLoadFile, id=1)
        #self.Bind(wx.EVT_MENU, self.OnLoadFolder, id=2)
        self.Bind(wx.EVT_MENU, self.OnLoadPlaylist, id=3)
        #self.Bind(wx.EVT_MENU, self.OnSavePlaylist, id=4)
        self.Bind(wx.EVT_MENU, self.OnClearPlaylist, id=5)
        self.Bind(wx.EVT_MENU, self.OnUpdatePasswords, id=6)
        self.Bind(wx.EVT_MENU, self.OnExit, id=100)
        self.frame_menubar.Append(self.file_menu, "File")
        
        help_menu = wx.Menu()
        help_menu.Append(91,  "Help", "Show intro to Zamp")
        help_menu.Append(92, "About", "About Zamp")
        self.frame_menubar.Append(help_menu, "Help")
        self.Bind(wx.EVT_MENU, self.OnShowHelp, id=91)
        self.Bind(wx.EVT_MENU, self.OnShowAbout, id=92)        
        
        self.SetMenuBar(self.frame_menubar)

        # Status Bar
        self.StatusBar = self.CreateStatusBar(2)

        # finally create the timer, which updates the timeslider
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        ctrlpanel = wx.Panel(self, -1 )
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(wx.StaticText(ctrlpanel, label="Player"), 0, flag=wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, border=2)
        self.playerSelect = wx.ComboBox(ctrlpanel)
        sizer.Add(self.playerSelect, 0, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=2)
        
        sizer.Add(wx.StaticText(ctrlpanel, label="Play List"), 0, flag=wx.LEFT|wx.RIGHT|wx.TOP|wx.EXPAND, border=2)
        self.playlistSelect = wx.ComboBox(ctrlpanel)
        sizer.Add(self.playlistSelect, 0, flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, border=2)
        self.Bind(wx.EVT_COMBOBOX, self.OnLoadPlaylist, self.playlistSelect)
        
        self.MediaList = FileDragList(AfterChangeCB=self.UpdateTimes, parent=ctrlpanel, style=wx.LC_REPORT)
        self.MediaList.InsertColumn(0, "Name", width=200)
        self.MediaList.InsertColumn(1, "Duration", wx.LIST_FORMAT_RIGHT)
        self.MediaList.InsertColumn(2, "Start Time", wx.LIST_FORMAT_RIGHT)
        sizer.Add(self.MediaList, 1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick, self.MediaList)
        
        # Time Slider
        self.timeslider = wx.Slider(ctrlpanel, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        self.DisableDuringPlayList.append(self.timeslider)
        self.Bind(wx.EVT_SLIDER, self.OnSetTime, self.timeslider)
        self.timeText = wx.StaticText(ctrlpanel, size=(70, -1), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.timeToEndText = wx.StaticText(ctrlpanel, size=(70, -1), style=wx.ST_NO_AUTORESIZE)
        play   = wx.Button(ctrlpanel, label="Play To End")
        stop   = wx.Button(ctrlpanel, label="Stop")
        shuffle = wx.Button(ctrlpanel, label="Shuffle")

        # box1 contains the timeslider
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box1.Add(self.timeText)
        box1.Add(self.timeslider, 2)
        box1.Add(self.timeToEndText)
        sizer.Add(box1, flag=wx.EXPAND)
        # box2 contains some buttons
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(play, flag=wx.RIGHT, border=5)
        box2.Add(stop)
        box2.Add(shuffle)
        box2.Add((-1, -1), 1)
        sizer.Add(box2, flag=wx.EXPAND)
        
        self.Bind(wx.EVT_BUTTON, self.OnPlay, play)
        self.Bind(wx.EVT_BUTTON, self.OnStop, stop)
        self.Bind(wx.EVT_BUTTON, self.OnShuffle, shuffle)
        self.DisableDuringPlayList.append(play)
        self.DisableDuringPlayList.append(shuffle)
        
        # box3 is for the end time
        box3 = wx.BoxSizer( wx.HORIZONTAL)
        box3.Add(wx.StaticText(ctrlpanel, label="End Time"))
        self.EndTime = wx.TextCtrl( ctrlpanel, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEndTimeChange, self.EndTime)
        box3.Add( self.EndTime)
        sizer.Add( box3, flag=wx.EXPAND)
        self.DisableDuringPlayList.append(self.EndTime)
        
        # Pre-populate End Time
        about_a_half_hour_from_now = datetime.datetime.now().replace(second = 5) + \
                                     datetime.timedelta(minutes = ((30-datetime.datetime.now().minute%30) + 30))
        self.last_end_time = about_a_half_hour_from_now
        self.EndTime.SetValue(about_a_half_hour_from_now.strftime("%I:%M:%S %p"))

        ctrlpanel.SetSizer(sizer)
        self.SetMinSize( (300,400) )
        
        if (Credentials["Spotify_User_Token"]):
            self.InitSpotify()

    def InitSpotify (self):
        # Check token
        so = spotipy.oauth2.SpotifyOAuth(
                client_id=Credentials["Spotify_Client_Id"],
                client_secret=Credentials["Spotify_Client_Secret"],
                redirect_uri='',
                cache_path = os.path.join(ZampConfig.get('FilePaths', 'LogPath'), "auth-cache"))
                
        auth = so.get_cached_token()
        
        if not auth:
            return
    
        try:
            self.sp = spotipy.client.Spotify(auth=auth['access_token'])
            
            #
            # Player Selector
            #
            self.playerSelect.Clear()

            devices = self.sp._get("me/player/devices") # aka. sp.devices()
            for device in devices['devices']:
                if device['is_active']:
                    self.playerSelect.Append("%s - %s"%(device['name'], device['type']), device["id"])
            self.playerSelect.SetSelection(0)
            
            #
            # Playlist selector
            #
            self.playlistSelect.Clear()
            playlists = self.sp.current_user_playlists()
            for playlist in playlists['items']:
                self.playlistSelect.Append(playlist['name'], playlist)
            self.playlistSelect.SetSelection(0)
            
            # Load first playlist
            if self.playlistSelect.Count:
                self.OnLoadPlaylist()
        except:
            traceback.print_exc()

    def OnEndTimeChange (self, evt):
        # Clean up EndTime
        end_time = self.EndDateTime()
        self.EndTime.SetValue(end_time.strftime("%I:%M:%S %p"))
        
        self.UpdateTimes()
    
    def UpdateTimes (self, evt=None):
        end_time = self.EndDateTime()
        for i in range(self.MediaList.GetItemCount()-1, -1, -1):
            if (end_time > datetime.datetime.now()):
                end_time -= self.MediaList.GetItemCollectionData( i, "duration")
                self.MediaList.SetItemCollectionData( i, "start_time", end_time)
                self.MediaList.SetItem( i, 2, end_time.strftime("%I:%M:%S %p"))
                end_time -= self.delay_between_songs
            else:
                self.MediaList.SetItem( i, 2, "")
        
    def EndDateTime (self):
        # Get the time
        try:
            end_time = datetime.datetime.strptime(self.EndTime.GetValue(), "%I:%M:%S %p")
        except ValueError:
            end_time = self.last_end_time
            
        self.last_end_time = end_time
        
        # Calculate the date.  It must be in the future.  Start with today.
        now = datetime.datetime.now()
        end_time = end_time.replace(year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo) 
        
        # If it is in the past, change it to tomorrow
        if (end_time < now):
            end_time += datetime.timedelta(days = 1)
            
        return end_time
                
    def OnPlay(self, evt=None):
        self.StartNextSong()
        self.IsPlayingToEndTime = True
        self.timer.Start(milliseconds=100)
        
        #Disable stuff to make playing safe
        for w in self.DisableDuringPlayList:
            w.Disable()
        self.MediaList.DisableDragDrop()
        self.frame_menubar.EnableTop(0, False)

    def StartNextSong( self):
        # Clear item colors
        for i in range( self.MediaList.GetItemCount()):
            if self.MediaList.GetItemTextColour(i) != wx.TheColourDatabase.Find("BLACK"):
                self.MediaList.SetItemTextColour(i, wx.TheColourDatabase.Find("BLACK"))
    
        # First find the file to play
        uris = []
        this_duration = None
        start_at = None
        next_start_at = None
        for i in range(self.MediaList.GetItemCount()-1, -1, -1):
            if self.MediaList.GetItemCollectionData( i, "start_time") and (self.MediaList.GetItemCollectionData( i, "start_time") < datetime.datetime.now()):
                this_duration = self.MediaList.GetItemCollectionData( i, "duration")
                # Find the time to start at
                start_at = datetime.datetime.now() - self.MediaList.GetItemCollectionData( i, "start_time")
                if (start_at > this_duration):
                    break
                # Highlight the song playing
                self.MediaList.SetItemTextColour(i, wx.TheColourDatabase.Find("RED"))
                for j in range(i, self.MediaList.GetItemCount()):
                    uris.append(self.MediaList.GetItemCollectionData( j, "id"))
                break
            next_start_at = self.MediaList.GetItemCollectionData( i, "start_time")
            
        # Play
        if uris:
            data = {}
            data['uris'] = uris
            if (start_at > self.delay_between_songs):
                data['position_ms'] = int(start_at.total_seconds() * 1000)
            self.sp._put(self.sp._append_device_id("me/player/play", device_id=self._device_id()), payload=data)
                
            self.StatusBar.SetStatusText(self.MediaList.GetItemCollectionData( i, "filename"))
            self.TimerBlank = 2
            
        elif next_start_at:
            self.StatusBar.SetStatusText("Waiting...")     
            return (next_start_at - datetime.datetime.now())
            
        else:
            # Done playing
            self.OnStop()

    def OnStop(self, evt=None):
        """Stop the player.
        """
        self.IsPlayingToEndTime = False
        try:
            self.sp.pause_playback(device_id=self._device_id())
        except:
            traceback.print_exc()
        self.timer.Stop()
        self.StatusBar.SetStatusText("")
        self.timeslider.SetValue(0)
        self.timeText.SetLabel("")
        self.timeToEndText.SetLabel("")
        
        # Re-enable stuff
        for w in self.DisableDuringPlayList:
            w.Enable()
        self.MediaList.EnableDragDrop()
        self.frame_menubar.EnableTop(0, True)

        # Clear item colors
        for i in range( self.MediaList.GetItemCount()):
            if self.MediaList.GetItemTextColour(i) != wx.TheColourDatabase.Find("BLACK"):
                self.MediaList.SetItemTextColour(i, wx.TheColourDatabase.Find("BLACK"))
                
        # Update times in case we were "playing from here"
        if evt:
            self.UpdateTimes()
            
    def OnShuffle( self, evt):
        self.MediaList.ShuffleItems()
        self.UpdateTimes()
        
    def OnTimer(self, evt):
        """Update the time slider according to the current movie time.
        """
        # Check for blanking after starting to play
        if self.TimerBlank:
            self.TimerBlank -= 1
            return
        
        # See if we need to start the next song
        time_until_start = None
        
        player_info = self.sp._get("me/player") # device_id=self._device_id()
        if not player_info:
            return
        is_playing = player_info["is_playing"]
        
        if self.IsPlayingToEndTime and not player_info["is_playing"]:
            time_until_start = self.StartNextSong()
            
            if time_until_start:
                self.timeslider.SetValue(0)
                self.timeText.SetLabel("")
                self.timeToEndText.SetLabel(ms_to_hms(time_until_start.total_seconds() * 1000))
            
        elif player_info["is_playing"]:
            # re-set the timeslider to the correct range.
            length = player_info["item"]["duration_ms"]
            self.timeslider.SetRange(-1, length)
            
            # update the time on the slider
            CurrentTime = player_info["progress_ms"]
            self.timeslider.SetValue(CurrentTime)
            self.timeText.SetLabel(ms_to_hms(CurrentTime))     
            self.timeToEndText.SetLabel(ms_to_hms(length - CurrentTime))
        
        else:
            # We are done playing
            self.timeslider.SetValue(0)
            self.timeText.SetLabel("")
            self.timeToEndText.SetLabel("")
            self.OnStop()

    def OnSetTime(self, evt):
        """Set the time according to the time sider.
        """
        if self.IsPlayingToEndTime:
            return
        slideTime = self.timeslider.GetValue()
        self.sp.seek_track (slideTime, self._device_id())

    def OnLoadPlaylist( self, evt=None):
        self.OnClearPlaylist()
        #
        # Load playlists and tracks
        #
        def show_tracks(tracks):
            for item in tracks['items']:
                track = item['track']
                screen_name = "%s (%s)" % (track['name'], track['artists'][0]['name'])
                duration_ms = track['duration_ms']
                self.MediaList.AppendNewItem(screen_name, duration_ms, track)
                
        index = self.playlistSelect.GetSelection()
        playlist = self.playlistSelect.GetClientData(index)
        results = self.sp.user_playlist(user=playlist['owner']['id'],
            playlist_id=playlist['id'],
            fields="tracks,next")
        tracks = results['tracks']
        show_tracks(tracks)
        while tracks['next']:
            tracks = sp.next(tracks)
            show_tracks(tracks)  
            
    def OnClearPlaylist( self, evt=None):
        self.MediaList.DeleteAllItems()
        self.MediaList.ItemDataCollection = {}
        self.UpdateTimes()
    
    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()
        
    def OnRightClick(self, event):
        # No menu if playing
        if self.IsPlayingToEndTime:
            return
            
        self.ItemIndexRightClicked = event.GetIndex()
        
        self.menuItems = []     
        self.menuItems.append((wx.NewId(),'Play This'))
        self.menuItems.append((wx.NewId(),'Play From Here'))
        self.menuItems.append((wx.NewId(),'Delete'))
            
        menu = wx.Menu()
        for (id,nm) in self.menuItems:
            menu.Append(id,nm)
            menu.Bind(wx.EVT_MENU, self.OnRightMenuSelect, id=id)
            
        self.menuItems = dict(self.menuItems)
        self.PopupMenu (menu, event.GetPoint())
        menu.Destroy

    def _device_id(self):
        return self.playerSelect.GetClientData(self.playerSelect.GetSelection())
        
    def OnRightMenuSelect(self, event):
        """
        Handle a right-click event.
        """
        if (self.menuItems[event.GetId()] == 'Play This'):
            self.sp.start_playback( device_id=self._device_id(), 
                uris=[self.MediaList.GetItemCollectionData( self.ItemIndexRightClicked, "id")])
                
            self.StatusBar.SetStatusText(self.MediaList.GetItemCollectionData( self.ItemIndexRightClicked, "filename"))
            self.timer.Start(milliseconds=100)              

        if (self.menuItems[event.GetId()] == 'Play From Here'):
            self.OnStop()
            # Set the start times with this song starting now
            start_time = datetime.datetime.now()
            for i in range(self.MediaList.GetItemCount()):
                if (i >= self.ItemIndexRightClicked):
                    self.MediaList.SetItemCollectionData( i, "start_time", start_time)
                    self.MediaList.SetItem( i, 2, start_time.strftime("%I:%M:%S %p"))
                    start_time += self.MediaList.GetItemCollectionData( i, "duration")
                    start_time += self.delay_between_songs
                else:
                    self.MediaList.SetItemCollectionData( i, "start_time", None)
                    self.MediaList.SetItem( i, 2, "")
            self.OnPlay()
            
                
        if (self.menuItems[event.GetId()] == 'Delete'):
            # Delete this item.
            self.MediaList.DeleteItem(self.ItemIndexRightClicked)
            self.UpdateTimes()
        
    def OnUpdatePasswords (self, evt):
        p = PasswordDialog()
        p.ShowModal()
        p.Destroy()
        self.InitSpotify()
        
    def OnShowAbout(self, event):
        m = wx.Dialog( self, title="About...")
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(m.CreateTextSizer("""ZAMP %s
Zamp is Another Media Player

Visit us at zamp.sourceforge.net

This program is released under the GNU Public License v2.0.  
It is released without without any warranty, expressed or 
implied, including any warranty as to merchantability.  
""" % VERSION), flag=wx.ALIGN_CENTER|wx.ALL, border=10)
        s.Add(wx.TextCtrl(m, value=license.GPL, style=wx.TE_MULTILINE, size=(450,100)), flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
        s.Add(wx.StaticText(m, label="VLClib is released under LGPL"), flag=wx.LEFT|wx.TOP, border=10)
        s.Add(wx.TextCtrl(m, value=license.LGPL, style=wx.TE_MULTILINE, size=(450,100)), flag=wx.LEFT|wx.RIGHT|wx.EXPAND, border=10)
        s.Add(m.CreateButtonSizer( wx.OK), flag=wx.ALIGN_CENTER)
        m.SetSizer(s)
        m.Fit()
        m.Show()

    def OnShowHelp(self, event):
        m = wx.Dialog( self, title="Help", style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(wx.TextCtrl(m, value = """ZAMP
Zamp is Another Media Player

Visit us at zamp.sourceforge.net

The point of this program is to play a list of music, and have the last song end at a specific time.  The "music" can be any file that can be played by VLC, including video.

PREREQUISITES
Zamp uses VLC media player.  It must also be installed prior to use.  You can get it at www.VideoLAN.org. You must have the same bitness for VLC and Zamp, e.g. for 64-bit Zamp you need 64-bit VLC (the default download for VLC is 32-bit).

STUFF YOU SHOULD KNOW
At the moment, you can't add any files with a length of less than 10 seconds.  VLC will happily let you add still images (e.g. JPEGs) to a playlist, which it will show for 10 seconds as a slide show.  So for right now Zamp ignores any files with a time less than 10 seconds.

SELECTING MEDIA
You can drag and drop media files and folders to the playlist window.  You can also add files and folders from the File menu.

Playlists can be loaded and saved from the File menu.  When you load a playlist, the existing media is not cleared first.

You can change the playlist order by dragging and dropping.

REMOVING MEDIA
Right-click and select "Delete" to remove a media.

Select "Clear Playlist" from the File menu to remove all media.

SET THE END TIME
Time is in the format HH:MM:SS pm.  You have to hit Enter for it to take effect.  At program start, the end time defaults to about a half hour in the future, at a 30 minute interval plus 5 seconds (because most songs have a few seconds of fade out).

PLAYING
When you click "Play To End", the media will begin playing at whatever song and time that will result in the last song ending at the "Time To End".  Note that there is a 2 second delay between songs.  When playing to end, all of the controls (e.g. adding files, scrubbing) are disabled.

You can also right-click on a song and select "Play This".  You can then use the scrubber to change the time to preview the song.  Play will stop at the end of the song.

Right-click on a song and select "Play From Here" to start that song at the beginning and play to the end of the lise.
""", style=wx.TE_MULTILINE|wx.TE_AUTO_URL|wx.TE_RICH), flag=wx.ALIGN_CENTER|wx.EXPAND, proportion=1)
        s.Add(m.CreateButtonSizer( wx.OK), flag=wx.ALIGN_CENTER)
        m.SetSizer(s)
        m.Show()
		
if __name__ == "__main__":
    # Create a wx.App(), which handles the windowing system event loop
    app = wx.App(redirect=False)
    # Create the window containing our small media player
    player = ZampMain("Zamp")
    # show the player window centred and run the application
    player.Show()
    app.MainLoop()