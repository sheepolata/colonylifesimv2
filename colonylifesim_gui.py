from tkinter import *
from tkinter import ttk
from tkcolorpicker import askcolor
import pygame
import re

import utils
import ColonyLifeSim
import parameters as p


class NumericalDictModificationTab(Frame):
    """docstring for DictModificationTab"""
    def __init__(self, parent, _dict):
        super(NumericalDictModificationTab, self).__init__()
        self._dict = _dict
        self.parent = parent

        self.numerical_entries = []

        self.initUI()

    def initUI(self):
        self._column = 0; self._row = -1;

        self.add_dict_to_gui()

        self.after(200, self.update)

    def add_dict_to_gui(self):
        for key in self._dict.keys():
            self._column = 0; self._row += 1;

            lbl1 = Label(self, text=key + " = ")
            ent  = Entry(self)
            self.numerical_entries.append([key, ent])

            lbl1.grid(column=self._column, row=self._row, pady=6, sticky=E); self._column += 1;
            ent .grid(column=self._column, row=self._row, pady=6, sticky=W); self._column += 1;



    def update(self):
        try:
            w = self.parent.focus_get()
            for key, entry in self.numerical_entries:
                if not w is entry:
                    entry.delete(0, END)
                    entry.insert(END, self._dict[key])
                else:
                    if type(self._dict[key]) is int:
                        if self._dict[key] != int(entry.get()):
                            self._dict[key] = int(entry.get())
                    elif type(self._dict[key]) is float:
                        if self._dict[key] != float(entry.get()):
                            self._dict[key] = float(entry.get())
        except Exception as e:
            print("In .update of {}; 1st dict elmt is {}".format(type(self), list(self._dict.keys())[0]))
            print(type(e))    # the exception instance
            print(e.args)     # arguments stored in .args
            print(e)

        self.after(200, self.update)

    def destroy(self):
        del self.numerical_entries[:]
        # self.update_thread.stop()
        super(NumericalDictModificationTab, self).destroy()

class ColorDictModificationTab(Frame):
    """docstring for DictModificationTab"""
    def __init__(self, parent, _dict):
        super(ColorDictModificationTab, self).__init__()
        self._dict = _dict
        self.parent = parent

        self.color_entries = []

        self.initUI()

    def initUI(self):
        self._column = 0; self._row = -1;

        self.add_dict_to_gui()

    def add_dict_to_gui(self):
        for key in self._dict.keys():
            self._column = 0; self._row += 1;

            lbl1 = Label(self, text=key)
            lbl2 = Label(self, text=" = ")
            ent  = Button(self, text="            ")
            ent.configure(command=lambda button=ent, k=key: self.pick_color_command(button, k))
            ent.configure(bg='#%02x%02x%02x' % tuple(self._dict[key][:3]))
            self.color_entries.append([key, ent])

            lbl1.grid(column=self._column, row=self._row, pady=6, sticky=E);   self._column += 1;
            lbl2.grid(column=self._column, row=self._row, pady=6, sticky=E+W); self._column += 1;
            ent .grid(column=self._column, row=self._row, pady=6, sticky=E+W); self._column += 1;


    def pick_color_command(self, button, key):
        c = askcolor(color=button["bg"])
        c_rgb, c_hex = c

        if c != None:
            self._dict[key] = c_rgb
            button.configure(bg=c_hex)

    def destroy(self):
        del self.color_entries[:]
        super(ColorDictModificationTab, self).destroy()

def main():
    main_window = Tk()

    screen_width = main_window.winfo_screenwidth()
    screen_height = main_window.winfo_screenheight()

    mw_height, mw_width = int(screen_width/2), int(screen_height/2)
    # main_window.geometry("{}x{}+{}+{}".format(mw_height, mw_width, int(mw_height/2), int(mw_width/2)))
    main_window.geometry("+{}+{}".format(int(mw_height/2), int(mw_width/2)))
    main_window.resizable(False, False)

    tab_parent = ttk.Notebook(main_window)

    tabs = []

    for _name in p.all_dict.keys():
        t = None
        if p.all_dict[_name][1] == "num":
            t = NumericalDictModificationTab (main_window, p.all_dict[_name][0]);
        elif p.all_dict[_name][1] == "color":
            t = ColorDictModificationTab (main_window, p.all_dict[_name][0]);
        if t != None:
            # _display_name = _name.split("_")
            _lname = re.split("_|2", _name)
            _lname_final = []
            for w in _lname:
                _lname_final.append(w[0].upper() + w[1:])
            _display_name = ""
            for w in _lname_final:
                _display_name += w + " "
            _display_name = _display_name.strip()
            tab_parent.add(t, text=_display_name)
            tabs.append(t);

    tab_parent.grid()

    def run_app():
        for t in tabs:
            t.destroy()
        tab_parent.destroy()
        main_window.destroy()

        ColonyLifeSim.main()

    submit_button = Button(main_window, text="Launch!", command=run_app)
    submit_button.grid()

    def on_closing():
        for t in tabs:
            t.destroy()
        tab_parent.destroy()
        main_window.destroy()

        pygame.quit()

    main_window.protocol("WM_DELETE_WINDOW", on_closing)


    main_window.mainloop()

if __name__ == '__main__':
    main()