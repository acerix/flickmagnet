#!/usr/bin/env sh

# Unmount torrents (needs root?)
umount "`dirname $0`"/flickmagnet/htdocs/torrents/*

# Force stop btfs
killall btfs
sleep 1
killall btfs -9

# Delete btfs torrent cache
rm -r ~/btfs/

# Delete config, cache, logs for the current user
rm -r ~/.config/flickmagnet/ ~/.cache/flickmagnet/ ~/.local/share/flickmagnet/

