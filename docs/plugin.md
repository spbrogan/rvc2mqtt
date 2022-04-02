# Plugin Model

All entities or devices in the system are handled by a plugin. 
Some plugins will be generally maintained while others can be customized and supplied
in the plugin directory independent of the rvc2mqtt code.  

At the moment it is unclear how consistent and specification compliant RV-C devices are
and this allows greater flexibility while still hopefully creating an easy system. 

This is all open to feedback.  Expect this API to change initially during development.

## Requirements

A plugin must subclass from `EntityPluginBaseClass` or a derivative

A plugin instance is instantiated by the `entity_factory` for each entry defined in the config.  
For this to work the plugin must define a class attributes of `FACTORY_MATCH_ATTRIBUTES` which
is a dictionary of key/value pairs that match an incoming floor-plan description from the config.

It is ok to create base classes and other supporting classes in the plugin that are not instantiated
by the factory.  

A plugin must be able to make a unique and consistent device identifier for mqtt usage.

Don't use relative imports.  Due to how it is loaded this doesn't work right.

## Members

`self.id:str` - Must be set to a unique and consistent value (used for mqtt topic).  Must be first thing done in `init`

`self.Logger` - Logger for the plugin.  Should be initialized during `init` after all super class initialization.

`self.status_topic: str` - Topic string for the device state to publish to

`self.mqtt_support: MQTT_Support` - mqtt_support object used for pub/sub operations

`self.send_queue: queue` - queue used to transmit any RVC can bus messages.  Msg must be a dictionary and must supply at least the `dgn` string and 8 byte `data` array.   

## Functions

### init

```python
"""
Initialize an entity instance for the data defined in data

@param: data - data definition defined in config
"""
def __init__(self, data:dict, mqtt_support: MQTT_Support):
    self.id: str #= <your unique value here for this instance>
    super().__init__(data, mqtt_support)
    self.Logger = logging.getLogger(__class__.__name__)

    # do your init here
```

### initialize

```python
def initialize(self):
    """ Optional function 
    Will get called once when the object is loaded.  
    RVC canbus tx queue is available
    mqtt client is ready.  
    
    This can be a good place to request data from canbus
    and publish more info topics
    
    """
    # publish info to mqtt
    self.mqtt_support.client.publish(self.status_topic, self.state, retain=True)

    # request dgn report - this should trigger that dgn to report
    # dgn = 1FFBD which is actually  BD FF 01 <instance> FF 00 00 00
    self.Logger.debug("Sending Request for DGN")
    data = struct.pack("<BBBBBBBB", int("0xBD",0), int("0xFF", 0), 1, self.rvc_instance, 0, 0, 0, 0)
    self.send_queue.put({"dgn": "EAFF", "data": data})
```

### process rvc messages

Each plugin instance will have an opportunity to evaluate an RV-C message
to see if it is relevant.  This is handled by implementing the function

``` python
""" 
Process an incoming rvc message and determine if it is of interest to this
instance of this object.

It is common to leverage _is_entry_match() from EntityPluginBaseClass
        
If relevant and exclusive - Process the message and return True
else - return False
"""
def process_rvc_msg(self, new_message: dict) -> bool:
```

### process mqtt messages

If you device allows for control from outside the RV-C network
then this is handled using mqtt.  
`mqtt_support` provides a subscription registration service for 
any topic of interest.  This subscription requires a callback.  
The callback has a function prototype like

```python
def process_mqtt_msg(self, topic, payload):
```
