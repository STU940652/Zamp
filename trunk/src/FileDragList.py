""" DnD demo with listctrl. """

import wx
import pickle

class DragList(wx.ListCtrl):
    def __init__(self, *arg, **kw):
        if 'style' in kw and (kw['style']&wx.LC_LIST or kw['style']&wx.LC_REPORT):
            kw['style'] |= wx.LC_SINGLE_SEL
        else:
            kw['style'] = wx.LC_SINGLE_SEL|wx.LC_LIST

        wx.ListCtrl.__init__(self, *arg, **kw)

        self.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)

        dt = ListDrop(self._insert)
        self.SetDropTarget(dt)
        
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

    def _insert(self, x, y, text):
        """ Insert text at given x, y coordinates --- used with drag-and-drop. """

        # Clean text.
        # import string
        # text = ''.join([x for x in text if x in (string.ascii_letters + string.digits + string.punctuation + ' ')])

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
                
        if (isinstance( text, list)):
            for r in text:
                textList = r["text"]
                self.InsertItem(index, textList[0])
                for i in range(1, len(textList)): # Possible extra columns
                    self.SetItem(index = index, column = i, label = textList[i])             
        else:
            self.InsertItem(index, text)
        
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

            if (format.GetType() == 49744): # CustomDataObject
                self.setFn(x, y, pickle.loads(dataobj.GetData()))

            if (format.GetType() == 13): # TextDataObject
                self.setFn(x, y, dataobj.GetText())

            if (format.GetType() == 15): # FileDataObject
                for filename in dataobj.GetFilenames():
                    self.setFn(x, y, filename)
                    
            
        # what is returned signals the source what to do
        # with the original data (move, copy, etc.)  In this
        # case we just return the suggested value given to us.
        return d
        
    def OnDropFiles(self, x, y, filenames):
        print (filenames)

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