from tkinter import *
from tkinter import ttk
from tkcolorpicker import askcolor
import pygame
import re

import utils
import ColonyLifeSim
import parameters as p


class ParamSetupGUI(Frame):
    """docstring for ParamSetupGUI"""
    def __init__(self, parent):
        super(ParamSetupGUI, self).__init__()

        self.parent = parent

        self.numerical_entries = []

        self.update_thread = utils.LoopingThread(target=self.update)

        self.initUI()

        self.update_thread.start()

    def initUI(self):
        self.master.title("Colony Life Setup")
        self.pack(fill=BOTH, expand=True)

        self._column = 0
        self._row    = -1

        self.add_dict_number_values_to_gui_as_line(p.parameters, "parameters")
        self.add_dict_number_values_to_gui_as_line(p.initial_params, "initial_params")
        self.add_dict_number_values_to_gui_as_line(p.sim_params, "sim_params")
        self.add_dict_number_values_to_gui_as_line(p.type2cost, "type2cost")
        self.add_dict_number_values_to_gui_as_line(p.type2cost_river, "type2cost_river")

        self.add_dict_colour_values_to_gui_as_line(p.type2color, "type2color")

        self.add_dict_number_values_to_gui_as_line(p.socialfeats_factors, "socialfeats_factors")

        self._column = 0; self._row += 1;
        # self.submit_button = Button(self, text="Launch!", command=self.run_app)
        # self.submit_button.grid(column=self._column, row=self._row, columnspan=1)

    def add_dict_number_values_to_gui_as_line(self, _dict, dict_name):
        self._column = 0; self._row += 1;

        """
        from Tkinter import *
        from ttk import *

        def on_field_change(index, value, op):
            print "combobox updated to ", c.get()

        root = Tk()
        v = StringVar()
        v.trace('w',on_field_change)
        c = Combobox(root, textvar=v, values=["foo", "bar", "baz"])
        c.pack()

        mainloop()
        """

        lbl1 = Label(self, text=dict_name + "[")
        cbb  = ttk.Combobox(self, values=list(_dict.keys()))
        cbb.set(list(_dict.keys())[0])
        lbl2 = Label(self, text="]  =  ")
        ent  = Entry(self)
        self.numerical_entries.append([_dict, cbb, ent])

        lbl1.grid(column=self._column, row=self._row, pady=6, sticky=E); self._column += 1;
        cbb .grid(column=self._column, row=self._row, pady=6);           self._column += 1;
        lbl2.grid(column=self._column, row=self._row, pady=6);           self._column += 1;
        ent .grid(column=self._column, row=self._row, pady=6);           self._column += 1;

    def add_dict_colour_values_to_gui_as_line(self, _dict, dict_name):
        pass

    def update(self):
        super(ParamSetupGUI, self).update()

        try:
            w = self.parent.focus_get()
            for _dict, combo, entry in self.numerical_entries:
                if not w is entry:
                    entry.delete(0, END)
                    entry.insert(END, _dict[combo.get()])
                else:
                    if type(_dict[combo.get()]) is int:
                        if _dict[combo.get()] != int(entry.get()):
                            _dict[combo.get()] = int(entry.get())
                    elif type(_dict[combo.get()]) is float:
                        if _dict[combo.get()] != float(entry.get()):
                            _dict[combo.get()] = float(entry.get())
        except Exception as e:
            print(e)
            pass

            

    def destroy(self):
        del self.numerical_entries[:]
        self.update_thread.stop()
        super(ParamSetupGUI, self).destroy()

    def run_app(self):
        self.destroy()
        self.parent.destroy()

        ColonyLifeSim.main()


class NumericalDictModificationTab(Frame):
    """docstring for DictModificationTab"""
    def __init__(self, parent, _dict):
        super(NumericalDictModificationTab, self).__init__()
        self._dict = _dict
        self.parent = parent

        self.numerical_entries = []

        self.update_thread = utils.LoopingThread(target=self.update)

        self.initUI()

        self.update_thread.start()

    def initUI(self):
        self._column = 0; self._row = -1;

        self.add_dict_to_gui()

    def add_dict_to_gui(self):
        for key in self._dict.keys():
            self._column = 0; self._row += 1;

            lbl1 = Label(self, text=key + " = ")
            ent  = Entry(self)
            self.numerical_entries.append([key, ent])

            lbl1.grid(column=self._column, row=self._row, pady=6, sticky=E); self._column += 1;
            ent .grid(column=self._column, row=self._row, pady=6, sticky=W); self._column += 1;



    def update(self):
        super(NumericalDictModificationTab, self).update()

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
            print(e)
            pass


    def destroy(self):
        del self.numerical_entries[:]
        self.update_thread.stop()
        super(NumericalDictModificationTab, self).destroy()

class ColorDictModificationTab(Frame):
    """docstring for DictModificationTab"""
    def __init__(self, parent, _dict):
        super(ColorDictModificationTab, self).__init__()
        self._dict = _dict
        self.parent = parent

        self.color_entries = []

        self.update_thread = utils.LoopingThread(target=self.update)

        self.initUI()

        self.update_thread.start()

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
            # print(c_rgb, c_hex, button["bg"], key)

    def update(self):
        super(ColorDictModificationTab, self).update()

    def destroy(self):
        del self.color_entries[:]
        self.update_thread.stop()
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


    # tab1 = NumericalDictModificationTab (main_window, p.parameters);          tabs.append(tab1);
    # tab2 = NumericalDictModificationTab (main_window, p.initial_params);      tabs.append(tab2);
    # tab3 = NumericalDictModificationTab (main_window, p.sim_params);          tabs.append(tab3);
    # tab4 = NumericalDictModificationTab (main_window, p.type2cost);           tabs.append(tab4);
    # tab5 = NumericalDictModificationTab (main_window, p.type2cost_river);     tabs.append(tab5);
    # tab6 = ColorDictModificationTab     (main_window, p.type2color);          tabs.append(tab6);
    # tab7 = NumericalDictModificationTab (main_window, p.socialfeats_factors); tabs.append(tab7);

    # tab_parent.add(tab1, text="parameters")
    # tab_parent.add(tab2, text="initial_params")
    # tab_parent.add(tab3, text="sim_params")
    # tab_parent.add(tab4, text="type2cost")
    # tab_parent.add(tab5, text="type2cost_river")
    # tab_parent.add(tab6, text="type2color")
    # tab_parent.add(tab7, text="socialfeats_factors")

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