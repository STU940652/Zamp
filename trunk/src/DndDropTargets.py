#!/usr/bin/env python
# -*- coding  : utf-8 -*-

"""
DndDropTargets.PY
From:
    @ http://wiki.wxpython.org/DragAndDrop
    "Simple Drag and Drop TARGETING in wx.Python"

Ray Pasco   2012-06-01
pascor(at)verizon(dot)net

"""

import sys, os
import wx

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class FilesDropTarget( wx.FileDropTarget ) :
    """ This object implements Drop Target functionality 
    for both files and folders.
    
    No source object initialization is needed because the source files and dirs 
    come from the OS's filesystem's GUI window, e.g., MSW { Explorer.exe ].
    """
    
    def __init__( self, targetControl ) :
        """ Initialize the Drop Target, passing in a control's Object Reference 
          to indicate what should receive the dropped files """
        
        self.targetControl = targetControl
        
        wx.FileDropTarget.__init__( self )
        self.targetControl = targetControl  # For dropped files are dropped.
      
    #end __init__
    
    #----------------------------------
    
    def FilenameDropDict( self ) :
        """ Defines a succinct dictionary for each given drop file's info. """
        
        filenameDropDict = dict()
        # Initialize it with dummy values.
        filenameDropDict[ 'coord' ] = (-1, -1)          # Real data can never have this value.
        filenameDropDict[ 'pathname' ] = ''             # Real data can never be empty.
        filenameDropDict[ 'basenameList' ] = list()     # Real data can never be empty.
        filenameDropDict[ 'fullPathList' ] = list()     # Real data can never be empty.
        
        return filenameDropDict
        
    #end def
    
    #----------------------------------
    
    def OnDropFiles( self, xOrd, yOrd, pathList ) :
        """ Implement the filenames drop event handler. 
        
        Create a dictionary with all the pertinent info about the filepaths.
        
        This drop handler has no direct way to either know what do 
           with the provided dropFile event filepaths.
        So, when instaiating this class, a function is passed in 
          which should actually do something useful with the data.
        """
        
        #print '$$$$  OnDropFiles{}:   len( pathList ) = %d\n', len( pathList )
        
        # All the paths are (have to be !) the same.
        # The give path is ALWAYS absolute (like what os.path.abspath returns).
        # There HAS to be at least 1 filename or directory name given.
        
        # Separate the dir path from the basename or leafDirectory name.
        pathname, _ignored = os.path.split( pathList[ 0 ] )
        
        # The file's and folders's basenames :
        basenameList = list()
        for aPath in pathList :
            _ignoredDir, aBasename = os.path.split( aPath )
            basenameList.append( aBasename )
            
        expandedPathList = []
        for aPath in pathList:
            if   (os.path.isfile( aPath )) :
                expandedPathList.append(aPath)
            elif (os.path.islink( aPath )) :
                expandedPathList.append(aPath)
            elif (os.path.isdir( aPath )) :
                for root, dirs, files in os.walk(aPath, topdown=False):
                    expandedPathList.extend(files)
        pathList = expandedPathList
                
        # The target control must know the structure of this dict
        #   in order to use this data about to be stored there.
        filenameDropDict = self.FilenameDropDict()
        filenameDropDict[ 'coord' ]         = (xOrd, yOrd)
        filenameDropDict[ 'pathList' ]      = pathList
        filenameDropDict[ 'pathname' ]      = pathname
        filenameDropDict[ 'basenameList' ]  = basenameList
        
        
        # DEVEL listing
        print ('\n$$$$$$$$  OnDropFiles{}:  Drop coord =',  (xOrd, yOrd))
        print ('\n$$$$$$$$  OnDropFiles{}:  pathList :')
        for aPath in filenameDropDict[ 'pathList' ] :
            print ('  [ %s ]' %( aPath ))
        print ()
        print ('          File and Folder Path :')
        print ('  [ %s ]' %( pathname ))
        print ('          Files and Folders:')
        for aFileOrFolder in pathList :
            fileOrDirType = 'UNKNOWN'
            if   (os.path.isfile( aFileOrFolder )) :
                fileOrDirType = 'FILE :\n '
            elif (os.path.islink( aFileOrFolder )) :
                fileOrDirType = 'LINK :\n '
            elif (os.path.isdir( aFileOrFolder )) :
                fileOrDirType = 'DIR :\n '
            #end if
            print ('%s [ %s ]' %( fileOrDirType, aFileOrFolder ))
        #end for
        
        
        # How the app is to use this data :
        if (hasattr( self.targetControl, 'dropFunc' ))  and  \
           (self.targetControl.dropFunc != None) :
            
            # Call the callback function with the processed drop data.
            self.targetControl.dropFunc( filenameDropDict )
        #end if
        
        return True
        
#end FilesDropTarget class

#------------------------------------------------------------------------------
#==============================================================================
#------------------------------------------------------------------------------

class TextDropTarget( wx.TextDropTarget ) :
    """ This object implements Drop Target functionality for text drop data.. 
    """
    
    def __init__( self, targetControl ) :
        """ Initialize the Drop Target, passing in the control's object 
            to indicate what control should receive the dropped text.
        """
        
        wx.TextDropTarget.__init__( self )
        
        # Store the object reference for dropped text.
        self.targetControl = targetControl      
        
    #end __init__
    
#end TextDropTarget class

#------------------------------------------------------------------------------
