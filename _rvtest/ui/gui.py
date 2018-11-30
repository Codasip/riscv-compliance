# Copyright (c) 2018, Codasip Ltd.
# See LICENSE file for license details.

try:
    from tkinter import *
    from tkinter import messagebox, filedialog
    from tkinter.ttk import Combobox
    from _rvtest.ui.widgets import *
except (ModuleNotFoundError, ImportError):
    import sys
    sys.stderr.write("Tkinter module not installed, GUI is not available.\n")
    sys.exit(1)

import math
import os

from PIL.ImageTk import PhotoImage# import ImageTk

from _rvtest import ISAS, RiscVExtensions, PlatformProperties, MemoryProperties, \
    Modes, Causes, CSRS
from _rvtest.exceptions import ConfigError
from _rvtest.ui.ui_utils import Interface
from _rvtest.plugin_generator import PLUGIN_TARGETS

images = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')


class RVComplianceGUI(Tk):
    # Window dimensions 
    WIDTH = 800
    HEIGHT = 600
    
    # Default widget styles
    
    # Menu item style while its inactive 
    INACTIVE_COLOR = {'bg': '#273272', 'fg': 'white', 'font': ('Helvetica', 12, 'bold')}
    # Menu item style while its active
    ACTIVE_COLOR = {'bg': '#273272', 'fg': '#f7b217', 'font': ('Helvetica', 12, 'bold')}
    
    BACKGROUND_COLOR = '#273272'
    FOREGROUD_COLOR = 'white'
    FONT_TEXT = ('Helvetica', 10)
    FONT_CAPTION = ('Helvetica', 12, 'bold')
    
    # Button and other widgets styles
    STYLE_WIDGETS = {'bg': '#273272', 'fg': 'white', 'font': ('Helvetica')}
    STYLE_CHECKBUTTONS = {'bg': '#273272', 'font': ('Helvetica'), 'activebackground': '#273272', 
                          'highlightthickness': 0, 'bd': 0, 'fg': 'white', 'activeforeground': 'white'}
    STYLE_CHECKBUTTON_CHECKED = {'selectcolor': '#273272'}
    STYLE_CHECKBUTTON_UNCHECKED = {'selectcolor': 'white'}
    STYLE_CAPTIONS = {'bg': '#273272', 'fg': '#f7b217', 'font': ('Helvetica', 12, 'bold')}
    
    def __init__(self, *args, **kwargs):
        super(RVComplianceGUI, self).__init__(*args, **kwargs)
        self.interface = Interface()
        self._steps = []
        self._current_step = 0
        # When using tkinter variables, they cannot be created as local variables,
        # because garbage collector would destroy them immediately, so we need 
        # to store these varibles somewhere to keep the reference.
        self._vars = []
        self._default_target = 'default'
        self._target = None
        self._create_layout()
    
    def _create_layout(self):
        
        self.title("RISC-V Compliance Testsuite plugin generator")
        self.geometry('%dx%d' % (self.WIDTH, self.HEIGHT))
        self.resizable(False, False)
        
        # Create basic widget layout
        self._frame_header = Canvas(self)
        self._frame_content = Canvas(self)
        self._frame_footer = Canvas(self)
        
        self._frame_header.config(bg='white', height=0.1 * self.HEIGHT, width=self.WIDTH)
        
        header_image = os.path.join(images, 'risc_square_small.png')
        #self._image_header = PhotoImage(data=header_image)
        self._image_header = PhotoImage(file=header_image)
        background_label = Label(self._frame_header, bg='white', image=self._image_header)
        background_label.place(x=130, y=0)
        
        self._frame_header.create_text(450, 30, fill="#273272", font="Times 20 italic bold",
                        text="Plugin generator for Compliance Framework")
        
        self._frame_content.config(bg='red', height=0.8 * self.HEIGHT, width=self.WIDTH)

        self._frame_menu = Canvas(self._frame_content)
        # self._frame_menu.config(bg='green', height=0.8*self.HEIGHT, width=0.3*self.WIDTH)
        self._frame_menu.config(bg='#273272', height=0.8 * self.HEIGHT, width=0.3 * self.WIDTH)
        
        self._frame_body = Canvas(self._frame_content)
        self._frame_body.config(bg='blue', height=0.8 * self.HEIGHT, width=0.7 * self.WIDTH)
            
        self._frame_footer.config(bg='white', height=0.1 * self.HEIGHT, width=self.WIDTH)
        
        self._frame_header.pack()
        self._frame_content.pack()
        self._frame_menu.pack(side=LEFT)
        self._frame_body.pack(side=RIGHT)
        self._frame_footer.pack()
        
        # Wizard step creation, each step has (caption, widget and id)
        self._add_step("Introduction", self._step_introduction(), 'intro')
        self._add_step("ISA, Extensions and Modes", self._step_isa_extensions(), 'isa')
        self._add_step("Memory and interrupts", self._step_memory_interrupts(), 'memory')
        self._add_step("Interrupt vectors", self._step_causes(), 'causes')
        self._add_step("Control and State Registers", self._step_control_registers(), 'csrs')
        self._add_step("Target", self._step_target(), 'target')
        self._add_step("Finish", self._step_finish(), 'finish')
     
        self._render_steps()
        
        self.previous = Button(self._frame_footer, text='Previous', width=6, command=lambda: self._set_active_step(self._current_step - 1))
        self.previous.place(relx=0.7, rely=0.25)
                
        self.next = Button(self._frame_footer, text='Next', width=6, command=lambda: self._set_active_step(self._current_step + 1))
        self.next.place(relx=0.8, rely=0.25)

        self.cancel = Button(self._frame_footer, text='Cancel', width=6, command=self.destroy)
        self.cancel.place(relx=0.9, rely=0.25)        
        
        self._set_active_step(0)
    
    def _add_caption(self, parent, text, **kwargs):
        """
        General method for adding a caption to any widget.
        
        :param parent: Widget which should be captioned.
        :param text: Caption text.
        :param kwargs: Additional style arguments for caption.
        """
        for k, v in self.STYLE_CAPTIONS.items():
            kwargs.setdefault(k, v)

        header = Label(parent, text=text, **kwargs)
        header.place(relx=0.5, rely=0.05, anchor=CENTER)
    
    def _add_description(self, parent, text, **kwargs):
        """
        General method for adding description to any widget.
        This is used for creating description of GUI steps. 
        
        :param parent: Widget which should be descripted.
        :param text: Description text.
        :param kwargs: Additional style arguments for description.
        """        
        for k, v in self.STYLE_WIDGETS.items():
            kwargs.setdefault(k, v)
        
        description = Text(parent, wrap='word', **kwargs)
        description.insert("1.0", text)
        description.config(borderwidth=0, state='disabled', highlightthickness=0, bd=0)
        description.place(relx=0.1, rely=0.1)
        
    def _add_label(self, widget, text, x=None, y=None, **kwargs):
        """
        General method for adding a label to any widget.
        
        :param parent: Widget which should be labeled.
        :param text: Label text.
        :param kwargs: Additional style arguments for label.
        """
        x = x if x else widget.winfo_x()
        y = y if y else widget.winfo_y()
        
        for k, v in self.STYLE_WIDGETS.items():
            kwargs.setdefault(k, v)

        label = Label(widget.master, text=text, **kwargs)
        label.place(x=x, y=y)
    
    def _add_step(self, label, content, name, position=None):
        """Register new step.
        
        :param label: Label which is displayed on the left menu.
        :param content: Widget which is shown when registered step is active.
        :param name: Step ID.
        :param position: Step position. By default it is appended. First step's 
                        position is 0.
        """
        if position is None:
            position = len(self._steps)
        self._steps.insert(position, (label, content, name))
    
    def get_step(self, name):
        """Search for step by its name."""
        for step in self._steps:
            if step[2] == name:
                return step
    
    # Step widgets
    def _step_introduction(self, caption="Introduction"):
        """First step - introduction"""
        width = int(self._frame_body['width'])
        height = int(self._frame_body['height'])
        
        widget = Canvas(self._frame_body, height=height, width=width, bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption)
        description = "Welcome to plugin generator."
        self._add_description(widget, description, width=int(0.12 * width), height=int(0.05 * height))
        
        return widget

    def _step_isa_extensions(self, caption="ISA, Extensions and Modes"):
        width = int(self._frame_body['width'])
        height = int(self._frame_body['height'])
        
        widget = Canvas(self._frame_body, height=height, width=width, bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption)
        description = 'Choose instruction set architecture, supported extensions and modes.'
        self._add_description(widget, description, width=int(0.09 * width), height=int(0.008 * height))
        
        choices = ISAS.values()
        default = StringVar(self)
        default.set(choices[0])
        self._add_var(default)
        self._check_state(self.interface.add_property, PlatformProperties.ISA, choices[0])
        
        # ISA
        isa_selection = Combobox(widget, state='readonly', textvariable=default, values=choices)
        isa_selection.bind("<<ComboboxSelected>>", self._event_isa_changed)
        isa_selection.place(x=50, y=150)
        self._add_label(isa_selection, 'ISA', x=50, y=120, **self.STYLE_CAPTIONS)
        
        # Extensions
        extensions = Checkbar(widget, RiscVExtensions.values(), splitnum=5,
                              callback=self._event_extension_changed, **self.STYLE_CHECKBUTTONS)
        extensions.place(x=50, y=210)
        self._add_label(isa_selection, 'Extensions', x=50, y=190, **self.STYLE_CAPTIONS)
        
        # Modes
        modes = Checkbar(widget, [m.upper() for m in Modes.values()], splitnum=5,
                              callback=self._event_mode_changed, **self.STYLE_CHECKBUTTONS)
        modes.place(x=50, y=330)
        self._add_label(modes, 'Modes', x=50, y=310, **self.STYLE_CAPTIONS)

        return widget
    
    def _step_memory_interrupts(self, caption="Memory and Interrupts"):
        width = int(self._frame_body['width'])
        height = int(self._frame_body['height'])
        
        widget = Canvas(self._frame_body, height=height, width=width, bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption)
        
        description = 'Set memory configuration and interrupt support'
        self._add_description(widget, description, width=int(0.09 * width), height=int(0.008 * height))
        
        opts = {'size': "Memory size [MB]:",
                'program': "Program start:",
                'data': "Data start:"
                }
        
        x = 180
        y = 150
        off = 40
        for id, label in opts.items():
            v = StringVar()
            e = Entry(widget, name='memory_' + id, textvariable=v)
            e.place(x=x, y=y)
            y += off
            
            self._add_label(e, label, x - 140, y - 40)
        
        var1 = IntVar()
        has_interrupts = Checkbutton(widget, variable=var1, name='interrupts', 
                                     **self.STYLE_CHECKBUTTONS)
        has_interrupts.var = var1 
        has_interrupts.place(x=x, y=y)
        has_interrupts.bind('<ButtonPress>', self._event_interrupts)
        self._add_label(has_interrupts, 'Interrupt support:', x - 140, y)
        
        y += off
        
        var2 = IntVar()
        has_unaligned = Checkbutton(widget, variable=var2, name='misaligned',
                                    **self.STYLE_CHECKBUTTONS)
        has_unaligned.var = var2
        has_unaligned.place(x=x, y=y)
        has_unaligned.bind('<ButtonPress>', self._event_misaligned)
        self._add_label(has_unaligned, 'Misaligned memory:', x - 140, y)
        
        return widget
    
    def _step_causes(self, caption="Interrupt vectors"):
        width = int(self._frame_body['width'])
        height = int(self._frame_body['height'])
        
        widget = Canvas(self._frame_body, height=height, width=width, bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption, width=int(0.12 * width), height=int(0.05 * height))
        description = 'Set implemented causes'
        self._add_description(widget, description)

        self._causes_listbox = DualListBox(widget)
        self._causes_listbox.set_values_left(Causes.values())
        self._causes_listbox.place(x=100, y=150)
        
        return widget
    
    def _step_control_registers(self, caption="Control State Registers"):
        width = int(self._frame_body['width'])
        height = int(self._frame_body['height'])
                
        widget = Canvas(self._frame_body, height=height, width=width, bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption, width=int(0.12 * width), height=int(0.05 * height))
        description = 'Set implemented control and state registers'
        self._add_description(widget, description)
        
        self._csrs_listbox = DualListBox(widget)
        self._csrs_listbox.set_values_left(CSRS.values())
        self._csrs_listbox.place(x=100, y=150)
        
        return widget   

    def _step_target(self, caption="Target"):
        widget = Canvas(self._frame_body, height=self._frame_body['height'], width=self._frame_body['width'], bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption)
        description = 'Target'
        self._add_description(widget, description)
        
        choices = PLUGIN_TARGETS
        choices.remove(self._default_target)
        choices.insert(0, self._default_target)
        
        default = StringVar(self)
        default.set(choices[0])
        self._add_var(default)

        # Targets
        target_selection = Combobox(widget, state='readonly', textvariable=default, values=choices)
        target_selection.bind("<<ComboboxSelected>>", self._event_target_changed)
        target_selection.place(x=50, y=150)
        self._add_label(target_selection, 'Target', x=50, y=120, **self.STYLE_CAPTIONS)
        
        return widget
    
    def _step_finish(self, caption="Finish"):
        widget = Canvas(self._frame_body, height=self._frame_body['height'], width=self._frame_body['width'], bg=self.BACKGROUND_COLOR)
        self._add_caption(widget, caption)
        description = 'Finish'
        self._add_description(widget, description)
        
        self._destination = StringVar()
        self._entry_path = Entry(widget, width=40, textvariable=self._destination)
        self._entry_path.place(x=60, y=150)
        dialog_button = Button(widget, text="Browse", command=self._browse_button)
        dialog_button.place(x=400, y=145) 
        
        return widget
    
    def _browse_button(self):
        filename = filedialog.askdirectory()
        self._destination.set(filename)
            
    def _render_steps(self):
        self._step_widgets = []
        x = 20
        y = 50
        offset = 40
        for label, content, _ in self._steps:
            l = Label(self._frame_menu, text=label, **self.INACTIVE_COLOR)
            l.place(x=x, y=y)
            y += offset
            self._step_widgets.append(l)
    
    def _check_memory(self):
        mem_size = None
        program_start = None
        data_start = None
        
        parent = self.get_step('memory')[1]
        for child in parent.winfo_children():
            if self._get_widget_id(child) == 'size':
                mem_size = child.get()
            if self._get_widget_id(child) == 'program':
                program_start = child.get() 
            if self._get_widget_id(child) == 'data':
                data_start = child.get() 
      
        return self._check_state(self.interface.add_property, PlatformProperties.MEMORY_RANGE,
                                (mem_size, program_start, data_start))
    
    def _set_active_step(self, position):
        # Clicked on Next button
        if position > self._current_step:
            success = True
            # Perform check actions for current step
            if self._steps[self._current_step][2] == 'memory':
                success = self._check_memory()
            elif self._steps[self._current_step][2] == 'causes':
                values = self._causes_listbox.get_values_right() 
                if values:
                    success = self._check_state(self.interface.add_property, PlatformProperties.CAUSE, values)
            elif self._steps[self._current_step][2] == 'csrs':
                values = self._csrs_listbox.get_values_right() 
                if values:
                    success = self._check_state(self.interface.add_property, PlatformProperties.CSR, values)                    
            if not success:
                return    

        if position <= 0:
            self.previous.config(state='disabled')
            self.next.config(text='Next')
        elif position == len(self._steps) - 1:
            self.previous.config(state='normal')
            self.next.config(text='Generate!')
        elif position > len(self._steps) - 1:
            destination = self._destination.get()
            if not destination:
                messagebox.showwarning("Invalid destination", "Please select plugin destination")
                return
            try:
                self.interface.generator.generate(destination, self._target)
            except Exception as e:
                messagebox.showerror("PluginGenerator error", str(e))
            else:
                messagebox.showinfo("Complete", f"Plugin successfully generated to {destination}")
        else:
            self.previous.config(state='normal')
            self.next.config(text='Next')
        
        if position < 0 or position >= len(self._steps):
            return
        # Hide current
        self._step_widgets[self._current_step].config(**self.INACTIVE_COLOR)
        self._steps[self._current_step][1].pack_forget()
        # Show desired
        self._step_widgets[position].config(**self.ACTIVE_COLOR)
        self._steps[position][1].pack()
        # Update step
        self._current_step = position
    
    def _set_checkbutton_color(self, widget, value):
        style = self.STYLE_CHECKBUTTON_CHECKED if value else self.STYLE_CHECKBUTTON_UNCHECKED
        widget.configure(**style)
         
    def _get_widget_id(self, widget):
        child_name = str(widget).split('.')[-1]
        if '_' in child_name:
            return child_name.split('_')[1]
        return child_name
    
    def _check_state(self, method, *args, **kwargs):
        
        try:
            method(*args, **kwargs)
        except ConfigError as e:
            messagebox.showerror("Configuration Error", str(e))
            return False
        except (AssertionError, TypeError, ValueError) as e:
            messagebox.showerror("Unexpected error", "Unexpected error: "+str(e))
            return False             
        return True
            
    def _add_var(self, variable):
        self._vars.append(variable)
        
    # Event handlers
    def _event_isa_changed(self, event):
        self._check_state(self.interface.add_property, PlatformProperties.ISA, event.widget.get())

    def _event_extension_changed(self, event):
        # Variable event still hold old value, so we 
        # need to negate the value
        value = not event.widget.var.get()
        self._set_checkbutton_color(event.widget, value)
        extension = self._get_widget_id(event.widget)
        if value:
            self._check_state(self.interface.add_property, PlatformProperties.EXTENSION, extension)
        else:
            self._check_state(self.interface.remove_property, PlatformProperties.EXTENSION, extension)
            
    def _event_mode_changed(self, event):
        # Variable event still hold old value, so we 
        # need to negate the value
        value = not event.widget.var.get()
        self._set_checkbutton_color(event.widget, value)
        mode = self._get_widget_id(event.widget).upper()
        if value:
            self._check_state(self.interface.add_property, PlatformProperties.MODE, mode)
        else:
            self._check_state(self.interface.remove_property, PlatformProperties.MODE, mode)
   
    def _event_interrupts(self, event):
        # Variable event still hold old value, so we 
        # need to negate the value
        value = not event.widget.var.get()
        self._set_checkbutton_color(event.widget, value)
        self._check_state(self.interface.add_property, PlatformProperties.INTERRUPT_SUPPORT, value)

    def _event_misaligned(self, event):
        # Variable event still hold old value, so we 
        # need to negate the value
        value = not event.widget.var.get()
        self._set_checkbutton_color(event.widget, value)
        self._check_state(self.interface.add_property, PlatformProperties.MEMORY_MISALIGNED, value)
    
    # Event handlers
    def _event_target_changed(self, event):
        self._target = event.widget.get()

    
def main():
    gui = RVComplianceGUI()
    gui.mainloop()


if __name__ == '__main__':
    main()
