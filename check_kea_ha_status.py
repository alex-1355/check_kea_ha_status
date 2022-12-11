#!/usr/bin/env python
###
# Version 1.0 - ali/14.06.2019
# Monitoring Kea DHCP HA state
###
# Version 1.1 - ali/09.12.2019
# added exception handling
###
# Version 1.2 - ali/11.12.2022
# Cleanup
###
# Nagios Exit-Codes:
# 0 = OK
# 1 = WARNING
# 2 = CRITICAL
# 3 = UNKNOWN
###
# curl -X POST -H "Content-Type: application/json" -d ' { "command": "ha-heartbeat", "service": [ "dhcp4" ]
# }' http://x.x.x.x:8080/
###
# Heartbeat Command
# The heartbeat commands are sent between the HA peers to detect failures.
# In the fatal failure case (e.g. server crash) no response will be received from the peer and the heartbeat will be lost.
# If the peer is online (e.g. waking up or ready for service), the server status will be returned.
###
# {
#     "command": "ha-heartbeat"
# }
###
# {
#     "result": 0,
#     "text": "HA peer status returned.",
#     "arguments": {
#         "status": "syncing" | "ready" | "load-balancing" | "partner-down"
#     }
# }
###


import sys
import re
import requests


def main(hostname,port):

    regex_status = re.compile(r'(hot-standby|partner-down)',flags=re.IGNORECASE)

#   create request
    headers = {
    'Content-Type': 'application/json',
    }

    data = ' { "command": "ha-heartbeat", "service": [ "dhcp4" ] \n}'

    try:

#       send request and save response as list
        response_raw = requests.post("http://"+hostname+":"+port+"/", headers=headers, data=data)

        ha_status = re.search(regex_status, response_raw.text)

        if response_raw.status_code == 200 and ha_status:
#           response is good and regex found a match
            if ha_status.group(1) == 'hot-standby':
#               ha-partner is available
                print("OK - HA state: hot-standby | ha_state=0;1;2;0;3")
                sys.exit(0)

            elif ha_status.group(1) == 'partner-down':
#               ha-partner is down
                print("CRITICAL - HA state: partner-down | ha_state=2;1;2;0;3")
                sys.exit(2)

        elif response_raw.status_code != 200 or not ha_status.group(1):
#           ha_status was not found using regex or API returned something other than OK
            print("UNKNOWN - API returned HTTP-Code %i | ha_state=3;1;2;0;3" % response_raw.status_code)
            sys.exit(2)

    except Exception as e:
        print("UNKNOWN - An error occured | ha_state=3;1;2;0;3")
        print("%s" % e)
        sys.exit(3)


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print("\n\t[*] check_kea_ha_status 1.2 [*]")
        print("\n\tUsage: check_kea_ha_status.py HOSTNAME PORT")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
