# Testing

You should use unit-tests when at all possible.  It leads to better structured code and can be automated. 
Information here about other options are for certain situations and more "functional" testing. 

Linux has the concept of a virtual can bus (vcan).  This can be an easy and safe way to test your 
code sending or receiving message if you can't do it in unit test or want to test more aspects of the 
full application.  

For example before sending my first command on the RVC bus I used a virtual canbus to confirm that byte order
and other attributes were correct as i didn't want to send a bad message and potentially cause issues.  

## Create vcan

run `sudo ip link add dev vcan0 type vcan`

## Bring it up

run `sudo ip link set vcan0 up`

## interact

For rvc2mqtt you can change the interface to vcan0 and it should just work.  

You can then open a second terminal and use something like canutils to send or receive 
on the canbus.  

## Todo

Develop some quick and easy scripts that mimic/mock/fake certain things for validation.