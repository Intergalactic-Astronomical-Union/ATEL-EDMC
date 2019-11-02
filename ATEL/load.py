###############################################################################
# A simple EDMC plugin to transmit CodexEntry data from the CMDR journal
# to the Intergalactic Astronomical Union for record keeping, and scientific
# purposes.
#
# Discoveries DO NOT have CMDR data attached to them unless a CMDR chooses to
# submit a public Astronomical Telegram - a short "postcard" style anouncement
# which can be used to immediately announce UNIQUE discoveries above and beyond
# normal discoveries (geysers, lava spouts, terraformable HMC's, water worlds, etc.)
#
# ATEL notices are available at:
# https://elite-dangerous-iau.fandom.com/wiki/Galactic_Bureau_for_Astronomical_Telegrams
#
# DATA COLLECTION NOTICE:
# IGAU only stores the following data:
# discovery date/time, discovery name, and discovery location.
#
# code availble for review at:
# https://github.com/Elite-IGAU/ATEL-EDMC
#
# please submit bug reports or issues at:
# https://github.com/Elite-IGAU/ATEL-EDMC/issues
#
# Special thanks to:
#
# Mobius PVE (https://elitepve.com/) for their assistance
# Otis B. EDMC (http://edcodex.info/?m=tools&entry=150)
# The many wonderful explorers that make the Intergalactic Astronomical Union
# a productive and enjoyable Elite Dangerous PVE squadron.
#
###############################################################################

import sys
import os
import ttk
import Tkinter as tk
import tkMessageBox
from ttkHyperlinkLabel import HyperlinkLabel
from config import applongname, appversion
import myNotebook as nb
import json
import requests
import zlib
import re
import webbrowser
from collections import defaultdict
import threading
import urllib2
import time

this = sys.modules[__name__]	# For holding module globals
status = tk.StringVar()
VERSION = '0.62b'
IGAU_GITHUB = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/load.py"
IGAU_API = "https://ddss70885k.execute-api.us-west-1.amazonaws.com/Prod"
IGAU_WIKI = "https://elite-dangerous-iau.fandom.com/api.php"
PADX = 10  # formatting
ts = time.time()
jd = ts / 86400 + 2440587.5

def plugin_start(plugin_dir):
    return 'ATEL'

def plugin_prefs(parent):
    frame = nb.Frame(parent)
    frame.columnconfigure(5, weight=1)
    HyperlinkLabel(frame, text='ATEL GitHub', background=nb.Label().cget('background'),
                   url='https://github.com/Elite-IGAU/ATEL-EDMC/tree/latest', underline=True).grid(columnspan=2, padx=PADX, sticky=tk.W)
    nb.Label(frame, text="ATEL {VER}".format(VER=VERSION)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    nb.Button(frame, text="UPGRADE", command=upgrade_callback).grid(row=10, column=0,
        columnspan=2, padx=PADX, sticky=tk.W)
    return frame

def upgrade_callback():
    this_fullpath = os.path.realpath(__file__)
    this_filepath, this_extension = os.path.splitext(this_fullpath)
    corrected_fullpath = this_filepath + ".py"
    try:
        response = requests.get(IGAU_GITHUB)
        if (response.status_code == 200):
            with open(corrected_fullpath, "wb") as f:
                f.seek(0)
                f.write(response.content)
                f.truncate()
                f.flush()
                os.fsync(f.fileno())
                this.upgrade_applied = True  # Latch on upgrade successful
                msginfo = ['Upgrade has completed sucessfully.',
                           'Please close and restart EDMC']
                tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))

        else:
            msginfo = ['Upgrade failed. Bad server response',
                       'Please try again']
            tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))
    except:
        msginfo = ['Upgrade encountered a problem.',
                   'Please try again, and restart if problems persist']
        tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))

def dashboard_entry(cmdr, is_beta, entry):
    this.cmdr = cmdr

def bulletin_callback():
    # Looks like the only way to get this to work is to embrce the icky JSON fad.
    ATEL_DATA = {
        'action': 'edit',
        'title': 'GBET '+str(jd)+': '+this.system,
        'category': 'GBET',
        'text': 'At time index: '+this.timestamp+', '+this.cmdr+' reports ' +this.name+' in system '+this.system+'',
        'token': '+\\',
        'format': 'json'
    }
    ATEL_POST = requests.post(IGAU_WIKI, data=ATEL_DATA)
    status.set("IGAU ATEL "+str(jd)+" Submitted")

def plugin_app(parent):
    this.parent = parent
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(2, weight=1)
    this.lblstatus = tk.Label(this.frame, anchor=tk.W, textvariable=status, wraplengt=200)
    this.lblstatus.grid(row=0, column=1, sticky=tk.W)
    status.set("Waiting for COVAS data...")
    #Submit ATEL Button
    nb.Button(frame, text="Submit IGAU ATEL (Discovery Report)", command=bulletin_callback).grid(row=10, column=0,
    columnspan=2, padx=PADX, sticky=tk.W)
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):
#############################
# What we're really after are unique discoveries.
    if entry['event'] == 'CodexEntry':
        # We discovered something!
            this.cmdr = cmdr
            entry['commanderName'] = cmdr
            status.set("{}: Discovered {} in {}\n".format(entry['timestamp'],entry['Name_Localised'],entry['System']))
            # data to be sent to api
            this.name=(format(entry['Name_Localised']))
            this.system=(format(entry['System']))
            this.timestamp=(format(entry['timestamp']))
            DATA_STR = '{{ "timestamp":"{}", "Name_Localised":"{}", "System":"{}" }}'.format(entry['timestamp'], entry['Name_Localised'], entry['System'])
            r = requests.post(url = IGAU_API, data = DATA_STR)
            # extracting response text
            db_response = r.text
            #Submit ATEL Button
            nb.Button(frame, text="Submit IGAU ATEL (Discovery Report)", command=bulletin_callback).grid(row=10, column=0,
            columnspan=2, padx=PADX, sticky=tk.W)
    else:
        # FSDJump happens often enough to clear the status window
            if entry['event'] == 'FSDJump':
                # We arrived at a new system!
                    status.set("Waiting for COVAS data...")
                    this.system=(format(entry['StarSystem']))
                    this.timestamp=(format(entry['timestamp']))
                    this.name = 'unknown entity'
                    #
                    #How do we clear the ATEL Button???
                    #nb.Button(frame, text="Submit IGAU ATEL (Discovery Report)", command=bulletin_callback).grid(row=10, column=0,
                    #columnspan=2, padx=PADX, sticky=tk.W)

def plugin_stop():
    sys.stderr.write("Shutting down.")
