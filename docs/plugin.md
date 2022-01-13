# Plugin Model

## init

class name must match filename

\_\_init\_\_(self, config: OPTIONAL(dict<str, str>))

create plugin object. 
self will be added to process list if object has 
process function.

## process function

function to take incoming msg dict
and change or add to it. 

process(self, msg: dict<str, str>) --> boolean 







