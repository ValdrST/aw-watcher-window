#!/usr/bin/env python
# encoding: utf-8
import subprocess
from subprocess import PIPE
import os
import logging
import osascript
from Quartz.CoreGraphics import (CGEventSourceSecondsSinceLastEventType,
                                 kCGEventSourceStateHIDSystemState,
                                 kCGAnyInputEventType)

def getInfo() -> str:
    #cmd = ["osascript", os.path.join(os.path.dirname(os.path.realpath(__file__)), "printAppTitle.scpt")]
    #p = subprocess.run(cmd, stdout=PIPE)
    info = []
    code, out, err = osascript.run('''
        global frontApp, frontAppName, windowTitle

        set windowTitle to ""
        tell application "System Events"
	        set frontApp to first application process whose frontmost is true
	        set frontAppName to name of frontApp
            tell process frontAppName
                try
                    tell (1st window whose value of attribute "AXMain" is true)
                        set windowTitle to value of attribute "AXTitle"
                    end tell
                end try
            end tell
        end tell
        return frontAppName
    ''')
    info.append(out.strip())

    code, out, err = osascript.run('''
        global frontApp, frontAppName, windowTitle

        set windowTitle to ""
        tell application "System Events"
	        set frontApp to first application process whose frontmost is true
	        set frontAppName to name of frontApp
            tell process frontAppName
                try
                    tell (1st window whose value of attribute "AXMain" is true)
                        set windowTitle to value of attribute "AXTitle"
                    end tell
                end try
            end tell
        end tell
        return windowTitle
    ''')
    info.append(out.strip())
    return info


def getApp(info) -> str:
    return info[0]


def getTitle(info) -> str:
    return info[1]

def seconds_since_last_input() -> float:
    return CGEventSourceSecondsSinceLastEventType(kCGEventSourceStateHIDSystemState, kCGAnyInputEventType)
