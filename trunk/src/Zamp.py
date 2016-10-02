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
import vlc
import datetime
from FileDragList import FileDragList

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
        self.delay_between_songs = datetime.timedelta(seconds=2)
        self.IsPlayingToEndTime = False
        
        # Menu Bar
        #   File Menu
        self.frame_menubar = wx.MenuBar()
        self.file_menu = wx.Menu()
        self.file_menu.Append(1, "&Open", "Open from file..")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(2, "&View Logs", "View Log File Directory")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(3, "&Update Passwords", "Update user names and passwords")
        self.file_menu.AppendSeparator()
        self.file_menu.Append(4, "&Close", "Quit")
        #self.Bind(wx.EVT_MENU, self.OnOpen, id=1)
        #self.Bind(wx.EVT_MENU, self.OnViewLogDir, id=2)
        #self.Bind(wx.EVT_MENU, self.OnUpdatePasswords, id=3)
        self.Bind(wx.EVT_MENU, self.OnExit, id=4)
        self.frame_menubar.Append(self.file_menu, "File")
        self.SetMenuBar(self.frame_menubar)
        
        # Status Bar
        self.StatusBar = self.CreateStatusBar(2)

        # finally create the timer, which updates the timeslider
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        # VLC player controls
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()  

        ctrlpanel = wx.Panel(self, -1 )
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.MediaList = FileDragList(AfterChange=self.UpdateTimes, parent=ctrlpanel, style=wx.LC_REPORT)
        self.MediaList.InsertColumn(0, "Name", width=200)
        self.MediaList.InsertColumn(1, "Duration", wx.LIST_FORMAT_RIGHT)
        self.MediaList.InsertColumn(2, "Start Time", wx.LIST_FORMAT_RIGHT)
        sizer.Add(self.MediaList, 1, flag=wx.EXPAND)
        #self.Bind(wx.EVT_LIST_INSERT_ITEM, self.UpdateTimes, self.MediaList)
        #self.Bind(wx.EVT_LIST_DELETE_ITEM, self.UpdateTimes, self.MediaList)

        # Time Slider
        self.timeslider = wx.Slider(ctrlpanel, -1, 0, 0, 1000)
        self.timeslider.SetRange(0, 1000)
        self.timeText = wx.StaticText(ctrlpanel, size=(100, -1))
        self.timeToEndText = wx.StaticText(ctrlpanel, size=(100, -1))
        play   = wx.Button(ctrlpanel, label="Play")
        stop   = wx.Button(ctrlpanel, label="Stop")
        volume = wx.Button(ctrlpanel, label="Volume")
        self.volslider = wx.Slider(ctrlpanel, -1, 0, 0, 100, size=(100, -1))

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
        box2.Add((-1, -1), 1)
        box2.Add(volume)
        sizer.Add(box2, flag=wx.EXPAND)
        box2.Add(self.volslider, flag=wx.TOP | wx.LEFT, border=5)
        
        self.Bind(wx.EVT_BUTTON, self.OnPlay, play)
        self.Bind(wx.EVT_BUTTON, self.OnStop, stop)
        
        # box3 is for the end time
        box3 = wx.BoxSizer( wx.HORIZONTAL)
        box3.Add(wx.StaticText(ctrlpanel, label="End Time"))
        self.EndTime = wx.TextCtrl( ctrlpanel, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEndTimeChange, self.EndTime)
        box3.Add( self.EndTime)
        sizer.Add( box3, flag=wx.EXPAND)
        
        # Pre-populate End Time
        about_a_half_hour_from_now = datetime.datetime.now().replace(second = 5) + datetime.timedelta(minutes = 30)
        about_a_half_hour_from_now = about_a_half_hour_from_now.replace( minute = round(about_a_half_hour_from_now.minute/30.0) * 30)
        self.last_end_time = about_a_half_hour_from_now.strftime("%I:%M:%S %p")
        self.EndTime.SetValue(self.last_end_time)

        ctrlpanel.SetSizer(sizer)
        self.SetMinSize( (300,200) )
        
    def OnEndTimeChange (self, evt):
        # Clean up EndTime
        end_time = self.EndDateTime()
        self.EndTime.SetValue(end_time.strftime("%I:%M:%S %p"))
        
        #self.EndTime.SetValue(self.last_end_time)
        
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
        end_time = datetime.datetime.strptime(self.EndTime.GetValue(), "%I:%M:%S %p")
        
        # Calculate the date.  It must be in the future.  Start with today.
        now = datetime.datetime.now()
        end_time = end_time.replace(year=now.year, month=now.month, day=now.day, tzinfo=now.tzinfo) 
        
        # If it is in the past, change it to tomorrow
        if (end_time < now):
            end_time += datetime.timedelta(days = 1)
            
        return end_time
        
    def OpenFile (self, MediaFileName, Play = True):
        # if a file is already running, then stop it.
        self.OnStop(None)

        self.MediaFileName=MediaFileName
        self.Media = self.Instance.media_new(str(self.MediaFileName))
        self.player.set_media(self.Media)
        # Report the title of the file chosen
        title = self.player.get_title()
        #  if an error was encountred while retriving the title, then use
        #  filename
        if title == -1:
            title = os.path.basename(MediaFileName)
        self.StatusBar.SetStatusText("%s - wxVLCplayer" % title)

        # set the window id where to render VLC's video output
        #if platform.system() == 'Windows':
        #    self.player.set_hwnd(self.videopanel.GetHandle())
        #elif platform.system() == 'Darwin':
        #    self.player.set_nsobject(self.videopanel.GetHandle())
        #else:
        #    self.player.set_xwindow(self.videopanel.GetHandle())

        if Play:
            self.OnPlay(None)

        # set the volume slider to the current volume
        #self.player.audio_set_volume(0)
        self.volslider.SetValue(self.player.audio_get_volume() / 2)
    
    def OnOpen(self, evt):
        """Pop up a new dialow window to choose a file, then play the selected file.
        """
        # if a file is already running, then stop it.
        self.OnStop(None)

        # Create a file dialog opened in the current home directory, where
        # you can display all kind of files, having as title "Choose a file".
        dlg = wx.FileDialog(self, "Choose a file", os.path.expanduser('~'), "",
                            "*.*", wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            dirname = dlg.GetDirectory()
            filename = dlg.GetFilename()
            # Creation
            self.OpenFile(os.path.join(dirname, filename))

        # finally destroy the dialog
        dlg.Destroy()
        
    def OnPlay(self, evt=None):
        """Toggle the status to Play/Pause.

        If no file is loaded, open the dialog window.
        """
        self.StartNextSong()
        self.IsPlayingToEndTime = True
        self.timer.Start(milliseconds=100)
        self.player.audio_set_volume(100)

    def StartNextSong( self):
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
                break
            next_start_at = self.MediaList.GetItemCollectionData( i, "start_time")
            
        if this_media and (start_at > this_duration):
            this_media = None
        
        # Play
        if this_media:
            self.player.stop()
            self.player.set_media(this_media)
            if self.player.play() == -1:
                self.errorDialog("Unable to play.")
                return

            # And set time
            if self.player.set_time(int(start_at.total_seconds() * 1000)) == -1:
            #if self.player.set_time(int(1)) == -1:
                self.errorDialog("Failed to set time")
                return
                
            title = self.player.get_title()
            #  if an error was encountred while retriving the title, then use
            #  filename
            if title == -1:
                title = os.path.basename(self.MediaList.GetItemCollectionData( i, "filename"))
            self.StatusBar.SetStatusText("%s - wxVLCplayer" % title)
        
        else:
            if next_start_at:
                self.StatusBar.SetStatusText("Waiting...")
            else:
                self.StatusBar.SetStatusText("Waiting...")

    def OnStop(self, evt):
        """Stop the player.
        """
        self.IsPlayingToEndTime = False
        self.player.stop()
        # reset the time slider
        self.timeslider.SetValue(0)
        self.timer.Stop()

    def OnTimer(self, evt):
        """Update the time slider according to the current movie time.
        """
        
        # See if we need to start the next song
        if self.IsPlayingToEndTime and not self.player.is_playing():
            self.StartNextSong()
        
        # since the self.player.get_length can change while playing,
        # re-set the timeslider to the correct range.
        length = self.player.get_length()
        self.timeslider.SetRange(-1, length)
        
        # update the time on the slider
        CurrentTime = self.player.get_time()
        self.timeslider.SetValue(CurrentTime)
        self.timeText.SetLabel(ms_to_hms(CurrentTime))     
        self.timeToEndText.SetLabel(ms_to_hms(length - CurrentTime))     

    def OnSetTime(self, evt):
        """Set the volume according to the volume sider.
        """
        slideTime = self.timeslider.GetValue()
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.set_time(slideTime) == -1:
            self.errorDialog("Failed to set time")


    def OnToggleVolume(self, evt):
        """Mute/Unmute according to the audio button.
        """
        is_mute = self.player.audio_get_mute()

        self.player.audio_set_mute(not is_mute)
        # update the volume slider;
        # since vlc volume range is in [0, 200],
        # and our volume slider has range [0, 100], just divide by 2.
        self.volslider.SetValue(self.player.audio_get_volume() / 2)

    def OnSetVolume(self, evt):
        """Set the volume according to the volume sider.
        """
        volume = self.volslider.GetValue() * 2
        # vlc.MediaPlayer.audio_set_volume returns 0 if success, -1 otherwise
        if self.player.audio_set_volume(volume) == -1:
            self.errorDialog("Failed to set volume")

        
    def OnExit(self, evt):
        """Closes the window.
        """
        self.Close()
		
if __name__ == "__main__":
    # Create a wx.App(), which handles the windowing system event loop
    app = wx.App(redirect=False)
    # Create the window containing our small media player
    player = ZampMain("Zamp" + VERSION)
    # show the player window centred and run the application
    player.Show()
    app.MainLoop()
