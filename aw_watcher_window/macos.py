import subprocess
from subprocess import PIPE
import os
import logging
from Quartz.CoreGraphics import (CGEventSourceSecondsSinceLastEventType,
                                 kCGEventSourceStateHIDSystemState,
                                 kCGAnyInputEventType)


def getInfo() -> str:
    cmd = ["osascript", os.path.join(os.path.dirname(os.path.realpath(__file__)), "printAppTitle.scpt")]
    p = subprocess.run(cmd, stdout=PIPE)
    return str(p.stdout, "utf8").strip()


def getApp(info) -> str:
    return info.split('","')[0][1:]


def getTitle(info) -> str:
    return info.split('","')[1][:-1]

def seconds_since_last_input() -> float:
    return CGEventSourceSecondsSinceLastEventType(kCGEventSourceStateHIDSystemState, kCGAnyInputEventType)
