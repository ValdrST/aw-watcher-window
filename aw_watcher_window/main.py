import argparse
import logging
import traceback
import sys
import os
import platform
from time import sleep
from datetime import datetime, timezone, timedelta
from time import sleep
import os
import getpass

from aw_core.util import assert_version
from aw_core.models import Event
from aw_core.log import setup_logging
from aw_client import ActivityWatchClient

from .lib import get_current_window
from .config import load_config, watcher_config

system = platform.system()
if system == "Windows":
    from .windows import seconds_since_last_input
elif system == "Darwin":
    from .macos import seconds_since_last_input
elif system == "Linux":
    from .unix import seconds_since_last_input
else:
    raise Exception("Unsupported platform: {}".format(system))


logger = logging.getLogger(__name__)

class Settings:
    def __init__(self, config_section):
        # Time without input before we're considering the user as AFK
        self.timeout = config_section.getfloat("timeout")
        # How often we should poll for input activity
        self.poll_time = config_section.getfloat("poll_time")

        assert self.timeout >= self.poll_time

def main():
    # Verify python version is >=3.5
    #   req_version is 3.5 due to usage of subprocess.run
    assert_version((3, 5))
    if sys.platform.startswith("linux") and ("DISPLAY" not in os.environ or not os.environ["DISPLAY"]):
        raise Exception("DISPLAY environment variable not set")

    # Read settings from config
    config = load_config()
    args = parse_args(default_poll_time=config.getfloat("poll_time"),default_timeout=config.getfloat("timeout"))

    setup_logging(name="aw-watcher-window", testing=args.testing, verbose=args.verbose,
                  log_stderr=True, log_file=True)

    client = ActivityWatchClient("aw-watcher-window", testing=args.testing)

    bucket_id = "{}_{}".format(client.client_name, client.client_hostname)
    event_type = "currentwindow"

    client.create_bucket(bucket_id, event_type, queued=True)

    logger.info("aw-watcher-window started")
    sleep(1)  # wait for server to start
    with client:
        heartbeat_loop(client, bucket_id, poll_time=args.poll_time, exclude_title=args.exclude_title, timeout=args.timeout)


def parse_args(default_poll_time: float):
    """config contains defaults loaded from the config file"""
    parser = argparse.ArgumentParser("A cross platform window watcher for Activitywatch.\nSupported on: Linux (X11), macOS and Windows.")
    parser.add_argument("--testing", dest="testing", action="store_true")
    parser.add_argument("--exclude-title", dest="exclude_title", action="store_true")
    parser.add_argument("--verbose", dest="verbose", action="store_true")
    parser.add_argument("--poll-time", dest="poll_time", type=float, default=default_poll_time)
    parser.add_argument("--timeout",dest="timeout", type=float,default=default_timeout)
    return parser.parse_args()



def heartbeat_loop(client, bucket_id, poll_time, exclude_title=False, timeout):
    afk = False
    while True:
        if os.getppid() == 1:
            logger.info("window-watcher stopped because parent process died")
            break

        try:
            current_window = get_current_window()
            logger.debug(current_window)
        except Exception as e:
            logger.error("Exception thrown while trying to get active window: {}".format(e))
            traceback.print_exc()
            current_window = {"appname": "unknown", "title": "unknown"}

        now = datetime.now(timezone.utc)
        if current_window is None:
            logger.debug('Unable to fetch window, trying again on next poll')
        else:
            # Create current_window event
            data = {
                "app": current_window["appname"],
                "title": current_window["title"] if not exclude_title else "excluded",
                "user": current_window["user"]
            }
            seconds_since_input = seconds_since_last_input()
            last_input = now - timedelta(seconds=seconds_since_input)
            if afk and seconds_since_last_input < timeout:
                logger.info("No longer AFK")
                data["status"] = "afk" if afk else "not-afk"
                current_window_event = Event(timestamp=last_input, data=data,duration=0)
                pulsetime = timeout + poll_time
                client.heartbeat(bucket_id, current_window_event, pulsetime=pulsetime, queued=True)
                afk = False
                data["status"] = "afk" if afk else "not-afk"
                current_window_event = Event(timestamp=last_input, data=data,duration=0)
                pulsetime = timeout + poll_time
                client.heartbeat(bucket_id, current_window_event, pulsetime=pulsetime, queued=True)
            elif not afk and seconds_since_input >= timeout:
                logger.info("Became AFK")
                data["status"] = "afk" if afk else "not-afk"
                current_window_event = Event(timestamp=last_input, data=data,duration=0)
                pulsetime = timeout + poll_time
                client.heartbeat(bucket_id, current_window_event, pulsetime=pulsetime, queued=True)
                afk = True
                data["status"] = "afk" if afk else "not-afk"
                current_window_event = Event(timestamp=last_input, data=data,duration=seconds_since_input)
                pulsetime = timeout + poll_time
                client.heartbeat(bucket_id, current_window_event, pulsetime=pulsetime, queued=True)
            else:
                if afk:
                    data["status"] = "afk" if afk else "not-afk"
                    current_window_event = Event(timestamp=last_input, data=data,duration=seconds_since_input)
                    pulsetime = timeout + poll_time
                    client.heartbeat(bucket_id, current_window_event, pulsetime=pulsetime, queued=True)
                else:
                    data["status"] = "afk" if afk else "not-afk"
                    current_window_event = Event(timestamp=last_input, data=data,duration=0)
                    pulsetime = timeout + poll_time
                    client.heartbeat(bucket_id, current_window_event, pulsetime=pulsetime, queued=True)
            # Set pulsetime to 1 second more than the poll_time
            # This since the loop takes more time than poll_time
            # due to sleep(poll_time).
        sleep(poll_time)
