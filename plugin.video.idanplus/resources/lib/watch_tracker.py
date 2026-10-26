# -*- coding: utf-8 -*-
"""The player service's part of the watch history: follows a tracked episode while it plays, saves its position, and drives the
"next episode" card near its end.

Cost model (the addon must stay light on a low-power box): the service loop wakes every `TICK_SECONDS` (5 s; a 1 s service loop was measured on such a box
at about 0.03 % of a core) and does nothing unless a tracked episode plays. While one plays, two cheap Player calls every
`SAMPLE_SECONDS` (memory only), the file is written every `FLUSH_SECONDS` and at stop/end, and in the last `NEXT_NEAR_END` seconds the loop
ticks every second for the card. Kodi cannot report the position after a stop, so the last sample is what a stop saves (at most
`SAMPLE_SECONDS` stale; a pause or a seek samples at once). The episode is recorded at its start even when the stream does not yet know its
length (seen in the first real run: the first version dropped such a start and its first sample came up to a minute late).

One thread only: Kodi delivers Player callbacks and window clicks on the thread that created the Player / window, inside
`Monitor.waitForAbort`, so the loop, the callbacks and the card's buttons all run on the service thread and nothing needs a lock.

`Tracker` and `Service` have no Kodi imports (player, prompt factory and clock are handed in), so a whole viewing runs in a test with fakes;
`run()` is the thin Kodi adapter.
"""
import watch_next
import watch_store

SAMPLE_SECONDS = 15
FLUSH_SECONDS = 60
TICK_SECONDS = 5       # the loop's wake-up while nothing needs a faster tick
NEAR_TICK_SECONDS = 1  # while the next-episode card is due or up, or a list refresh is waiting
REFRESH_WAIT_SECONDS = 8   # after a viewing: how long to wait for the Continue list to be the open screen and for the player to be idle


def showing_list(folder_path, addon_id):
	"""True when `folder_path` (Kodi's `Container.FolderPath`) is this addon's Continue-watching list: never another screen, another addon's mode 27, or
	the empty path Kodi gives while a video is fullscreen (the list window is then not the active one and Kodi would ignore a refresh anyway)."""
	return folder_path.startswith('plugin://{0}/'.format(addon_id)) and 'mode=27' in folder_path


def list_is_stale(folder_path, addon_id, built_version, current_version):
	"""True when the Continue list is the open screen and was built from an older progress file than the one on disk."""
	return showing_list(folder_path, addon_id) and built_version != current_version


class Tracker(object):
	"""State of the episode being watched (position and the write schedule)."""

	def __init__(self, log):
		self._log = log
		self._key = None
		self._last_flush = 0

	@property
	def active(self):
		return self._key is not None

	def begin(self, key, position, total, now):
		"""A tracked episode started (`key` is its watch-history key, from the ListItem property)."""
		self._key = key
		self._last_flush = now
		self._log.sample(key, position, total, now)
		self._log.flush()   # the start is on disk at once: the episode shows in Continue watching (a list that is open can be refreshed) while it plays

	def sample(self, position, total, now):
		"""The current position of the tracked episode; writes the file when `FLUSH_SECONDS` have passed."""
		if self._key is None:
			return
		self._log.sample(self._key, position, total, now)
		if now - self._last_flush >= FLUSH_SECONDS:
			self._log.flush()
			self._last_flush = now

	def end(self, finished, now):
		"""Playback stopped (`finished` False: keep the last sampled position) or ran to its end (`finished` True: mark it watched)."""
		if self._key is None:
			return
		if finished:
			self._log.mark_finished(self._key, now)
		self._log.flush()
		self._key = None


