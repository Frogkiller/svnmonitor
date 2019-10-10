import configparser
import datetime
import os
import tkinter as tk
from collections import OrderedDict
from getpass import getpass
from tkinter import ttk

import pysvn

configfile_name = "config.ini"


def get_creds(realm, username, may_save):
    pas = getpass()
    usr = get_username()
    return True, usr, pas, False

def get_username():
    config = configparser.ConfigParser()
    config.read(configfile_name)
    return config['defaults']['username']


def ssl_server_trust_prompt(trust_dict):
    return True, trust_dict["failures"], False


def get_logs(repo, number):
    client = pysvn.Client()
    client.callback_get_login = get_creds
    client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt

    log = client.log(
        repo,
        discover_changed_paths=True,
        limit=number
    )
    return log


def startup():
    config = configparser.ConfigParser()
    if os.path.isfile(configfile_name):
        config.read(configfile_name)
    return config


def create_tree(where):
    tree = ttk.Treeview(where)
    tree['show'] = 'headings'
    tree["columns"] = ('revision', 'author', 'date', 'message')
    tree.column('message', minwidth=0, width=700)
    tree.column('revision', minwidth=0, width=70)
    tree.column('author', minwidth=0, width=70)
    tree.column('date', minwidth=0, width=120)
    for column in tree["columns"]:
        tree.heading(column, text=column.capitalize())
    return tree


def create_file_tree(where):
    tree = ttk.Treeview(where)
    tree['show'] = 'headings'
    tree["columns"] = ('action', 'files')
    tree.column('action', minwidth=0, width=50)
    tree.column('files', minwidth=0, width=700)
    for column in tree["columns"]:
        tree.heading(column, text=column.capitalize())
    return tree


class Engine():
    def __init__(self, config):
        self.config = config

        self.top = tk.Tk()

        self.repo_lbl = tk.Label(self.top, text='SVN url: ')
        self.repo_lbl.grid(row=0, column=0)
        self.repo_val = tk.StringVar(value=self.config['defaults']['svn'])
        self.repo_txt = tk.Entry(self.top, textvariable=self.repo_val, width=100)
        self.repo_txt.grid(row=0, column=1, columnspan=2)

        self.rev_lbl = tk.Label(self.top, text='Revision: ')
        self.rev_lbl.grid(row=1, column=0)
        self.rev_val = tk.StringVar()
        self.rev_txt = tk.Entry(self.top, textvariable=self.rev_val)
        self.rev_txt.grid(row=1, column=1)
        self.rev_btn = tk.Button(self.top, text='Update', command=self.updater)
        self.rev_btn.grid(row=1, column=2)

        self.tr = create_tree(self.top)
        self.tr.bind("<Double-1>", self.refresh_files)
        self.tr.grid(row=2, column=0, columnspan=3)

        self.files = create_file_tree(self.top)
        self.files.grid(row=3, column=0, columnspan=3)

        self.data = OrderedDict()

    def fill_data_from_log(self, log):
        self.data.clear()
        for x in log:
            self.data[x.revision.number] = {'author': x.author, 'date': datetime.datetime.fromtimestamp(x.date),
                                            'message': x.message, 'revision': x.revision.number,
                                            'files': x.changed_paths}

    def fill_tree_with_data(self):
        self.tr.delete(*self.tr.get_children())
        for x, y in self.data.items():
            self.tr.insert('', 'end', iid=x)
            self.tr.set(x, column=0, value=x)
            self.tr.set(x, column=1, value=y['author'])
            self.tr.set(x, column=2, value=y['date'].strftime('%d-%m-%Y %H:%M'))
            self.tr.set(x, column=3, value=y['message'].replace('\n', ' '))

    def fill_files_view(self, files):
        self.files.delete(*self.files.get_children())
        for x in sorted(files, key=lambda z: z.path):
            self.files.insert('', 'end', values=(x.action,x.path))

    def refresh_files(self, event):
        val = self.tr.identify_row(event.y)
        if val is not '':
            self.fill_files_view(self.data[int(val)]['files'])


    def start(self):
        self.top.mainloop()

    def updater(self):
        log = get_logs(self.repo_val.get(), int(self.rev_val.get()))
        self.fill_data_from_log(log)
        self.fill_tree_with_data()


def main():
    config = configparser.ConfigParser()
    #todo: add config.ini creation when it's not present.
    config.read(configfile_name)
    eng = Engine(config)
    eng.start()


main()
