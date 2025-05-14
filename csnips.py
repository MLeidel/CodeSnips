'''
csnips.py
Yet Another Snippet Program
Author: Leidel
Dec 2020

To Run:
    > python3 path/csnips.py
'''
from tkinter import *
from tkinter.ttk import *  # defaults all widgets as ttk
from tkinter.font import Font
from tkinter import messagebox
import webbrowser
import sqlite3
import os
import sys
import subprocess
import threading
import pyperclip
from ttkthemes import ThemedTk  # ttkthemes is applied to all widgets
import iniproc

# DATABASE: csnips.db
# TABLE "snippet"
# "pkey"      TEXT NOT NULL UNIQUE
# "groupkey"  TEXT NOT NULL
# "snip"      TEXT NOT NULL


splash = '''

     ▗▄▄▖ ▗▄▄▖▄▄▄▄  ▄ ▄▄▄▄   ▄▄▄
    ▐▌   ▐▌   █   █ ▄ █   █ ▀▄▄
    ▐▌    ▝▀▚▖█   █ █ █▄▄▄▀ ▄▄▄▀
    ▝▚▄▄▖▗▄▄▞▘      █ █
                      ▀

            Version 1.0
'''

class Application(Frame):
    ''' main class This is the entry point for the application '''
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.pack(fill=BOTH, expand=True, padx=4, pady=8)
        self.font_, self.size_, self.fg_, self.bg_, self.browser_, \
        self.cursor_, self.tab_, self.auto_, self.literals_, \
        self.remarks_, self.numbers_ = iniproc.read("csnips.ini",
                                                    'font',
                                                    'fontsize',
                                                    'fg',
                                                    'bg',
                                                    'browser',
                                                    'cursorcolor',
                                                    'tabsize',
                                                    'autocopy',
                                                    'literals',
                                                    'remarks',
                                                    'numbers')

        self.create_widgets()
        self.db = sqlite3.connect('csnips.db')
        self.load_combobox()
        self.vcmbx.set("")
        self.opt_flg = False  # used in on_click_save
        # get csnips.ini values

    def create_widgets(self):
        ''' creates GUI for app '''

        # added sytle for buttons to keep uniform size
        style = Style()
        style.configure("TButton", width=11)

        frm_1 = Frame(self)
        frm_1.grid(row=1, column=1, padx=5, sticky='n')  # fix at top

        lf = LabelFrame(frm_1, text=" Group ")
        lf.grid(row=1, column=1, padx=8)

        self.vcmbx = StringVar()
        self.cmbx = Combobox(lf, textvariable=self.vcmbx, width=10)
        self.cmbx.pack()
        self.cmbx.focus()
        self.cmbx.bind("<<ComboboxSelected>>", self.on_cmbx_selected)

        self.vent_snip_id = StringVar()
        ent_snip_id = Entry(frm_1, textvariable=self.vent_snip_id, width=12)
        ent_snip_id.grid(row=2, column=1, sticky='ew', pady=8)

        btn_go = Button(frm_1, text='Options', command=self.on_click_options)
        btn_go.grid(row=3, column=1, pady=8)

        btn_close = Button(frm_1, text='Close', command=self.save_location)
        btn_close.grid(row=4, column=1, pady=15)

        # LISTBOX AREA

        self.lst_snip = Listbox(self, bd=0,
                                width=15,
                                bg="dimgray",
                                fg="white",
                                highlightthickness=0,
                                selectbackground='#fff',
                                activestyle='dotbox')
        self.lst_snip.grid(row=2, column=1, rowspan=2, sticky='nsew')

        self.lst_snip.bind("<<ListboxSelect>>", self.on_click_snippet_list)


        self.lst_scrolly = Scrollbar(self, orient=VERTICAL, command=self.lst_snip.yview)
        self.lst_scrolly.grid(row=2, column=2, rowspan=2, sticky='nsw')  # use N+S+E
        self.lst_snip['yscrollcommand'] = self.lst_scrolly.set

        # CODE SNIPPET AREA

        self.code = Text(self, padx=5)
        self.code.grid(row=1, column=4, rowspan=3, sticky='nsew')
        self.efont = Font(family=self.font_, size=self.size_)
        self.code.config(font=self.efont)
        self.code.config(wrap=NONE,
                         relief=FLAT,
                         bg=self.bg_,
                         fg=self.fg_,
                         undo=True, # Tk 8.4
                         width=45,
                         height=12,
                         highlightthickness=0,
                         insertbackground=self.cursor_,
                         tabs=(self.efont.measure(' ' * int(self.tab_)),)
                         )
        self.code.insert("1.0", splash)  # csnips dot picture
        self.code.edit_modified(False)

        self.code_scrolly = Scrollbar(self, orient=VERTICAL, command=self.code.yview)
        self.code_scrolly.grid(row=1, column=5, rowspan=3, sticky='nsw')  # use N+S+E
        self.code['yscrollcommand'] = self.code_scrolly.set

        self.code_scrollx = Scrollbar(self, orient=HORIZONTAL, command=self.code.xview)
        self.code_scrollx.grid(row=4, column=4, sticky='new')
        self.code['xscrollcommand'] = self.code_scrollx.set

        self.code.tag_configure("literals", foreground=self.literals_)
        self.code.tag_configure("remarks", foreground=self.remarks_)
        self.code.tag_configure("multrem", foreground=self.remarks_)
        self.code.tag_configure("numbers", foreground=self.numbers_)

        # MAKE COLUMN 6 ITS OWN FRAME

        frm = Frame(self)
        frm.grid(row=1, column=6, rowspan=4, sticky='n')

        btn_select_all = Button(frm, text='Clear', command=self.on_click_clear)
        btn_select_all.grid(row=1, column=1, pady=5)

        btn_copy = Button(frm, text='Copy', command=self.on_click_copy)
        btn_copy.grid(row=2, column=1, padx=5, pady=(5, 25))

        btn_save = Button(frm, text='Save', command=self.on_click_save)
        btn_save.grid(row=3, column=1, pady=5)

        btn_delete = Button(frm, text='Delete', command=self.on_click_delete)
        btn_delete.grid(row=4, column=1, pady=5)

        self.vcb_auto = IntVar()
        cb_auto = Checkbutton(frm, variable=self.vcb_auto, text='Auto Copy')
        cb_auto.grid(row=5, column=1, pady=5)
        if self.auto_ == "on":
            self.vcb_auto.set(1)  # default to un-checked
        else:
            self.vcb_auto.set(0)


        # Bindings
        self.code.bind('<Control-s>', self.on_click_save)
        root.bind('<Control-a>', self.select_all)
        root.bind('<Control-q>', self.save_location)
        self.code.bind("<Button-3>", self.on_right_click)

        self.columnconfigure(4, weight=1)
        #self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1, pad=20)

        self.highlite()  # starts off syntax highliting

    # EVENT HANDLER FUNCTIONS

    def select_all(self, e=None):
        ''' handles ctrl-a for the code text widget '''
        self.code.tag_add(SEL, '1.0', END)
        self.code.mark_set(INSERT, '1.0')
        self.code.see(INSERT)

    def on_click_options(self, e=None):
        ''' load the csnips.ini content into the code text area '''
        self.opt_flg = True
        self.vent_snip_id.set("")
        with open("csnips.ini") as f:
            txt = f.read()
        self.code.delete("1.0", END)
        self.code.insert("1.0", txt)
        self.code.edit_modified(False)

    def on_click_clear(self, e=None):
        ''' Clear the code snippet text area '''
        if self.check_Exit() is False:
            return
        self.code.delete("1.0", END)
        self.code.focus()
        self.code.edit_modified(False)

    def on_cmbx_selected(self, e=None):
        ''' Load up list box with group members '''
        if self.check_Exit() is False:
            return
        self.opt_flg = False  # options flag OFF
        grp_id = self.vcmbx.get()
        cursor = self.db.execute("SELECT * from snippet where groupkey='{}' \
                                 order by pkey".format(grp_id))
        self.lst_snip.delete(0, 'end')
        for inx, item in enumerate(cursor):
            self.lst_snip.insert(inx, item[0])
        self.code.delete("1.0", END)  # clear the code text area
        self.code.edit_modified(False)

    def on_click_snippet_list(self, e=None):
        ''' get the snippet code and display it '''
        if self.check_Exit() is False:
            return
        self.opt_flg = False  # options 'Save' flag OFF
        grp_id = self.vcmbx.get()
        list_item = self.lst_snip.curselection()
        try:  # executes when ListBox looses focus causing an Exception
            snip_key = self.lst_snip.get(list_item[0])
        except Exception:
            return
        cursor = self.db.execute("SELECT * from snippet where \
                                 groupkey='{}' and pkey='{}'".format(grp_id, snip_key))
        snip_key, grp_id, snip_code = cursor.fetchone()
        self.vent_snip_id.set(snip_key)
        self.code.delete("1.0", END)
        self.code.insert("1.0", snip_code)
        self.code.edit_modified(False)
        # Auto Copy
        if self.vcb_auto.get() == 1:
            pyperclip.copy(snip_code)

    def on_click_copy(self):
        '''
        Copy the selected snippet code into clipboard
        If nothing is selected copy all text into clipboard
        '''
        if self.code.tag_ranges("sel"):
            snip_code = self.code.selection_get()
        else:
            snip_code = self.code.get("1.0", END)
        pyperclip.copy(snip_code)

    def on_click_save(self, e=None):
        ''' Update current or Insert new snippet '''
        if self.opt_flg is True:
            with open("csnips.ini", "w") as f:
                txt = self.code.get("1.0", END).rstrip() + "\n"
                f.write(txt)
            self.code.delete("1.0", END)
            self.code.insert("1.0", "Parameters Saved.\nClick 'Options' to Edit.")
            self.refresh_code_text_options()
            self.opt_flg = False
            self.code.edit_modified(False)
            self.start_display("Saved - Options")
            return
        grp_id = self.vcmbx.get()
        snip_key = self.vent_snip_id.get()
        snip_code = self.code.get("1.0", END).rstrip() + "\n"  # remove extra whitespace

        if snip_key == "" or grp_id == "":
            messagebox.showwarning("Warning", "Missing key fields")
            return

        cursor = self.db.execute("SELECT * from snippet where \
                                 groupkey='{}' and pkey='{}'".format(grp_id, snip_key))
        try:
            if cursor.fetchone() is None:
                # None - new snippet
                self.db.execute("INSERT INTO snippet VALUES (?, ?, ?)", [snip_key, grp_id, snip_code])
                self.db.commit()
                self.load_combobox()
                self.vcmbx.set(grp_id)
                self.load_snippet_list()  # reload the snippet listbox
            else:
                # update snippet
                self.db.execute("UPDATE snippet SET snip=? \
                                where groupkey=? and pkey=?", [snip_code, grp_id, snip_key])
                self.db.commit()
        except Exception as e:
            messagebox.showerror("Duplicate Snippet Key", e)
            return
        self.code.edit_modified(False)
        self.start_display("Saved - " + snip_key)

    def on_right_click(self, e=None):
        ''' launch selected text in webbrowser '''
        if self.code.tag_ranges("sel"):
            txt = self.code.selection_get()
        else:
            return
        # this works with HTML URLs or Files and PDFs
        subprocess.call([self.browser_, "https://www.google.com/search?q=" + txt])

    def on_click_delete(self):
        ''' Delete the group or current snippet from the snippet db '''
        if self.opt_flg is True:  # check options flag OFF
            return
        grp_id = self.vcmbx.get()
        snip_key = self.vent_snip_id.get()
        if grp_id == snip_key:  # deleting entire group
            resp = messagebox.askokcancel('Confirm Delete', 'Delete Group ' + snip_key + "?")
            if resp is False:
                return
            self.db.execute("DELETE FROM snippet where groupkey='{}'".format(grp_id))
            self.db.commit()
            self.load_combobox()  # reload the group keys combobox
            self.code.delete("1.0", END)
            self.vent_snip_id.set("")
        else:  # deleting the current snippet
            resp = messagebox.askokcancel('Confirm Delete', 'Is OK to delete ' + snip_key + "?")
            if resp is False:
                return
            self.db.execute("DELETE FROM snippet where \
                            groupkey='{}' and pkey='{}'".format(grp_id, snip_key))
            self.db.commit()
            self.load_snippet_list()  # reload the snippet listbox
            self.code.delete("1.0", END)
            self.vent_snip_id.set("")


    # HELPER FUNCTIONS

    def load_combobox(self):
        ''' Fill combo box with all the group keys '''
        groups = []
        cursor = self.db.execute("SELECT distinct groupkey from snippet order by groupkey")
        for item in cursor:
            groups.append(item)
        self.cmbx['values'] = groups
        self.cmbx.current(0)  # set start selection

    def load_snippet_list(self, e=None):
        ''' Load up list box with group members '''
        grp_id = self.vcmbx.get()
        cursor = self.db.execute("SELECT * from snippet where groupkey='{}' \
                                 order by pkey".format(grp_id))
        self.lst_snip.delete(0, 'end')
        for inx, item in enumerate(cursor):
            self.lst_snip.insert(inx, item[0])

    def stop_display(self):
        ''' Handle "Saved" message timeout '''
        root.title("CSnips")

    def start_display(self, txt):
        ''' Put up "Saved" message and set timeout '''
        root.title("CSnips - " + txt)
        t = threading.Timer(2.5, self.stop_display)  # after 2.5 seconds, change back the window title
        t.start()

    def refresh_code_text_options(self):
        ''' Refreshes the snippet code text configuration based on new ini settings '''
        self.font_, self.size_, self.fg_, self.bg_, \
        self.cursor_, self.tab_, self.auto_, self.literals_, \
        self.remarks_, self.numbers_ = iniproc.read("csnips.ini",
                                                    'font',
                                                    'fontsize',
                                                    'fg',
                                                    'bg',
                                                    'cursorcolor',
                                                    'tabsize',
                                                    'autocopy',
                                                    'literals',
                                                    'remarks',
                                                    'numbers')

        efont = Font(family=self.font_, size=self.size_)
        self.code.config(font=efont,
                         bg=self.bg_,
                         fg=self.fg_,
                         insertbackground=self.cursor_,
                         tabs=(self.efont.measure(' ' * int(self.tab_)),)
                         )
        self.code.tag_configure("literals", foreground=self.literals_)
        self.code.tag_configure("remarks", foreground=self.remarks_)
        self.code.tag_configure("multrem", foreground=self.remarks_)
        self.code.tag_configure("numbers", foreground=self.numbers_)

    def save_location(self, e=None):
        ''' executes at WM_DELETE_WINDOW event '''
        if self.code.edit_modified():
            resp = messagebox.askokcancel('Edits Not Saved', 'OK to Exit or Cancel')
            if resp is False:
                return
        with open("winfo", "w") as fout:
            fout.write(root.geometry())
        root.destroy()

    def check_Exit(self, e=None):
        ''' Prompt the user if Edit has modified text '''
        resp = True
        if self.code.edit_modified():
            resp = messagebox.askokcancel('Edits Not Saved', 'OK to Leave this Edit?')
        return resp

    def highlite(self):
        global t
        self.highlight_pattern(r"(\d+|\d\.\d|\.\d)", "numbers", regexp=True)
        self.highlight_pattern(r"[\"\']((?:.|\n)*?)[\'\"]",
                               "literals", regexp=True)
        self.highlight_pattern(r"(#.*|//.*)\n", "remarks", regexp=True)
        self.highlight_pattern(r"(/\*|\'\'\')((?:.|\n)*?)(\*/|\'\'\')",
                               "multrem", regexp=True)

        t = threading.Timer(1, self.highlite)  # every 1.5 seconds
        t.daemon=True  # for threading runtime error
        t.start()

    def highlight_pattern(self, pattern, tag, start="1.0", end="end", regexp=False):
        start = self.code.index(start)
        end = self.code.index(end)
        self.code.tag_remove(tag, start, end)
        self.code.mark_set("matchStart", start)
        self.code.mark_set("matchEnd", start)
        self.code.mark_set("searchLimit", end)

        count = IntVar()
        while True:
            index = self.code.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=True)
            if index == "": break
            if count.get() == 0: break # degenerate pattern which matches zero-length strings
            self.code.mark_set("matchStart", index)
            self.code.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.code.tag_add(tag, "matchStart", "matchEnd")

