###############################################################################
# A simple EDMC plugin to automatically transmit CodexEntry data from the
# CMDR journal to the Intergalactic Astronomical Union for record keeping,
# and scientific purposes.
#
# Data Catalog available at:
# https://raw.githubusercontent.com/Elite-IGAU/publications/master/IGAU_Codex.csv
#
# Please submit bug reports or issues at:
# https://github.com/Elite-IGAU/ATEL-EDMC/issues
#
# Special thanks to:
#
# The entire EDCD community for assistance, suggestions, and testing.
#
# The many wonderful explorers that make the Intergalactic Astronomical Union
# [IGAU] a productive and enjoyable Elite Dangerous PVE squadron.
#
###############################################################################

import sys
import os
import json
import requests
import urllib
import tkinter as tk
from tkinter import ttk
from ttkHyperlinkLabel import HyperlinkLabel
from tkinter import messagebox
import myNotebook as nb
import time
import re

this = sys.modules[__name__]	# For holding module globals
this.status = tk.StringVar()
this.edsm_setting = None
this.app_name = 'ATEL-EDMC'
this.installed_version = 1.34
this.github_latest_version = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/version.txt"
this.plugin_source = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/load.py"
this.api = "https://ddss70885k.execute-api.us-west-1.amazonaws.com/Prod"
PADX = 10  # formatting

def plugin_start3(plugin_dir):
    check_version()
    return 'ATEL'

def plugin_prefs(parent, cmdr, is_beta):
    frame = nb.Frame(parent)
    frame.columnconfigure(5, weight=1)
    response = requests.get(url = this.github_latest_version)
    this.latest_version = float(response.content.strip().decode('utf-8'))
    this.latest_version_str = str(this.latest_version)
    nb.Label(frame, text="ATEL-EDMC {INSTALLED}".format(INSTALLED=installed_version)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    nb.Label(frame, text="Latest ATEL-EDMC version: {latest_version_str}".format(latest_version_str=latest_version_str)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    HyperlinkLabel(frame, text='GitHub', background=nb.Label().cget('background'), url='https://github.com/Elite-IGAU/ATEL-EDMC\n', underline=True).grid(padx=PADX, sticky=tk.W)
    HyperlinkLabel(frame, text='Discord', background=nb.Label().cget('background'), url='https://discord.gg/2Qq37xt\n', underline=True).grid(padx=PADX, sticky=tk.W)
    HyperlinkLabel(frame, text='Web', background=nb.Label().cget('background'), url='https://elite-igau.github.io/\n', underline=True).grid(padx=PADX, sticky=tk.W)
    return frame

def check_version():
    response = requests.get(url = this.github_latest_version)
    this.latest_version = float(response.content.strip().decode('utf-8'))
    this.latest_version_str = str(this.latest_version)
    if this.latest_version > this.installed_version:
        upgrade_callback()

def upgrade_callback():
    this_fullpath = os.path.realpath(__file__)
    this_filepath, this_extension = os.path.splitext(this_fullpath)
    corrected_fullpath = this_filepath + ".py"
    try:
        response = requests.get(this.plugin_source)
        if (response.status_code == 200):
            with open(corrected_fullpath, "wb") as f:
                f.seek(0)
                f.write(response.content)
                f.truncate()
                f.flush()
                os.fsync(f.fileno())
                this.upgrade_applied = True  # Latch on upgrade successful
                msginfo = ['ATEL-EDMC Upgrade '+this.latest_version_str+' has completed sucessfully.',
                           'Please close and restart EDMC']
                messagebox.showinfo("Upgrade status", "\n".join(msginfo))
            sys.stderr.write("Finished ATEL-EDMC upgrade!\n")

        else:
            msginfo = ['ATEL-EDMC Upgrade failed. Bad server response',
            'Please try again']
            messagebox.showinfo("Upgrade status", "\n".join(msginfo))
    except:
        this.upgrade_applied = True  # Latch on upgrade successful
        msginfo = ['ATEL-EDMC Upgrade '+this.latest_version_str+' has completed sucessfully.',
                   'Please close and restart EDMC']
        messagebox.showinfo("Upgrade status", "\n".join(msginfo))

def dashboard_entry(cmdr, is_beta, entry):
    this.cmdr = cmdr

def plugin_app(parent):
    this.parent = parent
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(2, weight=1)
    this.lblstatus = tk.Label(this.frame, anchor=tk.W, textvariable=status, wraplengt=255)
    this.lblstatus.grid(row=0, column=1, sticky=tk.W)
    this.status.set("Waiting for Codex data...")
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):

    if entry['event'] == 'CodexEntry':
        this.timestamp=(format(entry['timestamp']))
        this.cmdr = cmdr
        entry['commanderName'] = cmdr
        this.entryid=(format(entry['EntryID']))
        this.name=(format(entry['Name']))
        this.name_stripped=(re.sub(";|\$|_Name", "", this.name))
        this.name_lower = str.lower(this.name_stripped)
        this.name_localised=(format(entry['Name_Localised']))
        this.system=(format(entry['System']))
        this.systemaddress=(format(entry['SystemAddress']))
        try:
            this.voucher=(format(entry['VoucherAmount']))
            CODEX_DATA = '{{ "timestamp":"{}", "EntryID":"{}", "Name":"{}", "Name_Localised":"{}", "System":"{}", "SystemAddress":"{}", "App_Name":"{}", "App_Version":"{}"}}'.format(entry['timestamp'], entry['EntryID'], this.name_lower, entry['Name_Localised'], entry['System'], entry['SystemAddress'], this.app_name, this.installed_version,)
            API_POST = requests.post(url = this.api, data = CODEX_DATA)
            this.status.set("Codex data sent!\n "+this.name_localised)
        except KeyError:
            this.status.set("Waiting for Codex data...")

    else:
        if entry['event'] == 'FSDJump':
                this.cmdr = cmdr
                entry['commanderName'] = cmdr
                this.system=(format(entry['StarSystem']))
                this.timestamp=(format(entry['timestamp']))
                this.status.set("Waiting for Codex data...")

def plugin_stop():
    sys.stderr.write("Shutting down.")
