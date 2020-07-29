import argparse
import logging
import subprocess
import threading
from threading import Thread
import time

from inotify.adapters import InotifyTree
import inotify.constants

logger = logging.getLogger(__name__)


def main():
    args = _parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    watcher = Watcher(args)
    watcher.run()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Directory watcher")
    parser.add_argument(
        "-d", dest="debug", action="store_true", help="enable debug logging"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        metavar="SECS",
        type=float,
        default=1.0,
        help="set quiet period which must elapse before running command. Default: %(default)s.",
    )
    parser.add_argument("dir", metavar="DIR", help="directory to watch")

    parser.add_argument("cmd", metavar="CMD", help="command to run on changes")
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, metavar="...", help="arguments to command"
    )
    return parser.parse_args()


class Watcher:
    def __init__(self, args: argparse.Namespace):
        self._src = args.dir
        self._quiet_time = args.quiet
        self._args = [args.cmd] + args.args

        # when did the last update happen?
        self._last_update_time = 0.0

        # have there been writes since we last started a sync?
        self._dirty = True

        # is there currently a running sync thread?
        self._running = False

        # lock to protect _dirty and _running
        self._lock = threading.Lock()

    def run(self):
        # mask out a few boring events
        mask = inotify.constants.IN_ALL_EVENTS & ~(
            inotify.constants.IN_ACCESS
            | inotify.constants.IN_CLOSE_NOWRITE
            | inotify.constants.IN_OPEN
        )

        # set up the watchers
        notifier = InotifyTree(self._src, block_duration_s=3600, mask=mask)

        # perform an initial sync
        self._sync_thread()

        for event in notifier.event_gen():
            if event is None:
                continue
            self._schedule_sync()

    def _schedule_sync(self):
        self._last_update_time = time.time()

        # to avoid racing against the sync thread deciding to exit, we take the lock.
        with self._lock:
            self._dirty = True
            if self._running:
                return

        # set this before we start the thread, otherwise it might get cleared!
        self._running = True

        # fire off a separate thread to do the sync
        t = Thread(target=self._sync_thread)

        t.start()

    def _sync_thread(self):
        while True:
            # take the lock to decide if it is time to exit, and clear the running
            # bit if so.
            with self._lock:
                if not self._dirty:
                    self._running = False
                    return

            while True:
                delay = self._last_update_time + self._quiet_time - time.time()
                if delay <= 0:
                    break
                logger.info("Waiting %fs for quiet time to elapse", delay)
                time.sleep(delay)

            logger.info("running sync")
            self._dirty = False
            self._sync()
            logger.info("sync complete")

    def _sync(self):
        subprocess.run(self._args)


if __name__ == "__main__":
    main()
