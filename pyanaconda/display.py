#
# display.py:  graphical display setup for the Anaconda GUI
#
# Copyright (C) 2016
# Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s):  Martin Kolman <mkolman@redhat.com>
#
import os
import subprocess
import time

from pyanaconda.i18n import _

import logging
log = logging.getLogger("anaconda")
stdoutLog = logging.getLogger("anaconda.stdout")

from pyanaconda import constants
from pyanaconda import iutil
from pyanaconda import vnc
from pyanaconda.flags import flags
from pyanaconda import isys
from pyanaconda import startup_utils

import blivet

# Spice

def start_spice_vd_agent():
    status = iutil.execWithRedirect("spice-vdagent", [])
    if status:
        log.info("spice-vdagent exited with status %d", status)
    else:
        log.info("Started spice-vdagent.")

# X11

def start_x11():

    # Start Xorg and wait for it become ready
    iutil.startX(["Xorg", "-br", "-logfile", "/tmp/X.log",
                  ":%s" % constants.X_DISPLAY_NUMBER, "vt6", "-s", "1440", "-ac",
                  "-nolisten", "tcp", "-dpi", "96",
                  "-noreset"], output_redirect=subprocess.DEVNULL)

# function to handle X startup special issues for anaconda
def do_startup_x11_actions():
    """Start window manager"""
    # When metacity actually connects to the X server is unknowable, but
    # fortunately it doesn't matter. metacity does not need to be the first
    # connection to Xorg, and if anaconda starts up before metacity, metacity
    # will just take over and maximize the window and make everything right,
    # fingers crossed.
    # Add XDG_DATA_DIRS to the environment to pull in our overridden schema
    # files.
    datadir = os.environ.get('ANACONDA_DATADIR', '/usr/share/anaconda')
    if 'XDG_DATA_DIRS' in os.environ:
        xdg_data_dirs = datadir + '/window-manager:' + os.environ['XDG_DATA_DIRS']
    else:
        xdg_data_dirs = datadir + '/window-manager:/usr/share'

    childproc = iutil.startProgram(["metacity", "--display", ":1", "--sm-disable"],
                                   env_add={'XDG_DATA_DIRS': xdg_data_dirs})
    iutil.watchProcess(childproc, "metacity")

def set_x_resolution(runres):
    try:
        log.info("Setting the screen resolution to: %s.", runres)
        iutil.execWithRedirect("xrandr", ["-d", ":1", "-s", runres])
    except RuntimeError:
        log.error("The X resolution was not set")
        iutil.execWithRedirect("xrandr", ["-d", ":1", "-q"])

def do_extra_x11_actions(runres, display_mode):
    """Perform X11 actions not related to startup"""
    if runres and display_mode == 'g' and not flags.usevnc:
        set_x_resolution(runres)

    # Load the system-wide Xresources
    iutil.execWithRedirect("xrdb", ["-nocpp", "-merge", "/etc/X11/Xresources"])

    start_spice_vd_agent()

# general display startup

