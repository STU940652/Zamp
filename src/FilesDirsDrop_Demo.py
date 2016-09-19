#!/usr/bin/env python
# -*- coding  : utf-8 -*-

"""
FilesDirsDrop_Demo.py
    
    
Ray Pasco   2012-06-05
pascor(at)verizon(dot)net

"""

import sys, os
import wx

import DndDropTargets       as ddt
import FilesDirsDropCtrl    as fddc
import FolderDropCtrl       as fdc

try :                   # For shortening long paths in MSW, only.
    import win32api     
    ntGetShortpathname = win32api.GetShortPathName
except :
    ntGetShortpathname = None

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class AppFrame( wx.Frame ) :

    def __init__( self, args, argc, title='Files and Folders Drop Demo',
                        DEVEL=False ) :
        
        self.DEVEL = DEVEL
        
        super( AppFrame, self ).__init__( parent=None, id=-1, title=title, pos=(350, 0) )
        
        self.SetClientSize( (650, 375) )
        self.Bind( wx.EVT_CLOSE, self.OnExit )   # [ X ] button.  Hook for the future
        
        frmPanel = wx.Panel( self, -1 )     # For uniform cross-platform Frame appearance.
        frmPanel.Bind( wx.EVT_LEFT_DCLICK, self.OnExit )
        frmPanel.SetName( 'frmPanel' )      # For instantiated control identification.
        frmPanel.SetBackgroundColour( (240, 245, 255) )
        
        #-----  Global attributes
        
        self.filesAndLinks = list()
        self.exeFolder = None
        self.incFoldersList = list()
        
        #-----  FILES AND LINKS
        
        self.filesDropCtrl =  \
                fddc.FilesDirsDropCtrl( frmPanel, size=( -1, 100), 
                                        label='Any Files and Links :' )
        self.filesDropCtrl.SetName( 'AppFrame::self.filesDropCtrl' )
        
        # Associate the control with this app's dropfiles handler.
        self.filesDropCtrl.SetCallbackFunc( self.OnFilesDropped )
        
        # Write Column Header labels
        headerLabelList = [ 'File or Link Name', 'Parent Path' ]
        self.filesDropCtrl.WriteHeaderLabels( headerLabelList )
        
        # Write some "help info". It will be deleted on the first fileDrop.
        # It will reappear if all dropped items are deleted.
        # This call MUST be made after calling .WriteHeaderLabels{}.
        srcFilesHelpText = 'Drop Files and Links Here'
        self.filesDropCtrl.WriteHelptext( srcFilesHelpText )
        
        #-----  SINGLE FOLDER
        
        self.singleFolderDropCtrl =  \
                fdc.FolderDropCtrl( frmPanel, label='Folder :' )
        self.singleFolderDropCtrl.SetName( 'AppFrame::self.singleFolderDropCtrl' )
        
        # Associate the control with this app's dropfiles handler.
        self.singleFolderDropCtrl.SetCallbackFunc( self.OnSingleFolderDropped )
        
        # Write some "help info" lines.
        srcFilesHelpText = ' Drop a Folder Here'
        self.singleFolderDropCtrl.WriteText( srcFilesHelpText )
        
        #-----  MULTIPLE FOLDERS
        
        self.multipleFoldersDropCtrl =  \
                fddc.FilesDirsDropCtrl( frmPanel, size=( -1, 100), 
                                          label=' Folders :' )
        self.multipleFoldersDropCtrl.SetName( 'AppFrame::self.multipleFoldersDropCtrl' )
        
        # Associate the control with this app's dropfiles handler.
        self.multipleFoldersDropCtrl.SetCallbackFunc( self.OnIncFoldersDropped )
        
        # Write Column Header labels
        headerLabelList = [ 'Leaf Folder', 'Folder Parent Path' ]
        self.multipleFoldersDropCtrl.WriteHeaderLabels( headerLabelList )
        
        # Write some "help info" as a fake row entry.
        incFoldersHelpText = 'Drop Folders Here'
        self.multipleFoldersDropCtrl.WriteHelptext( incFoldersHelpText )
        
        #-----  BUTTON PANEL
        
        onButtonHandlersList = [ self.OnListFilesLinksButton, 
                                 self.OnListSingleFolderButton, 
                                 self.OnListFoldersButton,
                               ]
        self.buttonPanel = ListButtonPanel( frmPanel, 
                                            onButtonHandlers=onButtonHandlersList )
        
        #-----  FRMPANEL LAYOUT
        
        frmPnl_vertSzr = wx.BoxSizer( wx.VERTICAL )
        frmPnl_vertSzr.AddSpacer( 10 )
        frmPnl_vertSzr.Add( self.filesDropCtrl,   flag=wx.EXPAND )   # Expand horizontaly
        frmPnl_vertSzr.AddSpacer( 10 )
        frmPnl_vertSzr.Add( self.singleFolderDropCtrl,  flag=wx.EXPAND )
        frmPnl_vertSzr.AddSpacer( 10 )
        frmPnl_vertSzr.Add( self.multipleFoldersDropCtrl, flag=wx.EXPAND )
        frmPnl_vertSzr.AddSpacer( 10 )
        frmPnl_vertSzr.Add( self.buttonPanel,    flag=wx.EXPAND )
        frmPnl_vertSzr.AddSpacer( 10 )
        
        # Make an east and west side (horzontal) border/padding.
        frmPnl_outerHorzSzr = wx.BoxSizer( wx.HORIZONTAL )
        frmPnl_outerHorzSzr.AddSpacer( 10 )     # border/padding
        frmPnl_outerHorzSzr.Add( frmPnl_vertSzr, proportion=1 )
        frmPnl_outerHorzSzr.AddSpacer( 10 )
        
        frmPanel.SetSizerAndFit( frmPnl_outerHorzSzr )
        
        #-----
        
        self.Show()
        
    #end __init
    
    #----------------------------------
    
    def OnIncFoldersDropped( self, filenameDropDict ) :
        """ Callback function for self.multipleFoldersDropCtrl dropfiles. 
        
        Use only dropped folders.
        """
        
        # A convenience alias :
        dropTarget = self.multipleFoldersDropCtrl.GetDropTarget()    # self.filesDropCtrl.listCtrl
        
        #-----
        
        # Extract the info from the drop data dictionary.
        dropCoord = filenameDropDict[ 'coord' ]                 # Not used as yet.
        pathList = filenameDropDict[ 'pathList' ]
        leafFolderList = filenameDropDict[ 'basenameList' ]     # leaf folders, not basenames !
        
        commonPathname = filenameDropDict[ 'pathname' ]
        if (os.name == 'nt')  and  (ntGetShortpathname != None) :
            if (len( commonPathname ) > 40) :             # Set an arbitrary max width.
                commonPathname = ntGetShortpathname( commonPathname )
        #end if
        
        # Keep only folders.
        for aFolder in leafFolderList :
            
            _longFormParentPath, leafFolder = os.path.split( aFolder )
            
            # Reconstruct the uncompressed path for storage.
            fullpath = os.path.join( commonPathname, aFolder )
            
            if (os.path.isdir( fullpath ))  and  \
               (not fullpath in self.incFoldersList) :
                
                textTuple = [ leafFolder, commonPathname ]
                self.incFoldersList.append( fullpath )      # Save and ...
                dropTarget.WriteTextTuple( textTuple )      # Display
                
        #end for
        
    #end OnIncFoldersDropped def
    
    #----------------------------------
    
    def OnFilesDropped( self, filenameDropDict ) :
        """ Callback function for self.filesDropCtrl dropfiles. 
        
        Accepts only files and links though filenameDropDict may have folders in it.
        """
        
        print('>>>>>>>>  OnFilesDropped{}');   print()
        
        # A convenience alias :
        dropTarget = self.filesDropCtrl.GetDropTarget()  # self.filesDropCtrl.listCtrl
        
        #-----
        
        # Extract the info from the drop data dictionary.
        pathList = filenameDropDict[ 'pathList' ]
        commonPathname = filenameDropDict[ 'pathname' ]
        basenameList = filenameDropDict[ 'basenameList' ]   # Not used in this method.
        dropCoord = filenameDropDict[ 'coord' ]             # Not used in this method.
        
        if (os.name == 'nt')  and  (ntGetShortpathname != None) :
            if (len( commonPathname ) > 40) :             # Set an arbitrary max width.
                commonPathname = ntGetShortpathname( commonPathname )
        
        # Write (.append) a text 2-element list for each basename 
        for aPath in pathList :     # May include folders.
            
            # Keep just files and link files.
            if not os.path.isdir( aPath ) :
                
                if (aPath not in self.filesAndLinks) :
                    self.filesAndLinks.append( aPath )
                
                _longFormParentPath, basename = os.path.split( aPath )
                textTuple = (basename, commonPathname)
                dropTarget.WriteTextTuple( textTuple )
            
            #end if
            
        #end for
        
    #end OnFilesDropped def
    
    #----------------------------------
    
    def OnSingleFolderDropped( self, filenameDropDict ) :
        """ Callback function for self.singleFolderDropCtrl dropfiles. """
        
        print('>>>>>>>>  OnSingleFolderDropped{}');   print()
        
        # A convenience alias :
        dropTarget = self.singleFolderDropCtrl.GetDropTarget()
        dropCoord = filenameDropDict[ 'coord' ]         # Not used as yet.
        parentPath = filenameDropDict[ 'pathname' ]
        
        # User should have dropped only one file or folder.
        fileOrFolder = filenameDropDict[ 'basenameList' ][ 0 ]
        fullpath = os.path.join( parentPath, fileOrFolder )
        if os.path.isdir( fullpath ) :      # User dropped a folder:  Use this.
            exeFolderpath = fullpath
        else :                              # User dropped a file:  Use its parent path.
            exeFolderpath = parentPath
        
        if (os.name == 'nt')  and  (ntGetShortpathname is not None):
            if (len( exeFolderpath ) > 40) :
                exeFolderpath = ntGetShortpathname( exeFolderpath )
        
        if not hasattr( self, 'exeFolderpath' ) :
            self.exeFolderpath = None
        
        # This hardly seems worth doing...
        if (exeFolderpath == self.exeFolderpath) :
            #BEEPCHAR = chr( 0x07 )
            #sys.stderr.write( BEEPCHAR )
            return
            #-----
        
        # Save and display the new folder path.
        self.exeFolderpath = exeFolderpath
        dropTarget.Clear()              # Clear out any initial "help" lines.
        dropTarget.WriteText( self.exeFolderpath + '\n' )
        
    #end OnSingleFolderDropped def
    
    #----------------------------------
    
    def OnExit( self, event ) :
        """ "He's dead, Jim. """
        
        wx.Exit()   # Exit/break out of App.MainLoop{}.
        
    #end OnExit def
    
    #----------------------------------
    
    def OnSaveFile( self, event ) :
        
        if self.edLastFilenameSaved:
            
            try:
                file = open( self.edLastFilenameSaved, 'w' )
                text = self.edTextCtrl.GetValue()
                file.write( text )
                file.close()
                
                self.statusbar.SetStatusText( os.path.basename( self.edLastFilenameSaved ) + ' saved', 0 )
                self.anyChanges = False
                
            except IOError as error:
                errDlg = wx.MessageDialog( self, 'Error saving file\n' + str( error ) )
                errDlg.ShowModal()
            #end try
            
        else:
            self.OnSaveAsFile( event )
        #end if
        
    #end OnSaveFile def
    
    #----------------------------------
    
    def OnListFilesLinksButton( self, event ) :
        
        print('-'*79 + '\n')
    
        itemsList = self.filesDropCtrl.GetAllRows()     # GetAllFiles() will also work.
        print('>>>>  All Dropped Files and Links from [ %s ] :\n'  \
              %( self.filesDropCtrl.GetName() ))
        if itemsList :
            for item in itemsList :
                print('  [ %s ]' %( item ))
        else :
            print('  {None to list}')
        print()
        
    #----------------------------------
    
    def OnListSingleFolderButton( self, event ) :
        
        print('-'*79 + '\n')
    
        folderItem = self.singleFolderDropCtrl.GetFolder()
        
        print('>>>>  Dropped Folder from [ %s ] :\n'  \
              %( self.singleFolderDropCtrl.GetName() ))
        
        if os.path.exists( folderItem ) :
            print('  [ %s ]' %( folderItem ))
        else :
            print('  {None to list}')
        print()
    
    #----------------------------------
    
    def OnListFoldersButton( self, event ) :
        
        print('-'*79 + '\n')
    
        foldersList = self.multipleFoldersDropCtrl.GetAllFolders()
        
        print('>>>>  Dropped Folders from [ %s ] :\n'  \
              %( self.multipleFoldersDropCtrl.GetName() ))
        
        if foldersList :
            for item in foldersList :
                print('  [ %s ]' %( item ))
        else :
            print('  {None to list}')
        print()
    
