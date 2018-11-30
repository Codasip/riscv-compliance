# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

from tkinter import *
from tkinter.ttk import Combobox

class Checkbar(Frame):
    """Multiple checkboxes in single widget.
    
        +------------------------+
        |   _        _           |
        | A|X|     B|X|     C|‾| |  
        |   ‾        ‾        ‾  |
        |   _                 _  |
        | D|X|     E|‾|     F| | |  
        |   ‾        ‾        ‾  |
        +------------------------+
    """
    
    def __init__(self, parent=None, picks=[], splitnum=None, callback=None, **kwargs):
        Frame.__init__(self, parent, highlightthickness=0, bd=0, bg=kwargs.get('bg'))
        self._style = kwargs
        
        if splitnum is None:
            splitnum = int(math.ceil(math.sqrt(len(picks))))
        if splitnum == 0:
            splitnum = 10000
        self.vars = []
      
        for i, pick in enumerate(picks):
            var = BooleanVar()
            var.set(False)
            chk = Checkbutton(self, text=pick, name='id_'+pick, variable=var, **kwargs)
            chk.var = var
            if callback:
                chk.bind('<ButtonPress>', callback) 
            chk.grid(row=i//splitnum, column=i%splitnum, padx=10, pady=5)
            self.vars.append(var)
    
    def state(self):
        return map((lambda var: var.get()), self.vars)
    

class DualListBox(Frame):
    """Widget containing two lisboxes
    and support for moving items between them
    
    +--------+      +--------+
    | value1 |   >  | value6 |
    | value2 |   <  | value7 |
    | value3 |      | value8 |
    | value4 |  >>> | value9 |
    | value5 |  <<< |        |
    +--------+      +--------+
    """
    def __init__(self, parent, *args, **kwargs):
        super(DualListBox, self).__init__(parent, *args, **kwargs)
        
        self.lv1 = StringVar()
        self.lv2 = StringVar()
        
        self.left_box = Listbox(parent, listvariable=self.lv1, selectmode='multiple', height=10, width=20)
        self.right_box = Listbox(parent, listvariable=self.lv2, selectmode='multiple', height=10, width=20)

        self._move_some_right = Button(parent, text='>', width=4, command=lambda: self._move_items(self.left_box, self.right_box, False))
        self._move_some_left = Button(parent, text='<', width=4, command=lambda: self._move_items(self.right_box, self.left_box, False))
        self._move_all_right = Button(parent, text='>>>', width=4, command=lambda: self._move_items(self.left_box, self.right_box, True))
        self._move_all_left = Button(parent, text='<<<', width=4, command=lambda: self._move_items(self.right_box, self.left_box, True))

    
    def _move_items(self, src, dst, everything):
        selected = range(src.size()) if everything else src.curselection()
        # Nothing to move
        if not selected:
            return
        
        items = []
        for index in selected[::-1]:
            items.append(src.get(index))
            src.delete(index)
        
        dst.insert(END, *items[::-1])
            
    def place(self, cnf={}, **kw):
        x = kw.get('x', 0)
        y = kw.get('y', 0)
        
        self.left_box.place(x=x,y=y)
        self.right_box.place(x=x+250, y=y)
        self._move_some_right.place(x=x+175, y=y+10)
        self._move_some_left.place(x=x+175, y=y+40)
        self._move_all_right.place(x=x+175, y=y+90)
        self._move_all_left.place(x=x+175, y=y+120)
        
        Frame.place(self, cnf=cnf, **kw)
    
    def get_values_left(self):
        res = []
        for index in range(self.left_box.size()):
            res.append(self.left_box.get(index))
        return res

    def get_values_right(self):
        res = []
        for index in range(self.right_box.size()):
            res.append(self.right_box.get(index))
        return res
            
    def set_values_left(self, values):
        if not isinstance(values, (list, tuple)):
            values = [values]
        self.lv1.set(values)    

    def set_values_right(self, values):
        if not isinstance(values, (list, tuple)):
            values = [values]
        self.lv2.set(values)
        
            
            