
import os
import time

import libtorrent
import sys
import re

import binascii

from operator import attrgetter

status_names = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']

dht_routers = [
	('router.utorrent.com', 6881),
	('router.bittorrent.com', 6881),
	('dht.transmissionbt.com', 6881),
	('dht.aelitis.com', 6881)
]

dht_bootstrap_nodes = [
	('bootstrap.ring.cx', 4222)
]

default_trackers = [
	'udp://tracker.openbittorrent.com:80/announce',
	'udp://open.demonii.com:1337/announce',
	'udp://tracker.coppersurfer.tk:6969/announce',
	'udp://tracker.leechers-paradise.org:6969/announce',
	'udp://glotorrents.pw:6969/announce',
	'http://pow7.com/announce'
]

import inspect



def save_state(settings, session_handle):

	with open(settings['libtorrent_state_file'], 'wb') as state_file:
		state_file.write(libtorrent.bencode(session_handle.save_state()))
		#print('torrentd state saved to', settings['libtorrent_state_file'])



def load_state(settings, session_handle):

	if os.path.isfile(settings['libtorrent_state_file']):
		with open(settings['libtorrent_state_file'], 'rb') as state_file:
			session_handle.load_state(
				libtorrent.bdecode(state_file.read())
			)
			#print('torrentd state loaded from', settings['libtorrent_state_file'])



# store the metadata of active torrents
def save_torrents(settings, session_handle):

	for torrent_handle in session_handle.get_torrents():
		resume_data = torrent_handle.save_resume_data()
		print('save', torrent_handle.info_hash(), resume_data, type(resume_data))
		if resume_data is not None:
			print(resume_data)
			with open(os.path.join(settings['download_dir'], torrent_handle.info_hash() + '.torrent'), 'wb') as resume_data_file:
				print(os.path.join(settings['download_dir'], torrent_handle.info_hash() + '.torrent'))
				resume_data_file.write(libtorrent.bencode(resume_data))
		
		



def start(settings, db_connect, save_path):

	magnet_statuses = settings['cached_tables']['magnet_file_status']
	
	db = db_connect()

	# start session
	session_handle = libtorrent.session()

	session_settings = session_handle.get_settings()

	# default timeouts can cause shutdown to take over a minute

	# number of seconds the tracker connection will wait from when it sent the request until it considers the tracker to have timed-out. Default value is 60 seconds.
	session_settings['tracker_completion_timeout'] = 10

	# number of seconds to wait to receive any data from the tracker. If no data is received for this number of seconds, the tracker will be considered as having timed out. If a tracker is down, this is the kind of timeout that will occur. The default value is 20 seconds.
	session_settings['tracker_receive_timeout'] = 10

	# apply custom settings
	session_handle.set_settings(session_settings)
	
	# load previous state
	load_state(settings, session_handle)

	# stop any torrents
	stop_all_downloads(session_handle, db, magnet_statuses)


	# listen

	print('torrentd starting on port', settings['torrent_port'])

	session_handle.listen_on(settings['torrent_port'], settings['torrent_port'])

	# add some dht routers, if a search is ever made while the routing table is empty, those nodes will be used as backups
	for r in dht_routers:
		session_handle.add_dht_router(*r)

	# add some dht nodes, if a valid DHT reply is received, the node will be added to the routing table
	for r in dht_bootstrap_nodes:
		session_handle.add_dht_node(r)


	# already started by session() flags?

	# the listen port and the DHT port are attempted to be forwarded on local UPnP router devices
	# @todo dht_state should be saved on shutdown and passed in here:  http://libtorrent.org/reference-Session.html#id38
	#session_handle.start_dht()

	# the listen port and the DHT port are attempted to be forwarded on local UPnP router devices
	#session_handle.start_upnp()


	while True:

		save_state(settings, session_handle)
		
		save_torrents(settings, session_handle)

		
		preload_new_magnets(session_handle, save_path, db, magnet_statuses)
		
		#print()

		for alert in session_handle.pop_alerts():
			print('torrent alert:', alert)


		#session_status = session_handle.status()

		#print(
		#    'dht: ',
		#    '(down: ', session_status.dht_download_rate / 1000, ' kb/s up: ', session_status.dht_upload_rate / 1000, ' kB/s ',
		#    'nodes: ', session_status.dht_nodes, ') ',
		#    'dht_torrents: ', session_status.dht_torrents
		#)

		for torrent_handle in session_handle.get_torrents():

			print()
			print('status of torrent:', torrent_handle.info_hash())

			# dht_settings = session_handle.get_settings()

			torrent_status = torrent_handle.status()

			print(
				torrent_status.progress * 100, '% complete ',
				'(down: ', torrent_status.download_rate / 1000, ' kb/s up: ', torrent_status.upload_rate / 1000, ' kB/s ',
				'peers: ', torrent_status.num_peers, ') ',
				'state: ', status_names[torrent_status.state]

			)



		# print('trackers: ', torrent_handle.trackers())

		# print('torrent cleanup')
		# session_handle.remove_torrent(torrent_handle)

		#process_queue(session_handle, save_path, db, magnet_statuses)

		time.sleep(3)

	save_state(settings, session_handle)

	# exit instead of returning to parent process
	os._exit(0)





