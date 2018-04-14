# Flick Magnet

Open source NetFlix clone.

## Screenshot

![Flick Magnet 0.0.7 screenshot on desktop](https://acerix.github.io/flickmagnet/flickmagnet-0.0.7.png)

## Install Daemon

```
python3 setup.py install --optimize=1
```

## Start Daemon

Install examples/flickmagnet.service in systemd and start/enable the service, or run the installed flickmagnet.py with python3:

```
/usr/bin/python3 /usr/lib/python3.5/site-packages/flickmagnet/flickmagnet.py
```

## Open in Browser

When the daemon starts, it displays a URL to connect from web browsers. The default URL to connect to a daemon on the same machine is:

[http://localhost:42000/](http://localhost:42000/)