#end AppFrame def

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class ListButtonPanel( wx.Panel ) :
    """ Panel that holds the 3 "Get_" buttons. """
    
    def __init__( self, parent=None, id=-1, onButtonHandlers=None ) :
        
        super( ListButtonPanel, self ).__init__( parent=parent, id=id )  # , size=(300, 100) )
        self.Bind( wx.EVT_LEFT_DCLICK, self.OnExit )
        
        listAllBtn   = wx.Button( self, -1, 'List Files' )
        listFilesBtn = wx.Button( self, -1, 'List Single Folder' )
        listDirsBtn  = wx.Button( self, -1, 'List Folders' )
        
        if onButtonHandlers :       # Defined in the main app.
            listAllBtn.Bind( wx.EVT_LEFT_DOWN,   onButtonHandlers[ 0 ] )
            listFilesBtn.Bind( wx.EVT_LEFT_DOWN, onButtonHandlers[ 1 ] )
            listDirsBtn.Bind( wx.EVT_LEFT_DOWN,  onButtonHandlers[ 2 ] )
        
        btnPanel_innerHorzSzr = wx.BoxSizer( wx.HORIZONTAL )
        btnPanel_innerHorzSzr.AddStretchSpacer( prop=1 )
        btnPanel_innerHorzSzr.Add( listAllBtn )
        btnPanel_innerHorzSzr.AddSpacer( 25 )
        btnPanel_innerHorzSzr.Add( listFilesBtn )
        btnPanel_innerHorzSzr.AddSpacer( 25 )
        btnPanel_innerHorzSzr.Add( listDirsBtn )
        btnPanel_innerHorzSzr.AddStretchSpacer( prop=1 )
        
        btnPanel_outerVertSzr = wx.BoxSizer( wx.VERTICAL )
        btnPanel_outerVertSzr.AddSpacer( 5 )
        btnPanel_outerVertSzr.Add( btnPanel_innerHorzSzr, flag=wx.EXPAND )
        btnPanel_outerVertSzr.AddSpacer( 5 )
        
        self.SetSizer( btnPanel_outerVertSzr )
        self.Layout()
        
    #end __init__
    
    #----------------------------------
    
    def OnExit( self, event ) :
        """ "He's dead, Jim. """
        
        wx.Exit()   # Exit/break out of App.MainLoop{}.
        
    #end OnExit def
    
#end ListButtonPanel class

#==============================================================================

if __name__ == '__main__' :
    
    args = sys.argv
    THISPYFILE = args.pop( 0 )
    argc = len( args )
        
    app = wx.App( redirect=False )
    appFrame = AppFrame( args, argc, DEVEL=1 )
    
    import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
    
#end if