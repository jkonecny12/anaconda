:Type: GUI
:Summary: Migrate Anaconda to Wayland application (#2231339)

:Description:
    This change enables Anaconda to run natively on Wayland. Previously, Anaconda operated as an
    Xorg application or relied on XWayland for support.

    By implementing this update, we can eliminate dependencies on X11 and embrace newer, more 
    secure technologies.

:Links:
    - https://bugzilla.redhat.com/show_bug.cgi?id=2231339
    - https://fedoraproject.org/wiki/Changes/AnacondaWebUIforFedoraWorkstation
    - https://github.com/rhinstaller/anaconda/pull/5829
    - https://bugzilla.redhat.com/show_bug.cgi?id=1955025
