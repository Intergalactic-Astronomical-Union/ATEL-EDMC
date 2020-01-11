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
# (DISC) Sajime, (Mobius) Odyssey, and (Fuel Rats) Absolver
# for their assistance and suggestions.
#
# The many wonderful explorers that make the Intergalactic Astronomical Union
# [IGAU] a productive and enjoyable Elite Dangerous PVE squadron.
#
###############################################################################

import sys
import os
import json
import requests
try:
    # Python 2
    from urllib2 import quote
    import Tkinter as tk
except ModuleNotFoundError:
    # Python 3
    from urllib.parse import quote
    import tkinter as tk
import myNotebook as nb
import time

this = sys.modules[__name__]	# For holding module globals
this.status = tk.StringVar()
this.edsm_setting = None
this.installed_version = '1.10'
this.github = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/load.py"
this.github_latest_version = "https://raw.githubusercontent.com/Elite-IGAU/ATEL-EDMC/latest/ATEL/version.txt"
this.api = "https://ddss70885k.execute-api.us-west-1.amazonaws.com/Prod"
this.wiki = "https://elite-dangerous-iau.fandom.com/api.php"
PADX = 10  # formatting

def plugin_start3(plugin_dir):
    return plugin_start()

def plugin_start():
    check_version()
    return 'ATEL'

def plugin_prefs(parent):
    frame = nb.Frame(parent)
    frame.columnconfigure(5, weight=1)
    response = requests.get(url = github_latest_version)
    latest_version = response.content.strip()
    nb.Label(frame, text="ATEL-EDMC {VER}".format(VER=installed_version)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    nb.Label(frame, text="Latest ATEL-EDMC version: {CURRENT_VERSION}".format(CURRENT_VERSION=latest_version)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    return frame

def check_version():
    response = requests.get(url = github_latest_version)
    latest_version = response.content.strip()
    if int(latest_version) > int(installed_version):
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

    # Fandom wiki API needs icky JSON.
    ATEL_DATA = {
        'action': 'edit',
        'title': 'GBET '+str(jd)+': '+this.system,
        'text': 'At time index: '+this.timestamp+', '+this.cmdr+' reports '+this.name+' in system '+this.system+' via ATEL-EDMC ( Version '+VERSION+' ).'+'[[Category:' + 'GBET'+ ']]',
        'token': '+\\',
        'format': 'json'
    }

    ATEL_POST = requests.post(wiki, data=ATEL_DATA)

    this.status.set("ATEL "+str(jd)+" Transmitted \n "+this.name)
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
        # embrace the JSON fad - code suggestion
        json_data = json.dumps([{"timestamp": format(entry['timestamp']), "Name_Localised": format(entry['Name_Localised']), "System": format(entry['System'])}])
        r = requests.post(url = api, json = json_data)
        # Submit ATEL Button if CMDR wants to make a public discovery announcement.
        # Added a value check - unless a CodexEntry event generates a Voucher from a composition scan, we don't offer the report button.
        try:
            this.voucher=(format(entry['VoucherAmount']))
            this.status.set("Codex discovery data sent.\n "+this.name)
            this.b1 = nb.Button(frame, text="[Submit ATEL Report?]", command=bulletin_callback)
            retrieve(this.b1)
        except KeyError:
            this.status.set("Codex discovery data sent.\n "+this.name)
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
