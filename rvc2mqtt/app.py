"""
Main app/entrypoint for RVC2MQTT

Thanks goes to the contributers of https://github.com/linuxkidd/rvc-monitor-py
This code is derived from parts of https://github.com/linuxkidd/rvc-monitor-py/blob/master/usr/bin/rvc2mqtt.py
which was licensed using Apache-2.0.  No copyright information was present in the above mentioned file but original
content is owned by the authors. 

Copyright 2022 Sean Brogan
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import argparse
import logging
import queue
import signal
import time
import datetime
from rvc import RVC_Decoder
from rvc2mqtt.can import CAN_Watcher


def signal_handler(signal, frame):
    global MyApp
    logging.critcal("shutting down.")
    MyApp.close()
    logging.shutdown()
    exit(0)


class app(object):
    def main(self, can_interface_name: str):
        """main function.  Sets up the app services, creates
        the receive thread, and processes messages.

        Runs until kill signal is sent
        """

        self.Logger = logging.getLogger("app")

        # make an recieve queue pass messages
        self.rxQueue = queue.Queue()

        # make a transmit queue
        self.txQueue = queue.Queue()  ## messages to send

        # thread to recieve can bus messages
        self.receiver = CAN_Watcher(can_interface_name, self.rxQueue)
        self.receiver.start()

        self.rvc_decoder = RVC_Decoder()
        self.rvc_decoder.load_rvc_spec()  # load the RVC spec yaml

        while True:
            # process any received messages
            self.message_rx_loop()
            time.sleep(0.001)

    def close(self):
        """Shutdown the app and any threads"""
        if self.receiver:
            self.receiver.kill_received = True

    def message_rx_loop(self):
        """Process any recieved messages"""
        if self.rxQueue.empty():  # Check if there is a message in queue
            return

        message = self.rxQueue.get()
        self.Logger.debug("{0:X} ({1:X})".format(message.arbitration_id, message.dlc))

        try:
            MsgDict = self.rvc_decoder.rvc_decode(
                message.arbitration_id,
                "".join("{0:02X}".format(x) for x in message.data),
            )
        except Exception as e:
            self.Logger.warning(f"Failed to decode msg. {message}: {e}")

        self.Logger.debug(str(MsgDict))


if __name__ == "__main__":
    """Entrypoint.
    Get loggers setup, cli arguments parsed, and run the app
    """
    logger = logging.getLogger("")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--interface", default="can0", help="CAN interface to use"
    )
    parser.add_argument(
        "--OutputLog", dest="OutputLog", help="Create an output log file"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="Verbose",
        action="count",
        help="Increase verbosity. Add multiple times to increase",
        default=0,
    )
    args = parser.parse_args()

    verbosity2level = [logging.ERROR, logging.INFO, logging.DEBUG]
    console.setLevel(
        verbosity2level[max(min(0, args.verbose), len(verbosity2level) - 1)]
    )

    # setup file logging if so requested
    if args.OutputLog:
        if len(args.OutputLog) < 2:
            logging.critical("the output log file parameter is invalid")
        else:
            # setup file based logging
            filelogger = logging.FileHandler(filename=args.OutputLog, mode="w")
            filelogger.setLevel(
                verbosity2level[max(min(0, args.verbose), len(verbosity2level) - 1)]
            )
            logging.getLogger("").addHandler(filelogger)

    logging.info(
        "Log Started: "
        + datetime.datetime.strftime(datetime.datetime.now(), "%A, %B %d, %Y %I:%M%p")
    )

    global MyApp
    MyApp = app()
    signal.signal(signal.SIGINT, signal_handler)
    MyApp.main(args.interface)
