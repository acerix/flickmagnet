# flickmagnet

Open source NetFlix clone

## Install Daemon

```
python3 setup.py install --optimize=1
```

## Start Daemon

Note: The current prototype is not very resilient, be sure your Internet is working before starting the daemon for the first time.

Copy examples/flickmagnet.service to systemd and start/enable the service, or run the installed flickmagnet.py with python3:

```
/usr/bin/python3 /usr/lib/python3.5/site-packages/flickmagnet/flickmagnet.py
```

## Watch

When the daemon starts, it displays a URL to connect from web browsers. The default URL to connect to a daemon on the same machine is:

[http://localhost:42000/](http://localhost:42000/)

Note: Give the daemon a few minutes to find some videos the first time it's started.

