# Based on example functions listed in EDMC Plugin Documentation:
# https://github.com/Marginal/EDMarketConnector/blob/master/PLUGINS.md

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

VERSION = '0.02a'

this = sys.modules[__name__]	# For holding module globals
status = tk.StringVar()

def plugin_start(plugin_dir):
    """
    Load this plugin into EDMC
    """
    sys.stderr.write("Plugin loaded from: {}".format(plugin_dir.encode("utf-8")))
    #print "Plugin loaded from: {}".format(plugin_dir.encode("utf-8"))
    return 'ATEL'

def plugin_prefs(parent):
    PADX = 10  # formatting
    frame = nb.Frame(parent)
    frame.columnconfigure(5, weight=1)
    HyperlinkLabel(frame, text='ATEL GitHub', background=nb.Label().cget('background'),
                   url='https://github.com/Elite-IGAU/ATEL-EDMC', underline=True).grid(columnspan=2, padx=PADX, sticky=tk.W)
    nb.Label(frame, text="ATEL {VER}".format(
        VER=VERSION)).grid(columnspan=2, padx=PADX, sticky=tk.W)
    #
    # Todo - Add option to defer ATEL transmission until docked and cartographic data is sold.
    #
    return frame

def plugin_app(parent):
    """
    Create a pair of TK widgets for the EDMC main window
    """
    this.parent = parent
    this.frame = tk.Frame(parent)
    this.frame.columnconfigure(2, weight=1)
    this.lblstatus = tk.Label(this.frame, anchor=tk.W, textvariable=status, wraplengt=200)
    this.lblstatus.grid(row=0, column=1, sticky=tk.W)
    status.set("[ATEL] Waiting for COVAS feed...")
    return this.frame

def journal_entry(cmdr, is_beta, system, station, entry, state):

    if entry['event'] == 'FSDJump':
        # We arrived at a new system!
        if 'StarPos' in entry:
            sys.stderr.write("Arrived at {} ({},{},{})\n".format(entry['StarSystem'], *tuple(entry['StarPos'])))
            status.set("Arrived at {} ({},{},{})\n".format(entry['StarSystem'], *tuple(entry['StarPos'])))
        else:
            sys.stderr.write("Arrived at {}\n".format(entry['StarSystem']))
            status.set("Arrived at {} ({},{},{})\n".format(entry['StarSystem']))

def plugin_stop():
    """
    EDMC is closing
    """
    sys.stderr.write("Shutting down.")
