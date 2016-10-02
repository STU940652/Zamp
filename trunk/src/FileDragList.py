""" DnD demo with listctrl. """

import wx
import pickle
import datetime
import os
import os.path

try:
    import vlc
    HAVE_VLC = True
except:
    HAVE_VLC = False
    
#print (vlc.libvlc_get_version())
    
def ms_to_hms (ms):
    try:
        h = int(ms/(60*60*1000))
        msl = ms - h*60*60*1000
        m = int(msl/(60*1000))
        msl = msl - m*60*1000
        s = msl/1000.0
        return "%02i:%02i:%02i" % (h,m,s)
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

class FileDragList(wx.ListCtrl):
    def __init__(self, AfterChange=None, *arg, **kw):
        if 'style' in kw and (kw['style']&wx.LC_LIST or kw['style']&wx.LC_REPORT):
            kw['style'] |= wx.LC_SINGLE_SEL
        else:
            kw['style'] = wx.LC_SINGLE_SEL|wx.LC_LIST

        wx.ListCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)

        dt = ListDrop(self._insert)
        self.SetDropTarget(dt)
        self.ItemId = 0
        self.ItemDataCollection = {}
        self.AfterChange = AfterChange
        
    def getItemInfo(self, idx):
        """Collect all relevant data of a listitem, and put it in a dictionary"""
        l = {}
        l["idx"] = idx # We need the original index, so it is easier to eventualy delete it
        l["data"] = self.GetItemData(idx) # Itemdata
        l["text"] = [ self.GetItemText(idx) ] # Text first column
        for i in range(1, self.GetColumnCount()): # Possible extra columns
            l["text"].append(self.GetItem(idx, i).GetText())
        return l
        
    def _startDrag(self, e):
        """ Put together a data object for drag-and-drop _from_ this list. """

        # Create the Custom data object.
        data = wx.CustomDataObject("MediaFileDataObject")
        l = []
        idx = e.GetIndex()
        l.append(self.getItemInfo(idx))
        
        # Get any other selected rows
        idx = -1
        while True: # find all the selected items and put them in a list
            idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if idx == -1:
                break
            if idx != e.GetIndex():
                l.append(self.getItemInfo(idx))
        data.SetData(pickle.dumps(l))
            
        # Create drop source and begin drag-and-drop.
        dropSource = wx.DropSource(self)
        dropSource.SetData(data)
        res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

        # If move, we want to remove the item from this list.
        if res == wx.DragMove:
            # It's possible we are dragging/dropping from this list to this list.  In which case, the
            # index we are removing may have changed...
        
            idx = -1
            while True: # find all the selected items and put them in a list
                idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
                if idx == -1:
                    break
                self.DeleteItem(idx)
                if self.AfterChange:
                    self.AfterChange()

    def _insert(self, x, y, items):
        """ Insert text at given x, y coordinates --- used with drag-and-drop. """
        # Find insertion point.
        index, flags = self.HitTest((x, y))

        if index == wx.NOT_FOUND:
            if flags & wx.LIST_HITTEST_NOWHERE:
                index = self.GetItemCount()
            else:
                return
        else:
            # Get bounding rectangle for the item the user is dropping over.
            rect = self.GetItemRect(index)

            # If the user is dropping into the lower half of the rect, we want to insert _after_ this item.
            if y > rect.y + rect.height/2:
                index += 1
                
        self.InsertItems (index, items)
        
        if self.AfterChange:
            self.AfterChange()

    def InsertItems (self, index = None, items = []):
        if not index:
            index = self.GetItemCount()
            
        for this_item in items:
            if (isinstance( this_item, str)):
                # Filename as a string
                media = vlc.Media(this_item)
                media.parse()
                if media.get_duration():
                    # Only add if length is > 0
                    self.InsertItem(index, media.get_meta(vlc.Meta.Title))
                    self.SetItem(index=index, column = 1, label = ms_to_hms(media.get_duration()))
                    self.SetItemData(index, self.ItemId)
                    self.ItemDataCollection[self.ItemId] = {
                            "duration":datetime.timedelta(milliseconds = media.get_duration()), 
                            "media":media, 
                            "filename":this_item}
                    self.ItemId += 1
                    index += 1
                    
            elif (isinstance( this_item, dict)):
                # Dropped ListItem
                textList = this_item["text"]
                self.InsertItem(index, textList[0])
                for i in range(1, len(textList)): # Possible extra columns
                    self.SetItem(index = index, column = i, label = textList[i]) 
                self.SetItemData(index, this_item["data"])
                
    def GetItemCollectionData (self, index, key):
        return self.ItemDataCollection[self.GetItemData(index)][key]
        
    def SetItemCollectionData (self, index, key, value):
        self.ItemDataCollection[self.GetItemData(index)][key] = value
        
class ListDrop(wx.FileDropTarget):
    """ Drop target for simple lists. """

    def __init__(self, setFn):
        """ Arguments:
         - setFn: Function to call on drop.
        """
        wx.DropTarget.__init__(self)

        self.setFn = setFn

        # specify the type of data we will accept
        #self.data = wx.TextDataObject()
        self.data = wx.DataObjectComposite()
        self.data.Add(wx.CustomDataObject("MediaFileDataObject"))
        self.data.Add(wx.FileDataObject())
        self.data.Add(wx.TextDataObject())
        self.SetDataObject(self.data)

    # Called when OnDrop returns True.  We need to get the data and
    # do something with it.
    def OnData(self, x, y, d):
        # copy the data from the drag source to our data object
        if self.GetData():
            dataobjComp = self.GetDataObject()
            format = self.data.GetReceivedFormat()
            dataobj = dataobjComp.GetObject(format)

            if (format.GetType() == 13): # TextDataObject
                self.setFn(x, y, dataobj.GetText().split())

            elif (format.GetType() == 15): # FileDataObject
                file_list = []
                
                for this_filename in dataobj.GetFilenames():
                    if os.path.isfile(this_filename):
                        file_list.append(this_filename)
                    elif os.path.isdir(this_filename):
                        for dirpath, dirnames, filenames in os.walk(this_filename):
                            file_list.extend([os.path.join(dirpath, f) for f in filenames])
                        
                self.setFn(x, y, file_list)
                    
            else: # CustomDataObject
                self.setFn(x, y, pickle.loads(dataobj.GetData()))
     
        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d

if __name__ == '__main__':
    items = ['Foo', 'Bar', 'Baz', 'Zif', 'Zaf', 'Zof']

    class MyApp(wx.App):
        def OnInit(self):
            self.frame = wx.Frame(None, title='Main Frame')
            self.frame.Show(True)
            self.SetTopWindow(self.frame)
            return True

    app = MyApp(redirect=False)
    dl1 = DragList(app.frame)
    dl2 = DragList(app.frame)
    sizer = wx.BoxSizer()
    app.frame.SetSizer(sizer)
    sizer.Add(dl1, proportion=1, flag=wx.EXPAND)
    sizer.Add(dl2, proportion=1, flag=wx.EXPAND)
    for item in items:
        dl1.InsertItem(99, item)
        dl2.InsertItem(99, item)
    app.frame.Layout()
    app.MainLoop()