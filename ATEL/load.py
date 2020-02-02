###############################################################################
# A simple EDMC plugin to automatically transmit CodexEntry data from the
# CMDR journal to the Intergalactic Astronomical Union for record keeping,
# and scientific purposes.
#
# CMDR's may also (optionally) submit a public Astronomical Telegram
# Short "postcard" style anouncements used to immediately (and publicly)
# announce UNIQUE discoveries.
#
# ATEL notices are available at:
# https://github.com/Elite-IGAU/publications/tree/master/ATEL
#
# Data Catalog available at:
# https://raw.githubusercontent.com/Elite-IGAU/publications/master/IGAU_Codex.csv
#
# Source Code availble for review at:
# https://github.com/Elite-IGAU/ATEL-EDMC
#
# Please submit bug reports or issues at:
# https://github.com/Elite-IGAU/ATEL-EDMC/issues
#
# Special thanks to:
#
# Otis B. EDMC (http://edcodex.info/?m=tools&entry=150) for EDMC plugin docs
# (DISC) Sajime, (Mobius) Odyssey, (Fuel Rats) Absolver, and the entire EDCD
# community for assistance, suggestions, and testing.
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

this = sys.modules[__name__]	# For holding module globals
this.status = tk.StringVar()
this.edsm_setting = None
this.installed_version = 1.29
this.github_latest_version = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/version.txt"
this.plugin_source = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/load.py"
this.api = "https://ddss70885k.execute-api.us-west-1.amazonaws.com/Prod"
this.atel = "https://01ixzg9ifh.execute-api.us-west-1.amazonaws.com/Prod"
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
    HyperlinkLabel(frame, text='Wiki', background=nb.Label().cget('background'), url='https://elite-dangerous-iau.fandom.com\n', underline=True).grid(padx=PADX, sticky=tk.W)
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

def bulletin_callback():
    # update the current time, otherwise ATEL notices will all have the same timestamp
    this.ts = time.time()
    this.jd = this.ts / 86400 + 2440587.5
    #this.jd_str = str(jd)

    ATEL_POST = requests.post(this.atel, data=ATEL_DATA)
    ATEL_DATA = '{{ "timestamp":"{}", "Name_Localised":"{}", "System":"{}", "app_name":"{}", "app_version":"{}", "cmdr":"{}", "jd":"{}"}}'.format(entry['timestamp'], entry['Name_Localised'], entry['System'], entry['app_name'], entry['installed_version'], entry['cmdr'], entry['jd_str'])
    this.status.set("TEST ATEL "+str(jd)+" Logged \n ")
    #this.status.set("ATEL "+str(jd)+" Transmitted \n "+this.name)
    # The print statements below can be uncommented to debug data transmission issues.
    # Log file located at: \user_name\AppData\Local\Temp\EDMarketConnector.log
    print(str(this.atel))
    print(str(ATEL_DATA))
    print(str(ATEL_POST.request.body))
    print(str(ATEL_POST.text))
    # We don't issue forget(this.b1) in case there are multiple CodexEvents to report.
    # FSDJump event will clear the button.

def forget(widget):
    widget.grid_forget()

def retrieve(widget):
    widget.grid(row=10, column=0, columnspan=2, padx=PADX)

def plugin_app(parent):
    this.parent = parent
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(2, weight=1)
    this.lblstatus = tk.Label(this.frame, anchor=tk.W, textvariable=status, wraplengt=255)
    this.lblstatus.grid(row=0, column=1, sticky=tk.W)
    this.status.set("Waiting for Codex discovery data...")
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):

    if entry['event'] == 'CodexEntry':

        # Define variables to be passed along to submit ATEL Function
        this.timestamp=(format(entry['timestamp']))
        this.cmdr = cmdr
        entry['commanderName'] = cmdr
        this.name=(format(entry['Name_Localised']))
        this.system=(format(entry['System']))
        # Apparently Python 3's requests library breaks json. Not surprised.
        # do this the old fashioned way (version 1.08) with artisinal, hand-crafted JSON BS.
        CODEX_DATA = '{{ "timestamp":"{}", "Name_Localised":"{}", "System":"{}" }}'.format(entry['timestamp'], entry['Name_Localised'], entry['System'])
        API_POST = requests.post(url = this.api, data = CODEX_DATA)
        # Submit ATEL Button if CMDR wants to make a public discovery announcement.
        # Added a value check - unless a CodexEntry event generates a Voucher from a composition scan, we don't offer the report button.
        # This prevents ATEL reports for "mundane" discoveries like standard gas giants, non-terraformables, brown dwarfs, etc.

        # enabling ATEL button for testing purposes
        this.b1 = nb.Button(frame, text="[Submit TEST ATEL]", command=bulletin_callback)
        retrieve(this.b1)

        #try:
        #    this.voucher=(format(entry['VoucherAmount']))
        #    this.status.set("Codex discovery data sent.\n "+this.name)
        #    this.b1 = nb.Button(frame, text="[Submit ATEL Report?]", command=bulletin_callback)
        #    retrieve(this.b1)
        #except KeyError:
        #    this.status.set("Codex discovery data sent.\n "+this.name)
            # The print statements below can be uncommented to debug data transmission issues.
            # Log file located at: \user_name\AppData\Local\Temp\EDMarketConnector.log
            #print(str(this.api))
            #print(str(CODEX_DATA))
            #print(str(API_POST.request.body))
            #print(str(API_POST.text))

    else:
        # FSDJump happens often enough to clear the status window
        if entry['event'] == 'FSDJump':
                this.cmdr = cmdr
                entry['commanderName'] = cmdr
                this.system=(format(entry['StarSystem']))
                this.timestamp=(format(entry['timestamp']))
                this.status.set("Waiting for Codex discovery data...")
                try:
                    forget(this.b1)
                except AttributeError:
                    this.status.set("Waiting for Codex discovery data...")

def plugin_stop():
    sys.stderr.write("Shutting down.")
