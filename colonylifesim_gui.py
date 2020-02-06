from tkinter import *
from tkinter import ttk

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
        self.submit_button = Button(self, text="Launch!", command=self.run_app)
        self.submit_button.grid(column=self._column, row=self._row, columnspan=1)

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
        except:
            pass

            

    def destroy(self):
        del self.numerical_entries[:]
        self.update_thread.stop()
        super(ParamSetupGUI, self).destroy()

    def run_app(self):
        self.destroy()
        self.parent.destroy()

        ColonyLifeSim.main()


def main():
    main_window = Tk()

    screen_width = main_window.winfo_screenwidth()
    screen_height = main_window.winfo_screenheight()

    mw_height, mw_width = int(screen_width/2), int(screen_height/2)
    # main_window.geometry("{}x{}+{}+{}".format(mw_height, mw_width, int(mw_height/2), int(mw_width/2)))
    main_window.geometry("+{}+{}".format(int(mw_height/2), int(mw_width/2)))
    main_window.resizable(False, False)

    app = ParamSetupGUI(main_window)

    def on_closing():
        app.destroy()
        main_window.destroy()

    main_window.protocol("WM_DELETE_WINDOW", on_closing)


    main_window.mainloop()

if __name__ == '__main__':
    main()