class Service(object):
	"""One tracked viewing at a time. `player.position()` gives `(seconds, total)`; `make_prompt(key, prompt_data)` gives a `watch_next.NextPrompt` or
	None (`prompt_data` is the site's hints from the playing item, `{}` when there are none); `refresh()` redraws the Continue list when it is the open
	screen and returns True (False = it is not showing, try again); `log(text)` writes one info line."""

	def __init__(self, tracker, player, make_prompt, log, refresh=lambda: True):
		self._tracker, self._player, self._make_prompt, self._log, self._refresh = tracker, player, make_prompt, log, refresh
		self._prompt = None
		self._refresh_until = None   # a viewing ended: until when to keep trying to redraw the Continue list
		self._last_sample = 0
		self._position = (0, 0)

	# -- Player events (delivered by Kodi on this thread) -------------------------------------

	def started(self, key, now, prompt_data=None):
		self._refresh_until = None   # another viewing: the list is refreshed after the last one
		position, total = self._player.position()
		self._tracker.begin(key, position, total, now)
		self._position, self._last_sample = (position, total), now
		self._prompt = self._make_prompt(key, prompt_data or {})
		self._log('tracking {0} at {1:.0f}/{2:.0f}{3}'.format(key, position, total, ', next episode offered' if self._prompt else ''))

	def sample_now(self, now):
		"""A pause or a seek: the position is accurate right now."""
		if self._tracker.active:
			self._sample(now)

	def stopped(self, now):
		"""The viewer (or Kodi) stopped playback. A stop within `CLOSE_TO_END_SECONDS` of the end counts as the end (the player sometimes
		reports a stop where it should report an end): the episode is watched and the prompt may start the next one. Only judged when a
		prompt exists, because only then is the position fresh (the loop ticks every second near the end)."""
		if self._tracker.active:
			self._log('stopped')
			self._refresh_until = now + REFRESH_WAIT_SECONDS
		prompt, self._prompt = self._prompt, None
		position, total = self._position
		close = prompt is not None and total >= watch_next.MIN_TOTAL_SECONDS and 0 <= total - position <= watch_next.CLOSE_TO_END_SECONDS
		self._tracker.end(close, now)
		if prompt:
			prompt.ended() if close else prompt.stopped()

	def shutdown(self, now):
		"""Kodi is shutting down: save what there is, start nothing."""
		self._prompt = None
		self._tracker.end(False, now)

	def ended(self, now):
		if self._tracker.active:
			self._log('ended')
			self._refresh_until = now + REFRESH_WAIT_SECONDS
		prompt, self._prompt = self._prompt, None
		self._tracker.end(True, now)
		if prompt:
			prompt.ended()

	def finish_current(self, now):
		"""The viewer chose "Play now": the current episode counts as watched. The stop that follows is then a no-op here."""
		if self._tracker.active:
			self._refresh_until = now + REFRESH_WAIT_SECONDS
		self._prompt = None
		self._tracker.end(True, now)

	# -- the loop ----------------------------------------------------------------------------

	def tick(self, now):
		"""Called by the loop on every wake-up; returns the seconds to wait before the next one."""
		waiting = self._refresh_waiting(now)
		if not self._tracker.active:
			return NEAR_TICK_SECONDS if waiting else TICK_SECONDS
		near = self._prompt is not None and self._prompt.near_end(*self._position)
		if near or now - self._last_sample >= SAMPLE_SECONDS:
			self._sample(now)
			near = self._prompt is not None and self._prompt.near_end(*self._position)
		return NEAR_TICK_SECONDS if near or waiting else TICK_SECONDS

	def _refresh_waiting(self, now):
		"""Keep the Continue list current. Kodi does not redraw a plugin list by itself (when playback ends it shows the list as it was), and it redraws one
		only while its window is the active one, so `refresh()` (the adapter) decides: the list is the open screen and out of date. While a viewing runs it is
		asked on every tick and nothing waits (in fullscreen the list is simply not showing); after a viewing ends it is asked until it shows (the video
		window is closing), for at most `REFRESH_WAIT_SECONDS`. Returns True while still waiting."""
		active = self._tracker.active
		if not active and self._refresh_until is None:
			return False
		if not active and now > self._refresh_until:
			self._refresh_until = None
			self._log('list refresh: the Continue list was not the open screen, left alone')
			return False
		try:
			done = self._refresh()
		except Exception as ex:
			self._log('list refresh: {0}'.format(ex))
			done = False
		if active:
			return False
		if done:
			self._refresh_until = None
			return False
		return True

	def _sample(self, now):
		try:
			position, total = self._player.position()
		except Exception as ex:   # the player may have just stopped
			self._log('sample: {0}'.format(ex))
			return
		self._position, self._last_sample = (position, total), now
		self._tracker.sample(position, total, now)
		if self._prompt is not None:
			self._prompt.tick(position, total)


def read_bool(read_setting, name, default):
	"""A bool addon setting through `read_setting(name)` (Kodi's `getSetting`: 'true' / 'false' / '' when unknown); `default` when it is unknown."""
	value = (read_setting(name) or '').strip().lower()
	return default if value == '' else value == 'true'


