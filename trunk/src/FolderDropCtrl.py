#!/usr/bin/env python
# -*- coding  : utf-8 -*-

"""
FolderDropCtrl.py

    A 1-line TextCtrl for drag-and-dropping a folder.
    Features :
        - Automatic default "Drop files and folders here" help message
            which is deleted on the first drop
    
    ToDo: 
        - Prompt to save any dropped items to a file.

Ray Pasco   2012-06-05
pascor(at)verizon(dot)net

"""

import sys, os
import wx

import DndDropTargets   as ddt

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class FolderDropCtrl( wx.Panel ) :
    """ Labeled, single folder drop control class derived from a TextCtrl.
    
    It could just as well have been derived from a ListControl or even a StaticText.
    For a single row, using a TextControl is a bit simpler. 
    """
    
    def __init__( self, parent, id=-1, size=(-1, 200), 
                  label=' Default FolderDropCtrlTitle' ) :
        
        super( FolderDropCtrl, self ).__init__( parent=parent, id=-1, size=size, 
                                                style=wx.SIMPLE_BORDER )
        self.SetBackgroundColour( (240, 245, 255) )
        
        #-----  "Global state" variables.
        
        self.anyChanges = False     # ToDo: Prompt to save contents to a file.
        
        #-----
        
        fdcLabel = wx.StaticText( self, -1, label=' '+label, size=(-1, 17) )
        fdcLabel.SetBackgroundColour( (240, 245, 255) )
        
        fdcLabel.SetForegroundColour( wx.BLUE )
        SetBold( fdcLabel )
        
        #-----
        
        fdcStyle = wx.TE_READONLY | wx.TE_DONTWRAP
        fdcID = wx.NewId()
        self.folderTxtCtl = wx.TextCtrl( self, fdcID, size=(500, 37), style=fdcStyle )
        self.folderTxtCtl.Bind( wx.EVT_TEXT,        self.OnTextChanged, id=fdcID )
        self.folderTxtCtl.Bind( wx.EVT_LEFT_DCLICK, self.OnExit )   # Quick app exit.
        
        self.folderTxtCtl.SetBackgroundColour( wx.WHITE )        
        
        fdcFont = wx.Font( 9, wx.MODERN, wx.NORMAL, wx.NORMAL, False, 'Lucida Console' )
        self.folderTxtCtl.SetFont( fdcFont )
        
        self.folderDropTarget = self.folderTxtCtl       # The specific control in this class
        
        #-----  LAYOUT
        
        fdcPnl_vertSzr = wx.BoxSizer( wx.VERTICAL )     # Group the 2 controls
        
        fdcPnl_vertSzr.Add( fdcLabel,          proportion=0, flag=wx.EXPAND )
        fdcPnl_vertSzr.Add( self.folderTxtCtl, proportion=0, flag=wx.EXPAND )
        
        self.SetSizer( fdcPnl_vertSzr )    # Associate the sizer to container control
        
    #end __init__
    
    #----------------------------------
    
    def GetFolder( self ) :
        
        return self.folderTxtCtl.GetLineText( 0 )
    
    #----------------------------------
    
    def GetDropTarget( self ) :
        """ Returns the control that is to be this class's files-drop-target. """
        
        return self.folderDropTarget     # self.folderTxtCtl
    
    #----------------------------------
    
    def WriteText( self, text ) :
        """  A simple utility function "drills down" to the textCtrl's 
        WriteText built-in method.
        """
        # Always adjust the insertion point BEFORE the insertion.
        self.folderTxtCtl.SetInsertionPointEnd()
        self.folderTxtCtl.WriteText( text )
        
    #end def
    
    #----------------------------------
    
    def SetCallbackFunc( self, dropCallbacFunc=None ) :
        """ This method is called from the parent container who wants
        its instantiated FolderDropCtrl object to gain dropFiles capability.
        The parent provides a dropFiles callback function reference.
        """
        
        # Create a dropFiles event association for this control.
        #    [ SetDropTarget ] is a built-in method for (all ?) controls.
        self.folderDropTarget.SetDropTarget( ddt.FilesDropTarget( self.folderDropTarget ) )
        
        # Install the callback-function for this class's parent-widget dropFiles-event.
        self.folderDropTarget.dropFunc = dropCallbacFunc
        
    #end def
    
    #----------------------------------
    
    def OnTextChanged( self, event ) :
        
        self.anyChanges = True
        event.Skip()        # ?
        
    #------------------------------
    
    def OnExit( self, event ) :
        wx.Exit()       # Exit wx.App.MainLoop{}.
    
#end FolderDropCtrl class
    
#------------------------------------------------------------------------------

def SetBold( ctrl ) :
    
    font = ctrl.GetFont()
    font.SetWeight( wx.BOLD )
    ctrl.SetFont( font )
    
#------------------------------------------------------------------------------
