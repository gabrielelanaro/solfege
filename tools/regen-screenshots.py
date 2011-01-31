#!/usr/bin/python

import os
import sys
import subprocess

filenames = [
    "trainingset-editor.png",
    "preferences-midi.png",
    "preferences-user.png",
    "preferences-external-programs.png",
    "preferences-gui.png",
    "preferences-practise.png",
    "preferences-sound-setup.png",
    #    "preferences-sound-setup-win32.png",
    "id-interval-buttons-thirds.png",
    "id-interval-piano.png",
    "singinterval.png",
    "idbyname-chords.png",
    "chord.png",
    "singchord.png",
    "rhythm.png",
    "dictation.png",
    "idbyname-intonation.png",
    "idtone.png",
    "identifybpm.png",
    "twelvetone.png",
    "nameinterval.png",
    "elembuilder-harmonic-progressions.png",

    #"chordname-example.png",
    #"progressionlabel-example-1.png",
    #"rnc-example.png",
]

if 'LANGUAGE' not in os.environ:
    print "Set the LANGUAGE environment variable and run Solfege with that locale"
    sys.exit()
    
for filename in filenames:
    print "Prepare for", filename
    raw_input("[Press Enter]")
    subprocess.call(["python", "tools/screenshot.py", os.path.join("help", os.environ['LANGUAGE'], "figures", filename)])