# stop any torrents
# @todo only stop torrents for this user
def stop_all_downloads(session_handle, db, magnet_statuses):
	
	# change "watching" to "ready"
	dbc = db.execute("""
UPDATE
	magnet_file
SET
	status_id = :status_id_ready
WHERE
	status_id IN (:status_id_watching, :status_id_start_watching)
""", {
	'status_id_ready': magnet_statuses['ready'],
	'status_id_watching': magnet_statuses['watching'],
	'status_id_start_watching': magnet_statuses['start watching']
})
	db.commit()
	
	# pause all torrents
	for torrent_handle in session_handle.get_torrents():
		torrent_handle.pause()




# start downloading the torrent file immediately, with highest priority, starting at the byte_offset
def start_streaming_magnet_file(session_handle, save_path, btih, video_filename, magnet_file_id, db, magnet_statuses, byte_offset=0):
	
	print(btih, 'start streaming', video_filename, magnet_file_id)

	stop_all_downloads(session_handle, db, magnet_statuses)
		
	# can't get add_torrent to work with infohash
	#
	# btih_bytes = binascii.unhexlify(btih)
	# btih_str = btih_bytes.decode('raw_unicode_escape')
	# infohash = libtorrent.sha1_hash(btih_bytes)
	#torrent_handle = session_handle.add_torrent({
	#    'save_path': save_path,
	#    'infohash': infohash
	#})

	# putting it in a magnet URL works
	torrent_handle = session_handle.add_torrent({
		'save_path': os.path.join(save_path, btih),
		'url': 'magnet:?xt=urn:btih:' + btih,
		'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate
	})

	# add some udp trackers
	for url in default_trackers:
		torrent_handle.add_tracker({
			'url': url
		})

	torrent_handle.force_dht_announce()
	torrent_handle.set_sequential_download(True)




	print(btih, 'waiting for torrent metadata')

	# @todo timeout
	while torrent_handle.status().state<3:
		torrent_status = torrent_handle.status()
		print(btih, status_names[torrent_status.state])
		time.sleep(3)

	torrent_info = torrent_handle.get_torrent_info()


	# get magnet file info
	dbc = db.execute("""
SELECT
	*
FROM
	magnet_file
WHERE
	id = ?

""", [
	magnet_file_id
])
	magnet_file = dbc.fetchone()

	print(btih, 'looking at metadata')

	# tv episode
	if 1 == magnet_file['entity_type_id']:

		print('tv', magnet_file['entity_id'])
		print(magnet_file)

		for f in torrent_info.files():

			# ignore files less than 10 MB
			if f.size < 10485760:
				continue;
			
			
			dbc = db.execute("""
SELECT
	series.*
FROM
	episode
JOIN
	season
		ON
			season.id = episode.season_id
JOIN
	series
		ON
			series.id = season.series_id
WHERE
	episode.number = ?
AND
	season.number = ?
AND
	sibling.id = ?
""", [
	magnet_file['entity_id']
])
			series = dbc.fetchone()

			print('find_episode for', series.name, 'in', f.path)
			
			ignore_file, season_number, episode_number = find_episode_number_in_file_path(f.path, series.title)
			
			print('result', ignore_file, season_number, episode_number)
			
			if (ignore_file):
				continue
			
			dbc = db.execute("""
SELECT
	episode.id
FROM
	episode
JOIN
	season
		ON
			season.id = episode.season_id
WHERE
	season.series_id = ?
AND
	season.number = ?
AND
	episode.number = ?
""", [
	series.id,
	season_number,
	episode_number
])
			episode = dbc.fetchone()
			
			if episode:

				dbc = db.execute("""
UPDATE
	magnet_file
SET
	filename = ?
WHERE
	entity_type_id = 1 AND entity_id = ?
""", [
	f.path,
	episode['id']
])
				db.commit()


	# movie
	if 2 == magnet_file['entity_type_id']:

		#print('movie')

		# assume the biggest file is the video payload
		# http://libtorrent.org/reference-Storage.html#file-entry
		biggest_file_entry = max(torrent_info.files(), key=attrgetter('size'))

		dbc = db.execute("""
UPDATE
	magnet_file
SET
	filename = ?
WHERE
	id = ?

""", [
	biggest_file_entry.path,
	magnet_file_id
])
		db.commit()




	# @todo only download the specified video_filename, not entire torrent

	# @todo start downloading at "byte_offset", eg. so the video player can seek ahead

	# @todo stop any other downloads

	# torrent_status = torrent_handle.status()

	# @todo delete videos older than video_cache_days or not defined in a magnet_file