def run(profile_dir, addon_path, addon_id, quality_for=lambda module: '', clock=None, read_setting=lambda name: ''):
	"""The service loop. Blocks until Kodi shuts down. `quality_for(module)` gives the `moredata` (quality) the module's play url carries;
	`clock` is the time source (`time.time`; a test passes the simulator's virtual clock); `read_setting(name)` reads an addon setting
	(`watch_autoplay`, default OFF, and `watch_card`, default ON, are read when each tracked episode starts, so a change applies to the next one)."""
	import json
	import time
	import xbmc
	import xbmcgui

	now = clock or time.time

	def log(text):
		xbmc.log('idanplus watch: {0}'.format(text), xbmc.LOGINFO)

	folder = watch_store.watch_folder(profile_dir)
	tracker = Tracker(watch_store.ProgressLog(folder))
	holder = {}   # the Player and the Service, filled below (they refer to each other through the callbacks)

	class Watcher(xbmc.Player):
		def position(self):
			return self.getTime(), self.getTotalTime()

		def is_playing(self):
			return self.isPlaying()

		def onAVStarted(self):
			try:
				item = self.getPlayingItem()
				key = item.getProperty('idanplus_key')
				if key:
					holder['service'].started(key, now(), prompt_data(item.getProperty('idanplus_prompt')))
			except Exception as ex:
				log('start: {0}'.format(ex))

		def onPlayBackPaused(self):
			self._safe(lambda: holder['service'].sample_now(now()))

		def onPlayBackSeek(self, time_ms, seek_offset):
			self._safe(lambda: holder['service'].sample_now(now()))

		def onPlayBackStopped(self):
			self._safe(lambda: holder['service'].stopped(now()))

		def onPlayBackEnded(self):
			self._safe(lambda: holder['service'].ended(now()))

		def _safe(self, call):
			try:
				call()
			except Exception as ex:
				log('event: {0}'.format(ex))

	def prompt_data(text):
		"""The site's hints (`idanplus_prompt`, JSON) as a dict; `{}` when absent or not valid."""
		try:
			data = json.loads(text) if text else {}
		except ValueError:
			log('prompt data is not valid JSON')
			return {}
		return data if isinstance(data, dict) else {}

	def make_prompt(key, data):
		"""A card for the episode after `key` (the site's `next` if it gave one, else the saved season's next row), or None (neither knows one)."""
		seasons = watch_store.SeasonIndex(folder).load()
		entry = watch_store.choose_entry(data.get('next') if isinstance(data.get('next'), dict) else None, seasons, key)
		if entry is None:
			return None
		card = watch_next.KodiCard(addon_path)
		autoplay, show_card = read_bool(read_setting, 'watch_autoplay', False), read_bool(read_setting, 'watch_card', True)
		prompt = watch_next.NextPrompt(entry, card, play, credits_at=data.get('credits'), expected_total=data.get('total'), autoplay=autoplay, show_card=show_card)
		at_credits = bool(data.get('total')) and prompt.lead(data['total']) != watch_next.PROMPT_SECONDS
		log('card for {0} (next from {1}, opens {2}, autoplay {3}, card {4})'.format(entry['key'], 'the site' if data.get('next') else 'the saved season',
			'at the credits' if at_credits else 'at the default time', 'on' if autoplay else 'off', 'on' if show_card else 'off'))
		card.bind(prompt)
		return prompt

	def play(entry, replace):
		url = watch_store.play_url(addon_id, entry, quality_for(entry['key'].split(':')[0]))
		if replace:
			holder['service'].finish_current(now())
			watcher.stop()
		log('next episode: {0}'.format(entry['key']))
		watcher.play(url)

	home = xbmcgui.Window(10000)

	def refresh_view():
		"""Redraw the Continue list when it is the open screen and was built from older data than the saved data (it stamps its version on the Home window).
		True when the list is showing (refreshed or already current), False when it is not. Asks Kodi once per version: the plugin needs a moment to rebuild."""
		path = xbmc.getInfoLabel('Container.FolderPath')
		if not showing_list(path, addon_id):
			return False
		version = watch_store.progress_version(folder)
		if list_is_stale(path, addon_id, home.getProperty(watch_store.LIST_VERSION_PROPERTY), version) and holder.get('asked') != version:
			holder['asked'] = version
			xbmc.executebuiltin('Container.Refresh')
			log('list refreshed (the saved data changed)')
		return True

	watcher = Watcher()
	holder['service'] = Service(tracker, watcher, make_prompt, log, refresh_view)
	log('service started')
	monitor = xbmc.Monitor()
	wait = TICK_SECONDS
	while not monitor.waitForAbort(wait):
		try:
			wait = holder['service'].tick(now())
		except Exception as ex:
			log('tick: {0}'.format(ex))
			wait = TICK_SECONDS
	holder['service'].shutdown(now())
