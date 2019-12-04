###############################################################################
# A simple EDMC plugin to automatically transmit CodexEntry data from the
# CMDR journal to the Intergalactic Astronomical Union for record keeping,
# and scientific purposes.
#
# Discoveries DO NOT have CMDR data attached to them unless a CMDR chooses to
# submit a public Astronomical Telegram - a short "postcard" style anouncement
# to immediately announce UNIQUE discoveries which are automatically
# sent to IGAU by this plugin.
#
# ATEL notices are available at:
# https://elite-dangerous-iau.fandom.com/wiki/Galactic_Bureau_for_Astronomical_Telegrams
#
# Data Catalog available at:
# https://raw.githubusercontent.com/Elite-IGAU/publications/master/IGAU_Codex.csv
#
# Source Code availble for review at:
# https://github.com/Elite-IGAU/ATEL-EDMC
#
# DATA COLLECTION NOTICE:
# IGAU only stores the following data:
# discovery date/time, discovery name, and discovery location.
# IGAU does NOT store any "Personally Identifiable Information" (PII) in our
# public discovery catalog.
#
# Please submit bug reports or issues at:
# https://github.com/Elite-IGAU/ATEL-EDMC/issues
#
# Special thanks to:
#
# Otis B. EDMC (http://edcodex.info/?m=tools&entry=150) for EDMC plugin docs
# (DISC)Sajime and (Mobius) Odyssey for their assistance and suggestions.
#
# The many wonderful explorers that make the Intergalactic Astronomical Union
# [IGAU] a productive and enjoyable Elite Dangerous PVE squadron.
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
this.status = tk.StringVar()
this.ts = time.time()
this.jd = this.ts / 86400 + 2440587.5
VERSION = '1.08'
IGAU_GITHUB = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/load.py"
IGAU_GITHUB_LATEST_VERSION = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/version.txt"
IGAU_API = "https://ddss70885k.execute-api.us-west-1.amazonaws.com/Prod"
IGAU_WIKI = "https://elite-dangerous-iau.fandom.com/api.php"
PADX = 10  # formatting

def plugin_start(plugin_dir):
    check_version()
    return 'ATEL'

def plugin_prefs(parent):
    frame = nb.Frame(parent)
    frame.columnconfigure(5, weight=1)
    v = requests.get(url = IGAU_GITHUB_LATEST_VERSION)
    CURRENT_VERSION = str(v.text)
    nb.Label(frame, text="ATEL-EDMC {VER}".format(VER=VERSION)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    nb.Label(frame, text="Latest ATEL-EDMC version: {CURRENT_VERSION}".format(CURRENT_VERSION=CURRENT_VERSION)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    return frame

def check_version():
    response = requests.get(url = IGAU_GITHUB_LATEST_VERSION)
    serverVersion = response.content.strip()
    if serverVersion > VERSION:
        upgrade_callback()

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
                msginfo = ['ATEL-EDMC Upgrade has completed sucessfully.',
                           'Please close and restart EDMC']
                tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))

        else:
            msginfo = ['ATEL-EDMC Upgrade failed. Bad server response',
                       'Please try again']
            tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))
    except:
        msginfo = ['ATEL-EDMC Upgrade encountered a problem.',
                   'Please try again, and restart if problems persist']
        tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))

def dashboard_entry(cmdr, is_beta, entry):
    this.cmdr = cmdr

def bulletin_callback():
    # update the current time, otherwise ATEL notices will all have the same timestamp
    this.ts = time.time()
    this.jd = this.ts / 86400 + 2440587.5
    # I guess the only way to get this to work is to embrace the icky JSON fad.
    ATEL_DATA = {
        'action': 'edit',
        'title': 'GBET '+str(jd)+': '+this.system,
        'text': 'At time index: '+this.timestamp+', '+this.cmdr+' reports '+this.name+' in system '+this.system+' via ATEL-EDMC ( Version '+VERSION+' ).'+'[[Category:' + 'GBET'+ ']]',
        'token': '+\\',
        'format': 'json'
    }

    ATEL_POST = requests.post(IGAU_WIKI, data=ATEL_DATA)
    this.status.set("ATEL "+str(jd)+" Transmitted")

def plugin_app(parent):
    this.parent = parent
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(2, weight=1)
    this.lblstatus = tk.Label(this.frame, anchor=tk.W, textvariable=status, wraplengt=200)
    this.lblstatus.grid(row=0, column=1, sticky=tk.W)
    # The ATEL Submit function can't initialize until we read the current system
    # from an 'FSDJump' journal event.  TODO: See if EDMC exposes "system" like it does "CMDR"
    # we set the status below to let users know the plugin is loaded. 
    this.status.set("ATEL-EDMC Version "+VERSION +" [ACTIVE]")
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):
#############################
# What we're really after are unique discoveries.
    if entry['event'] == 'CodexEntry':
        # We discovered something!
            this.cmdr = cmdr
            entry['commanderName'] = cmdr
            # send journal strings to database endpoint:
            this.name=(format(entry['Name_Localised']))
            this.system=(format(entry['System']))
            this.timestamp=(format(entry['timestamp']))
            DATA_STR = '{{ "timestamp":"{}", "Name_Localised":"{}", "System":"{}" }}'.format(entry['timestamp'], entry['Name_Localised'], entry['System'])
            r = requests.post(url = IGAU_API, data = DATA_STR)

            # Submit ATEL Button if CMDR wants to make a public discovery announcement.
            # Updated wording to be more clear as to what people should be submitting.
            this.status.set("Scan something interesting? \n [NSP] [Bio] [Geo] [Non-Human] ")
            nb.Button(frame, text="[Submit ATEL Report]", command=bulletin_callback).grid(row=10, column=0,
            columnspan=2, padx=PADX, sticky=tk.W)
    else:
        # FSDJump happens often enough to clear the status window
            if entry['event'] == 'FSDJump':
                # We arrived at a new system!
                    this.cmdr = cmdr
                    entry['commanderName'] = cmdr
                    this.system=(format(entry['StarSystem']))
                    this.timestamp=(format(entry['timestamp']))
                    # We use "Unscanned Phenomena" as a generic discovery type
                    # for systems with unsual or unknown phenomena that the CMDR didn't (or couldn't) scan.
                    this.name = 'Unscanned Phenomena'
                    # Submit ATEL Button if CMDR wants to make a public discovery announcement.
                    # Updated wording to be more clear as to what people should be submitting.
                    this.status.set("Scan something interesting? \n [NSP] [Bio] [Geo] [Non-Human] ")
                    nb.Button(frame, text="[Submit ATEL Report]", command=bulletin_callback).grid(row=10, column=0,
                    columnspan=2, padx=PADX, sticky=tk.W)

def plugin_stop():
    sys.stderr.write("Shutting down.")