def setup_display(anaconda, options, addons=None):
    from pyanaconda.ui.tui.simpleline import App
    from pyanaconda.ui.tui.spokes.askvnc import AskVNCSpoke
    from pykickstart.constants import DISPLAY_MODE_TEXT
    from pyanaconda.nm import nm_is_connected, nm_is_connecting
    from blivet import arch

    graphical_failed = 0
    vncS = vnc.VncServer()          # The vnc Server object.
    vncS.anaconda = anaconda

    anaconda.displayMode = options.display_mode
    anaconda.isHeadless = arch.is_s390()

    if options.vnc:
        flags.usevnc = True
        anaconda.displayMode = 'g'
        vncS.password = options.vncpassword

        # Only consider vncconnect when vnc is a param
        if options.vncconnect:
            cargs = options.vncconnect.split(":")
            vncS.vncconnecthost = cargs[0]
            if len(cargs) > 1 and len(cargs[1]) > 0:
                if len(cargs[1]) > 0:
                    vncS.vncconnectport = cargs[1]

    if options.xdriver:
        anaconda.xdriver = options.xdriver
        anaconda.writeXdriver(root="/")

    if flags.rescue_mode:
        return

    if anaconda.ksdata.vnc.enabled:
        flags.usevnc = True
        anaconda.displayMode = 'g'

        if vncS.password == "":
            vncS.password = anaconda.ksdata.vnc.password

        if vncS.vncconnecthost == "":
            vncS.vncconnecthost = anaconda.ksdata.vnc.host

        if vncS.vncconnectport == "":
            vncS.vncconnectport = anaconda.ksdata.vnc.port

    if anaconda.displayMode == "g":
        import pkgutil
        import pyanaconda.ui

        mods = (tup[1] for tup in pkgutil.iter_modules(pyanaconda.ui.__path__, "pyanaconda.ui."))
        if "pyanaconda.ui.gui" not in mods:
            stdoutLog.warning("Graphical user interface not available, falling back to text mode")
            anaconda.displayMode = "t"
            flags.usevnc = False
            flags.vncquestion = False

    # disable VNC over text question when not enough memory is available
    if blivet.util.total_memory() < isys.MIN_GUI_RAM:
        stdoutLog.warning("Not asking for VNC because current memory (%d) < MIN_GUI_RAM (%d)", blivet.util.total_memory(), isys.MIN_GUI_RAM)
        flags.vncquestion = False

    # disable VNC question if text mode is requested and this is a ks install
    if anaconda.displayMode == 't' and flags.automatedInstall:
        stdoutLog.warning("Not asking for VNC because of an automated install")
        flags.vncquestion = False

    # disable VNC question if we were explicitly asked for text in kickstart
    if anaconda.ksdata.displaymode.displayMode == DISPLAY_MODE_TEXT:
        stdoutLog.warning("Not asking for VNC because text mode was explicitly asked for in kickstart")
        flags.vncquestion = False

    # disable VNC question if we don't have network
    if not nm_is_connecting() and not nm_is_connected():
        stdoutLog.warning("Not asking for VNC because we don't have a network")
        flags.vncquestion = False

    # disable VNC question if we don't have Xvnc
    if not os.access('/usr/bin/Xvnc', os.X_OK):
        stdoutLog.warning("Not asking for VNC because we don't have Xvnc")
        flags.vncquestion = False

    # Should we try to start Xorg?
    want_x = anaconda.displayMode == 'g' and not (flags.preexisting_x11 or flags.usevnc)

    # X on a headless (e.g. s390) system? Nonsense!
    if want_x and anaconda.isHeadless:
        stdoutLog.warning(_("DISPLAY variable not set. Starting text mode."))
        anaconda.displayMode = 't'
        graphical_failed = 1
        time.sleep(2)
        want_x = False

    # Is Xorg is actually available?
    if want_x and not os.access("/usr/bin/Xorg", os.X_OK):
        stdoutLog.warning(_("Graphical installation is not available. "
                            "Starting text mode."))
        time.sleep(2)
        anaconda.displayMode = 't'
        want_x = False

    if anaconda.displayMode == 't' and flags.vncquestion:
        #we prefer vnc over text mode, so ask about that
        message = _("Text mode provides a limited set of installation "
                    "options. It does not offer custom partitioning for "
                    "full control over the disk layout. Would you like "
                    "to use VNC mode instead?")

        app = App("VNC Question")
        spoke = AskVNCSpoke(app, anaconda.ksdata, message=message)
        app.schedule_screen(spoke)
        app.run()

        if anaconda.ksdata.vnc.enabled:
            anaconda.displayMode = 'g'
            flags.usevnc = True
            vncS.password = anaconda.ksdata.vnc.password
        else:
            # user has explicitly specified text mode
            flags.vncquestion = False

    log.info("Display mode = %s", anaconda.displayMode)
    startup_utils.check_memory(anaconda, options)

    # check_memory may have changed the display mode
    want_x = want_x and (anaconda.displayMode == "g")
    if want_x:
        try:
            start_x11()
            do_startup_x11_actions()
        except (OSError, RuntimeError) as e:
            log.warning("X startup failed: %s", e)
            stdoutLog.warning("X startup failed, falling back to text mode")
            anaconda.displayMode = 't'
            graphical_failed = 1
            time.sleep(2)

        if not graphical_failed:
            do_extra_x11_actions(options.runres, anaconda.displayMode)

    if anaconda.displayMode == 't' and graphical_failed and flags.vncquestion and not anaconda.ksdata.vnc.enabled:
        app = App("VNC Question")
        spoke = AskVNCSpoke(app, anaconda.ksdata)
        app.schedule_screen(spoke)
        app.run()

        if anaconda.ksdata.vnc.enabled:
            anaconda.displayMode = 'g'
            flags.usevnc = True
            vncS.password = anaconda.ksdata.vnc.password

    # if they want us to use VNC do that now
    if anaconda.displayMode == 'g' and flags.usevnc:
        vncS.startServer()
        do_startup_x11_actions()

    # with X running we can initialize the UI interface
    anaconda.initInterface(addons)

    anaconda.instClass.configure(anaconda)

    # report if starting the GUI failed
    anaconda.gui_startup_failed = bool(graphical_failed)