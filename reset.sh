#!/usr/bin/env sh

# Unmount torrents
umount "`dirname $0`"/flickmagnet/htdocs/torrents/*

# Force stop btfs
killall btfs
sleep 1
killall btfs -9

# Delete torrent caches
rm -r ~/btfs/ "`dirname $0`"/flickmagnet/htdocs/torrents/*

# Delete config, cache, logs for the current user
rm -r ~/.config/flickmagnet/ ~/.cache/flickmagnet/ ~/.local/share/flickmagnet/ 

