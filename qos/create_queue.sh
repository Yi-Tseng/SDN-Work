#!/bin/bash
# https://github.com/PeterDaveHello/ColorEchoForShell
if [[ ! -s "ColorEcho.bash" ]]; then
    alias echo.BoldRed='echo'
    alias echo.BoldGreen='echo'
    alias echo.BoldYellow='echo'
else
    . ColorEcho.bash
fi

if [ "$(id -u)" != "0" ]; then
   echo.Red "This script must be run as root" 1>&2
   exit 1
fi

ovs-vsctl -- get Port eth0 qos | grep -e '\[\]' &> /dev/null

if [ $? != 0 ]; then
    echo.Red "Qos settings is not empty, please clear it first!"
    exit 1
fi

echo.Yellow "Setting up queue to $PORTS"
PORTS="eth0 eth1 eth2 eth3"
CMD="ovs-vsctl"

for PORT in $PORTS; do
    CMD="$CMD -- set Port $PORT qos=@newqos"
done

CMD="$CMD -- --id=@newqos create QoS type=linux-htb other-config:max-rate=1000000000 queues=0=@q0,1=@q1"
CMD="$CMD -- --id=@q0 create Queue other-config:min-rate=100000000 other-config:max-rate=100000000"
CMD="$CMD -- --id=@q1 create Queue other-config:min-rate=500000000"

$CMD

echo.Green "Done"