# ---------------------------------------------------


def _save_location(e=None):
    resp = messagebox.askokcancel('Exit Requested', 'Do you want to Exit the App?')
    if resp is False:
        return
    with open("winfo", "w") as fout:
        fout.write(root.geometry())
    root.destroy()

# root = Tk()
# Requires ttkthemes module
# 'alt', 'scidsand', 'classic', 'scidblue',
# 'scidmint', 'scidgreen', 'default', 'scidpink',
# 'arc', 'scidgrey', 'scidpurple', 'clam', 'smog'
# 'kroc', 'black', 'clearlooks'
# 'radiance', 'blue' : https://wiki.tcl-lang.org/page/List+of+ttk+Themes
root = ThemedTk(theme="black")
root.configure(bg="dimgray")

p = os.path.realpath(__file__)
os.chdir(os.path.dirname(p))

if os.path.isfile("winfo"):
    with open("winfo") as f:
        lcoor = f.read()
    root.geometry(lcoor.strip())
else:
    root.geometry("700x225")  # start dimentions


root.title("CSnips")
root.protocol("WM_DELETE_WINDOW", _save_location)
Sizegrip(root).place(rely=1.0, relx=1.0, x=0, y=0, anchor=SE)
root.resizable(True, True) #  (width, height) no resize & removes maximize button
root.minsize(700, 225)
root.iconphoto(True, PhotoImage(file='yasnip_icon.png'))
# root.attributes("-topmost", True)  # Keep on top of other windows
app = Application(root)
app.mainloop()
