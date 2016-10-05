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
from FileDragList import FileDragList
try:
    import vlc
    HAVE_VLC = True
except:
    HAVE_VLC = False

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
        # See if VLC loaded
        if not HAVE_VLC:
            m = wx.MessageDialog(self, message = "Please download and install VLC Media Player\nfrom www.VideoLAN.org.", 
                                caption = "Could not find VLC Media Player.",
                                style = wx.ICON_ERROR|wx.OK)
            m.ShowModal()
        
        # Some variables
        self.delay_between_songs = datetime.timedelta(seconds=2)
        self.IsPlayingToEndTime = False
        
        # Menu Bar
        #   File Menu
        self.frame_menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.file_menu.Append(1, "&Load File", "Load file to playlist..")
        self.file_menu.Append(2, "Load &Folder", "Load folder to playlist..")
        self.file_menu.Append(3, "Load &Playlist", "Load playlist from file")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(4, "&Save Playlist", "Save playlist to file")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(5, "&Clear Playlist", "Remove all files from playlist")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(6, "&Close", "Quit")
        self.Bind(wx.EVT_MENU, self.OnLoadFile, id=1)
        self.Bind(wx.EVT_MENU, self.OnLoadFolder, id=2)
        self.Bind(wx.EVT_MENU, self.OnLoadPlaylist, id=3)
        self.Bind(wx.EVT_MENU, self.OnSavePlaylist, id=4)
        self.Bind(wx.EVT_MENU, self.OnClearPlaylist, id=5)
        self.Bind(wx.EVT_MENU, self.OnExit, id=6)
        self.frame_menubar.Append(self.file_menu, "File")
        self.SetMenuBar(self.frame_menubar)
        
        # Status Bar
        self.StatusBar = self.CreateStatusBar(2)

        # finally create the timer, which updates the timeslider
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        # VLC player controls
        if HAVE_VLC:
            self.Instance = vlc.Instance()
            self.player = self.Instance.media_player_new()  

        ctrlpanel = wx.Panel(self, -1 )
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.MediaList = FileDragList(AfterChange=self.UpdateTimes, parent=ctrlpanel, style=wx.LC_REPORT)
        self.MediaList.InsertColumn(0, "Name", width=200)
        self.MediaList.InsertColumn(1, "Duration", wx.LIST_FORMAT_RIGHT)
        self.MediaList.InsertColumn(2, "Start Time", wx.LIST_FORMAT_RIGHT)
        sizer.Add(self.MediaList, 1, flag=wx.EXPAND)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick, self.MediaList)

        # Time Slider
        self.timeslider = wx.Slider(ctrlpanel, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        self.Bind(wx.EVT_SLIDER, self.OnSetTime, self.timeslider)
        self.timeText = wx.StaticText(ctrlpanel, size=(70, -1), style=wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE)
        self.timeToEndText = wx.StaticText(ctrlpanel, size=(70, -1), style=wx.ST_NO_AUTORESIZE)
        play   = wx.Button(ctrlpanel, label="Play To End")
        stop   = wx.Button(ctrlpanel, label="Stop")
        shuffle = wx.Button(ctrlpanel, label="Shuffle")
        self.volslider = wx.Slider(ctrlpanel, -1, 100, 0, 200, size=(100, -1))
        self.Bind(wx.EVT_SLIDER, self.OnSetVolume, self.volslider)

        # box1 contains the timeslider
        box1 = wx.BoxSizer(wx.HORIZONTAL)
        box1.Add(self.timeText)
        box1.Add(self.timeslider, 2)
        box1.Add(self.timeToEndText)
        sizer.Add(box1, flag=wx.EXPAND)
        # box2 contains some buttons and the volume controls
        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(play, flag=wx.RIGHT, border=5)
        box2.Add(stop)
        box2.Add(shuffle)
        box2.Add((-1, -1), 1)
        box2.Add(wx.StaticText(ctrlpanel, label="Volume", style=wx.ALIGN_RIGHT))
        sizer.Add(box2, flag=wx.EXPAND)
        box2.Add(self.volslider, flag=wx.TOP | wx.LEFT, border=5)
        
        self.Bind(wx.EVT_BUTTON, self.OnPlay, play)
        self.Bind(wx.EVT_BUTTON, self.OnStop, stop)
        self.Bind(wx.EVT_BUTTON, self.OnShuffle, shuffle)
        
        # box3 is for the end time
        box3 = wx.BoxSizer( wx.HORIZONTAL)
        box3.Add(wx.StaticText(ctrlpanel, label="End Time"))
        self.EndTime = wx.TextCtrl( ctrlpanel, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEndTimeChange, self.EndTime)
        box3.Add( self.EndTime)
        sizer.Add( box3, flag=wx.EXPAND)
        
        # Pre-populate End Time
        about_a_half_hour_from_now = datetime.datetime.now().replace(second = 5) + \
                                     datetime.timedelta(minutes = ((30-datetime.datetime.now().minute%30) + 30))
        self.last_end_time = about_a_half_hour_from_now
        self.EndTime.SetValue(about_a_half_hour_from_now.strftime("%I:%M:%S %p"))

        ctrlpanel.SetSizer(sizer)
        self.SetMinSize( (300,200) )
        
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
        
    def OnLoadFile(self, evt):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        dlg = wx.FileDialog(self, "Choose files to add", 
                            wildcard="*.*",  
                            style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            # Add to list
            self.MediaList.InsertItems(items=dlg.GetPaths())

        # finally destroy the dialog
        dlg.Destroy()
        
    def OnLoadFolder(self, evt):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        dlg = wx.DirDialog(self, "Choose folder to add",  
                            style=wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            # Add to list
            file_list = []
            for dirpath, dirnames, filenames in os.walk(dlg.GetPath()):
                file_list.extend([os.path.join(dirpath, f) for f in filenames])
            self.MediaList.InsertItems(items=file_list)

        # finally destroy the dialog
        dlg.Destroy()
        
    def OnPlay(self, evt=None):
        """Toggle the status to Play/Pause.

        If no file is loaded, open the dialog window.
        """
        self.StartNextSong()
        self.IsPlayingToEndTime = True
        self.timer.Start(milliseconds=100)
        self.OnSetVolume()

    def StartNextSong( self):
        # Clear item colors
        for i in range( self.MediaList.GetItemCount()):
            if self.MediaList.GetItemTextColour(i) != wx.TheColourDatabase.Find("BLACK"):
                self.MediaList.SetItemTextColour(i, wx.TheColourDatabase.Find("BLACK"))
    
        # First find the file to play
        this_media = None
        this_duration = None
        start_at = None
        next_start_at = None
        for i in range(self.MediaList.GetItemCount()-1, -1, -1):
            if (self.MediaList.GetItemCollectionData( i, "start_time") < datetime.datetime.now()):
                this_media = self.MediaList.GetItemCollectionData( i, "media")
                this_duration = self.MediaList.GetItemCollectionData( i, "duration")
                # Find the time to start at
                start_at = datetime.datetime.now() - self.MediaList.GetItemCollectionData( i, "start_time")
                # Highlight the song playing
                self.MediaList.SetItemTextColour(i, wx.TheColourDatabase.Find("RED"))  
        
                break
            next_start_at = self.MediaList.GetItemCollectionData( i, "start_time")
            
        if this_media and (start_at > this_duration):
            this_media = None
        
        # Play
        if this_media:
            self.player.stop()
            self.player.set_media(this_media)
            if self.player.play() == -1:
                print("Unable to play.")
                return

            # And set time
            if self.player.set_time(int(start_at.total_seconds() * 1000)) == -1:
            #if self.player.set_time(int(1)) == -1:
                print("Failed to set time")
                return
                
            title = self.player.get_title()
            #  if an error was encountred while retriving the title, then use
            #  filename
            if title == -1:
                title = os.path.basename(self.MediaList.GetItemCollectionData( i, "filename"))
            self.StatusBar.SetStatusText(self.MediaList.GetItemCollectionData( i, "media").get_meta(vlc.Meta.Title))
            
        else:
            self.StatusBar.SetStatusText("Waiting...")     
            return (next_start_at - datetime.datetime.now())

    def OnStop(self, evt=None):
        """Stop the player.
        """
        self.IsPlayingToEndTime = False
        self.player.stop()
        self.timer.Stop()
        self.StatusBar.SetStatusText("")
        self.timeslider.SetValue(0)
        self.timeText.SetLabel("")
        self.timeToEndText.SetLabel("")

    def OnShuffle( self, evt):
        self.MediaList.ShuffleItems()
        
    def OnTimer(self, evt):
        """Update the time slider according to the current movie time.
        """
        # See if we need to start the next song
        time_until_start = None
        if self.IsPlayingToEndTime and not self.player.is_playing():
            time_until_start = self.StartNextSong()
        
        if self.player.is_playing():
            # since the self.player.get_length can change while playing,
            # re-set the timeslider to the correct range.
            length = self.player.get_length()
            self.timeslider.SetRange(-1, length)
            
            # update the time on the slider
            CurrentTime = self.player.get_time()
            self.timeslider.SetValue(CurrentTime)
            self.timeText.SetLabel(ms_to_hms(CurrentTime))     
            self.timeToEndText.SetLabel(ms_to_hms(length - CurrentTime))
        
        elif time_until_start:
            self.timeslider.SetValue(0)
            self.timeText.SetLabel("")
            self.timeToEndText.SetLabel(ms_to_hms(time_until_start.total_seconds() * 1000))
            
        else:
            # We are done playing
            self.timeslider.SetValue(0)
            self.timeText.SetLabel("")
            self.timeToEndText.SetLabel("")
            self.OnStop()

    def OnSetTime(self, evt):
        """Set the volume according to the volume sider.
        """
        if self.IsPlayingToEndTime:
            return
        slideTime = self.timeslider.GetValue()
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.set_time(slideTime) == -1:
            print("Failed to set time")

    def OnSetVolume(self, evt=None):
        """Set the volume according to the volume sider.
        """
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.audio_set_volume(self.volslider.GetValue()) == -1:
            print("Failed to set volume")

    def OnLoadPlaylist( self, evt):
        dlg = wx.FileDialog(self, "Load Playlist", 
                            wildcard="ZAMP Playlist (*.zamp)|*.zamp",  
                            style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            # Add to list
            with open( dlg.GetPath(), "rt") as f:
                d = json.load(f)
                self.MediaList.InsertItems(items=d["media_paths"])

        # finally destroy the dialog
        dlg.Destroy()
        
    def OnSavePlaylist( self, evt):
        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        dlg = wx.FileDialog(self, "Save Playlist", 
                            wildcard="ZAMP Playlist (*.zamp)|*.zamp",  
                            style=wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            # Roll up the media file paths
            l = []
            for i in range( self.MediaList.GetItemCount()):
                l.append(self.MediaList.GetItemCollectionData( i, "filename"))
                with open( dlg.GetPath(), "wt") as f:
                    json.dump({"media_paths" : l}, f)            

        # finally destroy the dialog
        dlg.Destroy()
        
    def OnClearPlaylist( self, evt):
        self.MediaList.DeleteAllItems()
        self.MediaList.ItemDataCollection = {}
    
    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()
        
    def OnRightClick(self, event):
        self.ItemIndexRightClicked = event.GetIndex()
        
        self.menuItems = []     
        self.menuItems.append((wx.NewId(),'Play This'))
        #self.menuItems.append((wx.NewId(),'Play From Here'))
        self.menuItems.append((wx.NewId(),'Delete'))
            
        menu = wx.Menu()
        for (id,nm) in self.menuItems:
            menu.Append(id,nm)
            menu.Bind(wx.EVT_MENU, self.OnRightMenuSelect, id=id)
            
        self.menuItems = dict(self.menuItems)
        self.PopupMenu (menu, event.GetPoint())
        menu.Destroy

    def OnRightMenuSelect(self, event):
        """
        Handle a right-click event.
        """
        if (self.menuItems[event.GetId()] == 'Play This'):
            self.OnStop()
            self.player.set_media(self.MediaList.GetItemCollectionData( self.ItemIndexRightClicked, "media"))
            if self.player.play() == -1:
                print("Unable to play.")
                return
            title = self.player.get_title()
            if title == -1:
                title = os.path.basename(self.MediaList.GetItemCollectionData( self.ItemIndexRightClicked, "filename"))
            self.StatusBar.SetStatusText(self.MediaList.GetItemCollectionData( self.ItemIndexRightClicked, "media").get_meta(vlc.Meta.Title))
            self.timer.Start(milliseconds=100)              
                
        if (self.menuItems[event.GetId()] == 'Delete'):
            # Delete this item.  First, delete the data
            del self.MediaList.ItemDataCollection[self.MediaList.GetItemData(self.ItemIndexRightClicked)]
            self.MediaList.DeleteItem(self.ItemIndexRightClicked)
		
if __name__ == "__main__":
    # Create a wx.App(), which handles the windowing system event loop
    app = wx.App(redirect=False)
    # Create the window containing our small media player
    player = ZampMain("Zamp" + VERSION)
    # show the player window centred and run the application
    player.Show()
    app.MainLoop()
