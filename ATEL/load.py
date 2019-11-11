###############################################################################
# A simple EDMC plugin to automatically transmit CodexEntry data from the
# CMDR journal to the Intergalactic Astronomical Union for record keeping,
# and scientific purposes.
#
# Discoveries DO NOT have CMDR data attached to them unless a CMDR chooses to
# submit a public Astronomical Telegram - a short "postcard" style anouncement
# which can be used to immediately announce UNIQUE discoveries above and beyond
# normal Codex (geysers, lava spouts, terraformable HMC's, etc.) discoveries
# which are autmoatically sent to IGAU by this plugin
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
VERSION = '1.02'
IGAU_GITHUB = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/load.py"
IGAU_GITHUB_LATEST_VERSION = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/version.txt"
IGAU_API = "https://ddss70885k.execute-api.us-west-1.amazonaws.com/Prod"
IGAU_WIKI = "https://elite-dangerous-iau.fandom.com/api.php"
PADX = 10  # formatting

def plugin_start(plugin_dir):
    return 'ATEL'

def plugin_prefs(parent):
    frame = nb.Frame(parent)
    frame.columnconfigure(5, weight=1)
    HyperlinkLabel(frame, text='ATEL GitHub', background=nb.Label().cget('background'),
                   url='https://github.com/Elite-IGAU/ATEL-EDMC/tree/latest', underline=True).grid(columnspan=2, padx=PADX, sticky=tk.W)
    v = requests.get(url = IGAU_GITHUB_LATEST_VERSION)
    if int(VERSION) == int(v):
        nb.Label(frame, text="ATEL {VER}".format(VER=VERSION)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    else:
        nb.Label(frame, text="ATEL {v}".format(v=v) ."available. Please upgrade.").grid(columnspan=2, padx=PADX, sticky=tk.W)
    return frame

#def upgrade_callback():
    #
    # disabled - pending rewite to do this automagically.
    #
    #this_fullpath = os.path.realpath(__file__)
    #this_filepath, this_extension = os.path.splitext(this_fullpath)
    #corrected_fullpath = this_filepath + ".py"
    #try:
    #    response = requests.get(IGAU_GITHUB)
    #    if (response.status_code == 200):
    #        with open(corrected_fullpath, "wb") as f:
    #            f.seek(0)
    #            f.write(response.content)
    #            f.truncate()
    #            f.flush()
    #            os.fsync(f.fileno())
    #            this.upgrade_applied = True  # Latch on upgrade successful
    #            msginfo = ['Upgrade has completed sucessfully.',
    #                       'Please close and restart EDMC']
    #            tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))

    #    else:
    #        msginfo = ['Upgrade failed. Bad server response',
    #                   'Please try again']
    #        tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))
    #except:
    #    msginfo = ['Upgrade encountered a problem.',
    #               'Please try again, and restart if problems persist']
    #    tkMessageBox.showinfo("Upgrade status", "\n".join(msginfo))

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
        'category': 'GBET',
        'text': 'At time index: '+this.timestamp+', '+this.cmdr+' reports '+this.name+' in system '+this.system+' via ATEL-EDMC ( Version '+VERSION+' ).',
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
    # we will do a version check here since this is the first status box that appears.
    v = requests.get(url = IGAU_GITHUB_LATEST_VERSION)
    if int(VERSION) == int(v):
        this.status.set("ATEL-EDMC Version "+VERSION +" [ACTIVE]")
    else:
        this.status.set("ATEL-EDMC Version "+v +" available. Please Upgrade.")
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):
#############################
# What we're really after are unique discoveries. TODO: Filter out "mundane"
# CodexEntry events for stuff like Y-Type Dwarfs, HMC's, etc. These will generate
# a CodexEntry event the first time a CMDR encounters one in a sector.
#
# Not an urgent fix because the data isn't entirely worthless.
# (Black Holes, ELW's, WD/NS Herbigs, CS, are of interest.)

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

            #Submit ATEL Button if CMDR wants to make a public discovery announcement.
            this.status.set("Discover something interesting? \n  Click the button below to report it!")
            nb.Button(frame, text="[Transmit ATEL]", command=bulletin_callback).grid(row=10, column=0,
            columnspan=2, padx=PADX, sticky=tk.W)
    else:
        # FSDJump happens often enough to clear the status window
            if entry['event'] == 'FSDJump':
                # We arrived at a new system!
                    this.cmdr = cmdr
                    entry['commanderName'] = cmdr
                    this.system=(format(entry['StarSystem']))
                    this.timestamp=(format(entry['timestamp']))
                    # Since we don't know what "name" is unless we have a
                    # CodexEntry event, we use "Unknown Entity" as a generic
                    # discovery type for systems with unsual or unknown phenomena
                    this.name = 'Unknown Entity'

                    #Submit ATEL Button if CMDR wants to make a public discovery announcement.
                    this.status.set("Discover something interesting? \n  Click the button below to report it!")
                    nb.Button(frame, text="[Transmit ATEL]", command=bulletin_callback).grid(row=10, column=0,
                    columnspan=2, padx=PADX, sticky=tk.W)

def plugin_stop():
    sys.stderr.write("Shutting down.")
