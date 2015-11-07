#!/usr/bin/env bash

# Allow daemon to listen on http port 80
setcap 'cap_net_bind_service=+ep' /usr/bin/flickmagnetd

