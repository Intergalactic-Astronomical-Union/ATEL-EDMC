###############################################################################
# A simple EDMC plugin to automatically transmit CodexEntry data from the
# CMDR journal to the Intergalactic Astronomical Union
# for record keeping, and scientific purposes.
#
# Data Catalog available at:
# https://github.com/Intergalactic-Astronomical-Union/publications
#
# Please Note: With EDDN and EDSM now carrying Codex data, IGAU will disable this
# plugin Dec 2023
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
import logging
from config import appname
# setting up logging
plugin_name = os.path.basename(os.path.dirname(__file__))
logger = logging.getLogger(f'{appname}.{plugin_name}')

this = sys.modules[__name__]	# For holding module globals
this.status = tk.StringVar()
this.edsm_setting = None
this.app_name = 'ATEL-EDMC'
this.installed_version = 1.60
this.github_latest_version = "https://raw.githubusercontent.com/Intergalactic-Astronomical-Union/ATEL-EDMC/latest/ATEL/version.txt"
this.plugin_source = "https://raw.githubusercontent.com/Intergalactic-Astronomical-Union/ATEL-EDMC/latest/ATEL/load.py"
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
    HyperlinkLabel(frame, text='Web', background=nb.Label().cget('background'), url='https://intergalactic-astronomical-union.github.io\n', underline=True).grid(padx=PADX, sticky=tk.W)
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
            logger.info("Finished ATEL-EDMC upgrade!\n")

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
    this.status.set("Plugin deprecated, please use EDDN")
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):
    if entry['event'] == 'FSDJump':
        this.timestamp=(format(entry['timestamp']))
        this.status.set("Plugin deprecated, please use EDDN")
    elif entry['event'] == 'FSSDiscoveryScan':
        this.timestamp = (format(entry['timestamp']))
        this.status.set("Plugin deprecated, please use EDDN")

def plugin_stop():
    logger.info("Shutting down.")
