from tkinter import *
from tkinter import ttk

import utils
import ColonyLifeSim

class ParamSetupGUI(Frame):
    """docstring for ParamSetupGUI"""
    def __init__(self, parent):
        super(ParamSetupGUI, self).__init__()

        self.parent = parent

        self.ui_elements = []

        self.update_thread = utils.LoopingThread(target=self.update)

        self.initUI()

        self.update_thread.start()

    def initUI(self):
        self.master.title("Colony Life Setup")
        self.pack(fill=BOTH, expand=True)

        _column = 0
        _row    = 0

        _column = 0; _row += 1;
        self.submit_button = Button(self, text="Launch!", command=self.run_app)
        self.ui_elements.append(self.submit_button)
        self.submit_button.grid(column=_column, row=_row, columnspan=6)

    def update(self):
        super(ParamSetupGUI, self).update()

    def run_app(self):

        self.update_thread.stop()
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

    main_window.mainloop()

if __name__ == '__main__':
    main()