# if file_path looks like a video file for an episode of season_title, return the season number and episode number, otherwise ignore_file
def find_episode_number_in_file_path(file_path, series_title=None):
	
	ignore_file = True
	season_number = None
	episode_number = None

	se = re.search(r's(?:eason)? ?(\d{1,2}).*e(?:pisode)? ?(\d{1,2})', file_path, flags=re.IGNORECASE)

	if se is not None:
		ignore_file = False
		season_number = int(se.group(1))
		episode_number = int(se.group(2))
		
	return (ignore_file, season_number, episode_number)
	


# process magnet_file actions
def process_queue(session_handle, save_path, db, magnet_statuses):

	# find videos queued to start streaming
	dbc = db.execute("""
SELECT
	magnet_file.*,
	magnet.btih
FROM
	magnet_file
JOIN
	magnet
		ON
			magnet.id = magnet_file.magnet_id
WHERE
	magnet_file.status_id = :status_id_start_watching
""", {
	'status_id_start_watching': magnet_statuses['start watching']
})

	for r in dbc.fetchall():
		
		# start watching
		print('start watching')
		
		dbc = db.execute("""
UPDATE
	magnet_file
SET
	status_id = :status_id_watching
WHERE
	magnet_file.id = :magnet_file_id
""", {
	'status_id_watching': magnet_statuses['watching'],
	'magnet_file_id': r['id']
})
		db.commit()
		
		start_streaming_magnet_file(session_handle, save_path, r['btih'], r['filename'], r['id'], db, magnet_statuses, r['stream_position'])






# get metadata for new titles
def preload_new_magnets(session_handle, save_path, db, magnet_statuses):
	
	# find torrents queued to preload
	dbc = db.execute("""
SELECT
	magnet_file.*,
	magnet.btih
FROM
	magnet_file
JOIN
	magnet
		ON
			magnet.id = magnet_file.magnet_id
WHERE
	magnet_file.status_id = :status_id_new
""", {
	'status_id_new': magnet_statuses['new']
})

	for r in dbc.fetchall():
		
		# start watching
		print(r['btih'], 'preloading...')
		
		dbc = db.execute("""
UPDATE
	magnet_file
SET
	status_id = :status_id_preloading
WHERE
	magnet_file.id = :magnet_file_id
""", {
	'status_id_preloading': magnet_statuses['preloading'],
	'magnet_file_id': r['id']
})
		db.commit()
		
		torrent_handle = session_handle.add_torrent({
			'save_path': os.path.join(save_path, r['btih']),
			'url': 'magnet:?xt=urn:btih:' + r['btih']
		})
		
		# @todo does it download the metadata when paused?
		torrent_handle.pause()

		# add some udp trackers
		for url in default_trackers:
			torrent_handle.add_tracker({
				'url': url
			})

		torrent_handle.force_dht_announce()
		torrent_handle.set_sequential_download(True)
		return
