#!/usr/bin/env python
# -*- coding  : utf-8 -*-

"""
FilesDirsDropCtrl.py

    An intelligent ListCtrl for drag-and-dropping files and folders.
    
    Whether both files and folders, just files, just folders or just specific ones
    is determined by the drop event callback function's filtering logic 
    defined in the main app.
    
    Features :
        - Both files and folders may be dropped.
        - Duplicate dropped files/folders are ignored.
        - Dropped items may be deleted using a context (right-click) menu.
        
        - Retreive all row complete paths (folders and files)
        - Retrieve just file names or leaf folder name
        - Retrieve just the parent folder paths
    
        - A "Drop files and folders here" help message
            is deleted on the first drop.
        - The help message disappears when a file is dropped.
        - The help message reappears when all dropped items/rows/entries are deleted.
        - Properly functioning column autosizing: Takes into account the column headers !
        
    ToDo: 
        - DeleteAll()
        - SaveAllToFile()
        - Allow only files and/or fiolders to be dropped.

Ray Pasco   2012-06-05
pascor(at)verizon.net

"""

import sys, os
import wx

import DndDropTargets   as ddt

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class FilesDirsDropCtrl( wx.Panel ) :
    
    def __init__( self, parent, callbackFunc=None, size=(-1, 100), 
                  label='Default FilesDirsListCtrlTitle', DEVEL=False ) :
        
        super( FilesDirsDropCtrl, self ).__init__( parent=parent, id=-1, 
                                                   style=wx.SIMPLE_BORDER )
        
        self.callbackFunc = callbackFunc    # For the files drop handler.
        
        #-----
        
        flcLabel = wx.StaticText( self, -1, label=' '+label, size=(-1, 17) )
        flcLabel.SetForegroundColour( wx.BLUE )     # set the text color
        SetBold( flcLabel )
        
        # wx.LC_REPORT creates column headers.
        flcID = wx.NewId()
        self.filesLstCtl = FilesDirsListCtrl( self, flcID, size=size, 
                                                    style=wx.LC_REPORT )
        self.filesLstCtl.Bind( wx.EVT_LEFT_DCLICK, self.OnExit )
        
        flcFont = wx.Font( 9, wx.MODERN, wx.NORMAL, wx.NORMAL, False, 'Lucida Console' )
        self.filesLstCtl.SetFont( flcFont )
        
        self.filesDropTarget = self.filesLstCtl     # Clearer to use an alias.
        
        #-----  LAYOUT
        
        flcPnl_vertSzr = wx.BoxSizer( wx.VERTICAL ) # Group the 2 controls
        
        flcPnl_vertSzr.Add( flcLabel,          proportion=0, flag=wx.EXPAND )
        flcPnl_vertSzr.Add(  self.filesLstCtl, proportion=1, flag=wx.EXPAND )
        
        flcPnl_horzSzr = wx.BoxSizer( wx.HORIZONTAL )
        flcPnl_horzSzr.Add( flcPnl_vertSzr, proportion=1, flag=wx.EXPAND )
        
        self.SetSizer( flcPnl_horzSzr )     # Associate the sizer to the container control
        
    #end __init__
    
    #----------------------------------  FilesDirsDropCtrl
    
    def GetAllRows( self ) :
        
        return self.filesDropTarget.GetAllRows()
        
    #----------------------------------  FilesDirsDropCtrl
    
    def GetAllFiles( self ) :
        
        return self.filesDropTarget.GetAllFiles()
        
    #----------------------------------  FilesDirsDropCtrl
    
    def GetAllFolders( self ) :
        
        return self.filesDropTarget.GetAllFolders()
        
    #----------------------------------  FilesDirsDropCtrl
    
    def WriteHelptext( self, helpText='Drop Files and Folders Here' ) :
        """ Write a message to be erased on the first file drop. """
        
        helpTextTuple = [ ' '*20, helpText ]
        self.filesLstCtl.Append( helpTextTuple )
        
        for col in range( 2 ) :       # Widen the column widths.
            self.filesLstCtl.SetColumnWidth( col, wx.LIST_AUTOSIZE )
        
        # Save for rewriting if all list entries have been deleted.
        self.filesLstCtl.HelpTextTuple = helpTextTuple
        
    #end def
    
    #----------------------------------  FilesDirsDropCtrl
    
    def WriteHeaderLabels( self, headerLabelList ) :
        """ Write the column header labels. """
        
        self.headerLabelList = headerLabelList
        self.filesLstCtl.headerLabelList = headerLabelList
        
        #-----
        
        # This sets the "official" number of columns the textCtrl has.
        self.numCols = len( self.headerLabelList )
        self.filesLstCtl.numCols = self.numCols
        
        for col in range( self.numCols ) :
            self.filesLstCtl.InsertColumn( col, self.headerLabelList[ col ] )
        
        # AUTOSIZE
        for col in range( self.numCols ) :
            self.filesLstCtl.SetColumnWidth( col, wx.LIST_AUTOSIZE )
        
        # Widen the header-list-as-row-data in order to completely show the column labels.
        # This hack works very well !
        hdrListWidened = headerLabelList
        for i in range( len( hdrListWidened ) ) :
            hdrListWidened[ i ] += ' '     # Estimated number of spaces needed 
                                            #   to fully show the header.
        # Delete the header-list-as-row-data.
        self.filesLstCtl.Append( hdrListWidened )   # Does NOT add to item/row data list.
        numRows = self.filesLstCtl.GetItemCount()
        self.filesLstCtl.DeleteItem( numRows - 1 )
        
    #end def
    
    #----------------------------------  FilesDirsDropCtrl
    
    def SetCallbackFunc( self, dropCallbacFunc=None ) :
        """ This method is called from the parent container wanting
        its FilesDirsDropCtrl object to gain dropFiles capability.
        
        The parent provides a dropFiles callback function reference
        that actually processes the dropfiles data (a dictionary)
        whenever files are dropped.
        """
        
        # Create a dropFiles event association for this control.
        #    [ SetDropTarget ] is a built-in method for (all ?) controls.
        self.filesDropTarget.SetDropTarget( ddt.FilesDropTarget( self.filesDropTarget ) )
        
        # Install the callback-function for this class's parent-widget dropFiles-event.
        self.filesDropTarget.dropFunc = dropCallbacFunc
        
    #end def
    
    #----------------------------------  FilesDirsDropCtrl
    
    def GetDropTarget( self ) :
        """ Returns the control reference for this class's files-drop-target. """
        
        return self.filesDropTarget     # self.filesLstCtl
    
    #------------------------------  FilesDirsDropCtrl
    
    def OnExit( self, event ) :
        wx.Exit()       # Exit method wx.App.MainLoop{}.
    
