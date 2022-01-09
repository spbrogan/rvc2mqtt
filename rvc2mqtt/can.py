"""
Defines a thread class for reading the can bus using python-can library.
Messages are put into queue for usage outside this thread.

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

import threading
import can
import logging
import queue

class CAN_Watcher(threading.Thread):
    def __init__(self, interface, rx_queue: queue.Queue):
        threading.Thread.__init__(self)
        # A flag to notify the thread that it should finish up and exit
        self.kill_received = False
        logging.getLogger(__name__).info(f"Starting can bus on interface {interface}")
        self.bus = can.interface.Bus(channel=interface, bustype="socketcan_native")
        self.rx = rx_queue

    def run(self):
        while not self.kill_received:
            message = self.bus.recv()  # read messages from a canbus
            self.rx.put(message)  # Put message into queue