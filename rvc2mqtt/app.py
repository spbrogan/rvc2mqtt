"""
Main app/entrypoint for RVC2MQTT

Thanks goes to the contributors of https://github.com/linuxkidd/rvc-monitor-py
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
import logging.config
from math import floor
import queue
import signal
import time
import os
import sys
import ruyaml as YAML
from os import PathLike
import datetime
from typing import Optional
from rvc2mqtt.rvc import RVC_Decoder
from rvc2mqtt.can_support import CAN_Watcher
from rvc2mqtt.mqtt import MQTT_Support
from rvc2mqtt.plugin_support import PluginSupport
from rvc2mqtt.mqtt import *
from rvc2mqtt.entity_factory_support import entity_factory

PATH_TO_FOLDER = os.path.abspath(os.path.dirname(__file__))


def signal_handler(signal, frame):
    global MyApp
    logging.critical("shutting down.")
    MyApp.close()
    logging.shutdown()
    exit(0)


class app(object):
    def main(self, argsns: argparse.Namespace):
        """main function.  Sets up the app services, creates
        the receive thread, and processes messages.

        Runs until kill signal is sent
        """

        self.Logger = logging.getLogger("app")
        self.mqtt_client: MQTT_Support = None

        # make an receive queue of receive can bus messages
        self.rxQueue = queue.Queue()

        # For now lets buffer rVC formatted messages in this queue
        # which can then go thru the app to get encoded
        # and put into the txQueue for the canbus
        # this is a little hacky...so need to revisit
        self.tx_RVC_Buffer = queue.Queue()

        # make a transmit queue to send can bus messages
        self.txQueue = queue.Queue()

        # thread to receive can bus messages
        self.receiver = CAN_Watcher(
            argsns.can_interface, self.rxQueue, self.txQueue)
        self.receiver.start()

        # setup decoder
        self.rvc_decoder = RVC_Decoder()
        self.rvc_decoder.load_rvc_spec(os.path.join(
            PATH_TO_FOLDER, 'rvc-spec.yml'))  # load the RVC spec yaml

        # setup the mqtt broker connection
        if argsns.mqtt_host is not None:
            self.mqtt_client = MqttInitalize(
                argsns.mqtt_host, argsns.mqtt_port, argsns.mqtt_user, argsns.mqtt_pass, argsns.mqtt_client_id)
            if self.mqtt_client:
                self.mqtt_client.client.loop_start()

        # Enable plugins
        self.PluginSupport: PluginSupport = PluginSupport(os.path.join(
            PATH_TO_FOLDER, "entity"), argsns.plugin_paths)

        # Use plugins to dynamically prepare the entity factory
        entity_factory_list = []
        self.PluginSupport.register_with_factory_the_entity_plugins(
            entity_factory_list)

        # setup entity list using
        self.entity_list = []

        # initialize objects from the floorplan
        for item in argsns.fp:
            obj = entity_factory(
                item, self.mqtt_client, entity_factory_list)
            if obj is not None:
                obj.set_rvc_send_queue(self.tx_RVC_Buffer)
                obj.initialize()
                self.entity_list.append(obj)

        # Our RVC message loop here
        while True:
            # process any received messages
            self.message_rx_loop()
            self.message_tx_loop()
            time.sleep(0.001)

    def close(self):
        """Shutdown the app and any threads"""
        if self.receiver:
            self.receiver.kill_received = True
        if self.mqtt_client is not None:
            self.mqtt_client.shutdown()
            self.mqtt_client.client.loop_stop()

    def message_tx_loop(self):
        """ hacky - translate RVC formatted dict from rvc_tx to canbus msg formatted tx"""
        if self.tx_RVC_Buffer.empty():
            return

        rvc_dict = self.tx_RVC_Buffer.get()

        # translate
        rvc_dict["arbitration_id"] = self.rvc_decoder._rvc_to_can_frame(
            rvc_dict)

        self.Logger.debug(f"Sending Msg: {str(rvc_dict)}")

        # put into canbus watcher
        self.txQueue.put(rvc_dict)

    def message_rx_loop(self):
        """Process any RVC received messages"""
        if self.rxQueue.empty():  # Check if there is a message in queue
            return

        message = self.rxQueue.get()

        try:
            MsgDict = self.rvc_decoder.rvc_decode(
                message.arbitration_id,
                "".join("{0:02X}".format(x) for x in message.data),
            )
        except Exception as e:
            self.Logger.warning(f"Failed to decode msg. {message}: {e}")
            return

        # Log all rvc bus messages to custom logger so it can be routed or ignored
        logging.getLogger("rvc_bus_trace").debug(str(MsgDict))

        # Find if this is a device entity in our list
        # Pass to object

        for item in self.entity_list:
            if item.process_rvc_msg(MsgDict):
                # Should we allow processing by more than one obj.
                ##
                return

        # Use a custom logger so it can be routed easily or ignored
        logging.getLogger("unhandled_rvc").debug(f"Msg {str(MsgDict)}")


def configure_logging(verbosity: int):
    log_format = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(stream=sys.stdout,
                        format=log_format, level=logging.DEBUG)


def load_the_config(config_file_path: Optional[os.PathLike]):
    """ if config_file_path is a valid file load a yaml/json config file """
    if os.path.isfile(config_file_path):
        with open(config_file_path, "r") as content:
            yaml = YAML.YAML(typ='safe')
            return yaml.load(content.read())


def main():
    """Entrypoint.
    Get the config and run the app
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interface", "--INTERFACE", dest="can_interface",
                        help="can interface name like can0", default=os.environ.get("CAN_INTERFACE_NAME", "can0"))
    parser.add_argument("-f", "--floorplan", "--FLOORPLAN",
                        dest="floorplan", help="floorplan file path")
    parser.add_argument("-g", "--floorplan2",
                        dest="floorplan2", help="filepath to more floorplan")
    parser.add_argument("-p", "--plugin_path", dest="plugin_paths", action="append", help="path to directory to load plugins", default=[])
    parser.add_argument("--MQTT_HOST", "--mqtt_host", dest="mqtt_host",
                        help="Host URL", default=os.environ.get("MQTT_HOST"))
    parser.add_argument("--MQTT_PORT", "--mqtt_port", dest="mqtt_port",
                        help="Port", default=os.environ.get("MQTT_PORT", "1883"))
    parser.add_argument("--MQTT_USER", "--mqtt_user", dest="mqtt_user",
                        help="username for mqtt", default=os.environ.get("MQTT_USERNAME"))
    parser.add_argument("--MQTT_PASS", "--mqtt_pass", dest="mqtt_pass",
                        help="password for mqtt", default=os.environ.get("MQTT_PASSWORD"))

    # optional settings
    parser.add_argument("--MQTT_CLIENT_ID", "--mqtt_client_id", dest="mqtt_client_id",
                        help="client id for mqtt", default=os.environ.get("MQTT_CLIENT_ID"))
    parser.add_argument("--MQTT_CA", "--mqtt_ca", dest="mqtt_ca",
                        help="ca for mqtt", default=os.environ.get("MQTT_CA"))
    parser.add_argument("--MQTT_CERT", "--mqtt_cert", dest="mqtt_cert",
                        help="cert for mqtt", default=os.environ.get("MQTT_CERT"))
    parser.add_argument("--MQTT_KEY", "--mqtt_key", dest="mqtt_key",
                        help="key for mqtt", default=os.environ.get("MQTT_KEY"))

    parser.add_argument("-v", "--verbose", "--VERBOSE", dest="verbose", action="count",
                        help="Increase verbosity. Add multiple times to increase",
                        default=0)

    args = parser.parse_args()
    configure_logging(args.verbose)
    logging.info(
        "Log Started: "
        + datetime.datetime.strftime(datetime.datetime.now(),
                                     "%A, %B %d, %Y %I:%M%p")
    )

    try: 
        fp = []
        if args.floorplan is not None:
            if os.path.isfile(args.floorplan):
                c = load_the_config(args.floorplan)
                if "floorplan" in c:
                    fp.extend(c["floorplan"])
        
        if args.floorplan2 is not None:
            d = load_the_config(args.floorplan2)
            if "floorplan" in d:
                fp.extend(d["floorplan"])
        args.fp = fp
    except Exception as e:
        logging.critical(f"Floorplan failure: {str(e)}")

    global MyApp
    MyApp = app()
    signal.signal(signal.SIGINT, signal_handler)
    MyApp.main(args)


if __name__ == "__main__":
    main()