#end FilesDirsDropCtrl class

#------------------------------------------------------------------------------

def SetBold( ctrl ) :
    
    font = ctrl.GetFont()
    font.SetWeight( wx.BOLD )
    ctrl.SetFont( font )

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class FilesDirsListCtrl( wx.ListCtrl ) :
    """ The dropFiles control for class FilesDirsDropCtrl.
    
    Dropped files are listed in this control.
    Duplicate dropped files are gracefully ignored.
    
    Files may be deleted using a context (right-click) menu.
    This control keeps track of the current entry data 
    and the current entry count. Line items to be deleted are
    first verified to be in the entry data list.
    """
    
    def __init__( self, *args, **kwargs ) :
        
        super( FilesDirsListCtrl, self ).__init__( *args, **kwargs )
    
        # For row deletions.
        self.Bind( wx.EVT_LEFT_DOWN,  self.OnFindCurrentRow )
        self.Bind( wx.EVT_RIGHT_DOWN, self.OnRightDown )
        
        #----  "Global attributes"
        
        self.currRow = None
        self.numCols = -1
        
        self.entriesList = list()   # Actual dropped file entries; duplicates are avoided.
        self.numEntries = 0         # Dropped file entry count.
        self.haveEntries = False    # Tracks actual dropped file entries, but not help entries.
        
    #end __init__
    
    #----------------------------------  FilesDirsListCtrl
    
    def GetAllRows( self ) :
        """ Return a list of all current row data.
        
        Note that extracting this info directly from the control is insanely complicated. 
        This is another reason why the row data list is maintained.
        """
        
        # SANITY CHECK
        assert( len( self.entriesList ) == self.numEntries )
        
        allRowsList = list()
        for rowIdx in range( self.numEntries ) :
            
            rowData = self.entriesList[ rowIdx ]
            basename   = rowData[ 0 ]
            foldername = rowData[ 1 ]
            fullpath = os.path.join( foldername, basename )
            allRowsList.append( fullpath )
            
        #end if
        
        return allRowsList
        
    #end GetAllRows def
    
    #----------------------------------  FilesDirsListCtrl
    
    def GetAllFiles( self ) :
        """ Return a list of all current files in the row data.
        
        Note that extracting this info directly from the control is insanely complicated. 
        This is another reason why the row data list is maintained.
        """
        
        allRowsList = self.GetAllRows()     # Complete file paths list
        
        # SANITY CHECK
        assert( len( allRowsList )      == self.numEntries )
        
        allFoldersList = list()
        for fullpath in allRowsList :        # len( allRowsList )
            
            if (not os.path.isdir( fullpath ) ) :     # files and links
                allFoldersList.append( fullpath )
        
        return allFoldersList
        
    #end GetAllFiles def
    
    #----------------------------------  FilesDirsListCtrl
    
    def GetAllFolders( self ) :
        """ Return a list of all current folders in the row data.
        
        Note that extracting this info directly from the control is insanely complicated. 
        This is another reason why the row data list is maintained.
        """
        
        allRowsList = self.GetAllRows()     # Complete file paths list
        
        # SANITY CHECK
        assert( len( allRowsList )      == self.numEntries )
        
        allFoldersList = list()
        for fullpath in allRowsList :        # len( allRowsList )
            
            if os.path.isdir( fullpath ) :     # files and links
                allFoldersList.append( fullpath )
        
        
        return allFoldersList
        
    #end GetAllFolders def
    
    #----------------------------------  FilesDirsListCtrl
    
    def WriteTextTuple( self, rowDataTuple ) :
        """  Write non-duplicate row data to the LstCtrl.
        
        The text data may be any indexable, 2-text-element data object.
        E.g., a list or tuple [or set ?].
        
        All row entries written to the ListCtrl are also stored in a list 
          for deletion verification purposes.
        """
        
        # Do some basic data checking.
        assert (len( rowDataTuple ) >= self.numCols),  \
                'Given data must have at least %d items.' %( self.numCols )
        
        for idx in range( self.numCols ) :    # Need to check only the first two elements.
            assert( isinstance( rowDataTuple[ idx ], str ) ),  \
               'One or both data elements are not strings.'
        
        #-----
        
        # Write a new row's ietm/text/data.
        rowDataTupleTruncated = tuple( rowDataTuple[ :self.numCols ] )
        if (rowDataTupleTruncated not in self.entriesList) :
            
            if (not self.haveEntries) :     # Clear any help message(s).
                self.DeleteAllItems()
            
            # Update everything
            self.Append( rowDataTupleTruncated )    # Add row to the ListCtrl.
            self.entriesList.append( rowDataTupleTruncated )    # Store the row data.
            self.numEntries += 1 
            self.haveEntries = True
            
            # Set reasonable column widths.
            self.Autosize()
            
            """ DEVEL
            #self.GetAllRows()
            #self.GetAllFolders()
            #self.GetAllFiles()
            """
            
        #end if
        
    #end WriteTextTuple def
    
    #----------------------------------  FilesDirsListCtrl
    
    def Autosize( self ) :
        """
        Intelligently autosize the first column (the filenames, if any) since the 
          control's autosizing method does not include the width of the column labels.
        """
        
        # Temporarily appending the column headers as a row data item
        #   causes the columns to be resized to min( dropEntryText, headerText ).
        self.Append( self.headerLabelList )
        for colIndex in range( len( self.headerLabelList ) ) :
            self.SetColumnWidth( colIndex, wx.LIST_AUTOSIZE )
        
        self.DeleteItem( self.GetItemCount() - 1 )
        
        """
        If any one filename is very long the column width was set too long and 
          occupies "too much" width in the control causing little or no display 
          of the folder paths to be shown. 
        
        Set first row's width to no more than 50% of the control's client width.
        This is a "reasonable" balance which leaves both columns's data 
           at least 50% displayed at all times.
        """
        firstColMaxWid = self.GetClientSize()[ 0 ] / 2      # Half the avaiable width.
        firstColIndex = 0                           # Avoid the use of "Magic Numbers".
        firstColActualWid = self.GetColumnWidth( firstColIndex )
        reasonableWid = min( firstColMaxWid, firstColActualWid )
        self.SetColumnWidth( firstColIndex, reasonableWid )
        
    #end Autosize def
    
    #----------------------------------  FilesDirsListCtrl
    
    def OnFindCurrentRow( self, event ) :
        """ Triggered on every wx.EVT_LEFT_DOWN.
        
        Is also called by OnRightDown{}.
        """
        
        # Deselect any previously selected row.
        if (self.currRow is not None) :
            self.Select( self.currRow, False )  
        
        # Select the currently clicked row.
        row, _ignoredFlags = self.HitTest( event.GetPosition() )
        self.currRow = row      # Save row index for later use.
        self.Select( row )
        
    #end def
    
    #----------------------------------  FilesDirsListCtrl
    
    def OnRightDown( self, event ) :
        
        menu = wx.Menu()
        menuItem_delete = menu.Append( -1, 'Delete this entry' )
        
        self.Bind( wx.EVT_MENU, self.OnDeleteRow, menuItem_delete )
        
        # Select row
        self.OnFindCurrentRow( event )
        
        self.PopupMenu( menu, event.GetPosition() )
        
    #end def
    
    #----------------------------------  FilesDirsListCtrl
    
    def OnDeleteRow( self, event ) :
        
        if (self.currRow >= 0) :
            
            # This row data must have been appended to self.entriesList.
            
            #-----  SANITY CHECK
            
            # self.GetItemCount() may be greater than self.numEntries due to help messages.
            assert( self.numEntries == len( self.entriesList ) )
                
            #-----
            
            # Retreive the selected raw-row-data as a list of lists.
            allSelectedRowData = self.GetAllSelectedRowData()
            
            if (len( allSelectedRowData ) >= 1) :
                
                #-----
                
                rawRowData = allSelectedRowData[ 0 ]    # There can be only a single row selected.
                lineIdx       = rawRowData[ 0 ]
                unknownData   = rawRowData[ 1 ]
                textDataTuple = tuple( rawRowData[ 2: ] )   # Make same type as in self.entriesList
                
                if self.numEntries :
                    
                    try :
                        entryListIndex = None
                        entryListIndex = self.entriesList.index( textDataTuple )
                    except ValueError :
                        print('####  ERROR:  textDataTuple NOT FOUND in self.entriesList :')
                        print(' ', textDataTuple)
                        print()
                        
                        return
                        #-----
                        
                    #end try
                    
                    # Delete this row item from [ self.entriesList ].
                    del self.entriesList[ entryListIndex ]
                    
                    # Update the status vars.
                    self.numEntries -= 1
                    if (self.numEntries < 1) :
                        
                        self.haveEntries = False
                        self.Append( self.HelpTextTuple )
                        
                    # Finally, detete the textList row item.
                    self.DeleteItem( self.currRow )
                    
                #end if self.numEntries
                
            #end if (len( allSelectedRowData ) > 0)
        
        #end if (self.currRow >= 0)
        
    #end OnDeleteRow def
    
    #----------------------------------
    
    def GetAllSelectedRowData( self ) :
        """ A strange algorithm to retrieve all selected row data.
        
        From "DnD demo with listctrl" @ http ://wiki.wxpython.org/ListControls#List_Controls
        """
        
        allSelectedRowData = list()
        idx = -1        # Special flag value.
        while True :    # Find all the selected items and put them in a list
            
            idx = self.GetNextItem( idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED )
            
            # ???  If return value is [ -1 ] why predefine it as [ -1 ] before loop entry ?
            if (idx == -1) :    
                break
            #-----
            
            allSelectedRowData.append( self.GetItemInfo( idx ) )
            
        #end while
        
        return allSelectedRowData
        
    #end GetAllSelectedRowData def
    
    #----------------------------------
    
    def GetItemInfo( self, idx ) :
        """ Collects all relevant data of a listitem and puts it in a list 
        
        From "DnD demo with listctrl" @ http ://wiki.wxpython.org/ListControls#List_Controls
        """
        
        rowItemList = list()
        rowItemList.append( idx ) # We need the original index, so it is easier to eventualy delete it
        rowItemList.append( self.GetItemData( idx ) )   # Itemdata
        rowItemList.append( self.GetItemText( idx ) )   # Text first column
        
        for i in range( 1, self.GetColumnCount() ) :    # Possible extra columns
            rowItemList.append( self.GetItem( idx, i ).GetText() )
            
        return rowItemList
        
    #end def
    
#end FilesDirsListCtrl class

#------------------------------------------------------------------------------
