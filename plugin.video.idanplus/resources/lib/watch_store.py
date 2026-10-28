# -*- coding: utf-8 -*-
"""Watch history for episodes: what was played, how far, and which episode comes next. Pure Python, no Kodi imports.

Two small JSON files in one folder, each written by exactly ONE process so no cross-process lock is needed:

* `seasons.json`  - written by the plugin when it lists a season: the ordered episodes (key, name, picture, number, play url, air date) of each
  season and the series each season belongs to. This is the only place "next episode" is looked up, so asking for it costs no request.
* `progress.json` - written by the player service: per episode key the position, the length and whether it was finished.

Why our own resume point instead of Kodi's: Kodi keys a bookmark by the exact plugin path, and this addon's path carries the
(coloured) name, the picture url and the quality, which change from one listing to the next; the episode id inside it does not.
Everything here is keyed by an episode key `module:id` (for Mako that is the VCM id), never by a path.

What is stored and what is not: ids, titles, pictures, numbers, positions. Never a stream url, ticket, CDN or Next.js build id - those are
created fresh for every play (the Mako build id changes whenever the site is deployed).
"""
import hashlib
import json
import os
import re
import time
from urllib.parse import quote_plus, urlencode

SEASONS_FILE = 'seasons.json'
RESUME_AUTO, RESUME_ASK = 0, 1               # values of the `watch_resume` setting: resume silently / ask first
ASK_START_OVER, ASK_RESUME, ASK_CANCEL = 0, 1, -1   # the answers to the question
BASE_URLS = {'keshet': 'https://www.mako.co.il'}   # module -> site, to turn a saved season / program path into a url the module can open
PROGRESS_FILE = 'progress.json'
EPISODES_FILE = 'episodes.json'
HIDDEN_FILE = 'hidden.json'   # series key -> when the owner removed it from Continue watching; written by the plugin only (progress.json belongs to the service)
LIST_VERSION_PROPERTY = 'idanplus_continue_version'   # Home window property: the progress version the open Continue list was built from

RESUME_MIN_SECONDS = 60       # less than this watched: start from the beginning
FINISHED_RATIO = 0.95         # this much watched counts as finished
SEASON_REWRITE_SECONDS = 6 * 3600  # an unchanged season index is not rewritten more often than this


def watch_folder(profile_dir):
	"""The folder holding the two files, created on first use (inside the addon's profile folder)."""
	folder = os.path.join(profile_dir, 'watch')
	os.makedirs(folder, exist_ok=True)
	return folder


def episode_key(module, item_id):
	"""The key under which an episode is stored: `module:id`."""
	return '{0}:{1}'.format(module, item_id)


def _read(path):
	try:
		with open(path, 'r', encoding='utf-8') as handle:
			data = json.load(handle)
		return data if isinstance(data, dict) else {}
	except (OSError, ValueError):
		return {}


def _write(path, data):
	"""Write `data` as JSON through a temp file and a rename, so a reader never sees half a file."""
	tmp = path + '.tmp'
	with open(tmp, 'w', encoding='utf-8') as handle:
		json.dump(data, handle, ensure_ascii=False, separators=(',', ':'))
	os.replace(tmp, path)


class SeasonIndex(object):
	"""The plugin side: remembers the episodes of every season it lists."""

	def __init__(self, folder):
		self._path = os.path.join(folder, SEASONS_FILE)

	def remember_season(self, season_url, series_key, series_title, season_title, episodes, now=None, open_season=None, open_series=None):
		"""Save the listing of one season. `episodes` is the ordered list of dicts with `key`, `name`, `icon`, `number` (may be None), `url` (the addon's play url, built from ids only)
		and `aired` (`YYYY-MM-DD`, may be missing), and `play_mode` (the channel's mode that plays it; 4 when missing).

		`open_season` and `open_series` are `[mode, url, more_data]` descriptors of how the channel reopens this season and the program's season list (a channel
		whose pages are not just a base url + a path: Channel 13 uses a series id and a season number); `None` = the base-url rule in `season_descriptor`.

		Writes only when the content changed or the saved copy is older than `SEASON_REWRITE_SECONDS`, so opening an unchanged
		season costs a file read and no write. Episodes that vanished upstream are dropped from the order.
		"""
		now = time.time() if now is None else now
		data = _read(self._path)
		seasons = data.setdefault('seasons', {})
		entry = {
			'series': series_key, 'series_title': series_title, 'title': season_title, 'open': open_season, 'series_open': open_series,
			'order': [e['key'] for e in episodes],
			'eps': {e['key']: {'name': e['name'], 'icon': e.get('icon', ''), 'number': e.get('number'), 'url': e.get('url', ''), 'aired': e.get('aired', ''), 'play_mode': e.get('play_mode', 4)} for e in episodes},
		}
		old = seasons.get(season_url)
		if old and old.get('fetched') and now - old['fetched'] < SEASON_REWRITE_SECONDS and \
				{k: v for k, v in old.items() if k != 'fetched'} == entry:
			return False
		entry['fetched'] = now
		seasons[season_url] = entry
		_write(self._path, data)
		return True

	def load(self):
		return _read(self._path).get('seasons', {})


class EpisodeMeta(object):
	"""Facts about episodes that arrive with the play answer: `plot` (description), `aired` (`YYYY-MM-DD`), `duration` (seconds). Written by the plugin only
	(one writer, like the season index), read by the chooser and the Continue list. An empty fact never erases a known one; nothing is written when nothing changed."""

	def __init__(self, folder):
		self._path = os.path.join(folder, EPISODES_FILE)

	def remember(self, key, plot='', aired='', duration=0):
		"""Merge the non-empty facts into `key`'s; returns True when the file was written."""
		new = {name: value for name, value in (('plot', plot), ('aired', aired), ('duration', duration)) if value}
		if not new:
			return False
		data = _read(self._path)
		known = data.get(key) if isinstance(data.get(key), dict) else {}
		if all(known.get(name) == value for name, value in new.items()):
			return False
		data[key] = dict(known, **new)
		_write(self._path, data)
		return True

	def load(self):
		return _read(self._path)


class ProgressLog(object):
	"""The service side: positions of the episodes being watched.

	`sample` only updates memory; `flush` writes the file. The service samples every few seconds while a tracked episode plays and
	flushes about once a minute and at the end, so the disk is touched rarely.
	"""

	def __init__(self, folder):
		self._path = os.path.join(folder, PROGRESS_FILE)
		self._data = _read(self._path)
		self._dirty = False

	def sample(self, key, position, total, now=None):
		"""Note that `key` is at `position` seconds of `total`. Marks it finished once `FINISHED_RATIO` is reached.

		`position` is clamped to 0 (Kodi reports the start of a stream as a tiny negative number). `total` may be 0: a stream often does not know its length yet when playback starts. The episode is still recorded (so it
		shows in Continue watching) and the last known total is kept until a sample brings a real one.
		"""
		now = time.time() if now is None else now
		if total < 0:
			return
		position = max(0, position)   # Kodi reports the start as -0.0x; a position is never negative in the file
		old = self._data.get(key)
		if total == 0 and old:
			total = old['total']
		self._data[key] = {'pos': int(position), 'total': int(total), 'fin': total > 0 and position >= total * FINISHED_RATIO, 't': int(now)}
		self._dirty = True

	def mark_finished(self, key, now=None):
		"""The player reported the end of `key`: it is watched, whatever the last sampled position was."""
		now = time.time() if now is None else now
		old = self._data.get(key) or {'pos': 0, 'total': 0}
		self._data[key] = {'pos': old['pos'], 'total': old['total'], 'fin': True, 't': int(now)}
		self._dirty = True

	def flush(self):
		if self._dirty:
			_write(self._path, self._data)
			self._dirty = False

	def record(self, key):
		return self._data.get(key)


def progress_version(folder):
	"""A string that changes whenever the content of `progress.json` changes ('0' when there is no file): a hash of the file, which is a few KB. (The first
	version used the modification time and size; two writes within the timestamp granularity and of the same size, e.g. position 10 then 20, got the same
	version, found by running the test file on its own.) The Continue list stamps the version it was built from; the service refreshes an open list whose stamp
	differs, so a list is never redrawn for nothing and never left behind."""
	try:
		with open(os.path.join(folder, PROGRESS_FILE), 'rb') as handle:
			return hashlib.md5(handle.read()).hexdigest()[:16]
	except OSError:
		return '0'


def read_progress(folder):
	"""The progress records as the plugin sees them (a fresh read of the file)."""
	return _read(os.path.join(folder, PROGRESS_FILE))


def read_hidden(folder):
	"""The series removed from Continue watching: `{series key: time it was removed}` (empty when none)."""
	return _read(os.path.join(folder, HIDDEN_FILE))


def hide_series(folder, series, now=None):
	"""Remove `series` from the Continue watching list without touching its watch records (resume points and watched marks stay).

	The row comes back by itself when the series is watched again after `now` (see `continue_rows`)."""
	hidden = read_hidden(folder)
	hidden[series] = int(time.time() if now is None else now)
	_write(os.path.join(folder, HIDDEN_FILE), hidden)


def resume_point(progress, key):
	"""Seconds to resume `key` from, or 0 (never watched, finished, or too little watched to matter)."""
	rec = progress.get(key)
	if not rec or rec.get('fin') or rec.get('pos', 0) < RESUME_MIN_SECONDS:
		return 0
	return rec['pos']


def resume_mode(text):
	"""The `watch_resume` setting (Kodi's `getSetting` text) as `RESUME_AUTO` / `RESUME_ASK`; auto for anything else (unset, odd)."""
	try:
		value = int(text)
	except (TypeError, ValueError):
		return RESUME_AUTO
	return value if value in (RESUME_AUTO, RESUME_ASK) else RESUME_AUTO


def decide_resume(progress, key, mode, ask):
	"""Where playing `key` should start: `(proceed, resume)`. `resume` is `(seconds, total)` to resume from or None to start from the beginning; `proceed` False =
	the viewer cancelled. Only a position worth resuming (`resume_info`) is ever asked about. `RESUME_AUTO` resumes without a question; `RESUME_ASK` calls
	`ask(seconds)`, which returns `ASK_RESUME`, `ASK_START_OVER` or `ASK_CANCEL` (anything else counts as a cancel)."""
	info = resume_info(progress, key)
	if info is None:
		return True, None
	if mode != RESUME_ASK:
		return True, info
	answer = ask(info[0])
	if answer == ASK_RESUME:
		return True, info
	if answer == ASK_START_OVER:
		return True, None
	return False, None


def resume_info(progress, key):
	"""`(position, total)` to resume `key` with, or None. Kodi only treats a resume point as set when its total is positive, so an
	unknown total is replaced by one second past the position (the real length is learned again as soon as playback starts)."""
	position = resume_point(progress, key)
	if not position:
		return None
	return position, progress[key].get('total') or position + 1


def episode_entry(seasons, key):
	"""Any saved episode as a dict (`key`, `name`, `icon`, `number`, `url`, `series_title`, `season_url`), or None when it is in no saved season."""
	for season_url, season in seasons.items():
		if key in season.get('order', []):
			return dict({'play_mode': 4}, **dict(season['eps'][key], key=key, series_title=season.get('series_title', ''), season_url=season_url))
	return None


def episode_details(folder, key):
	"""Video info of episode `key` for the player (title, show, season, episode, plot, air date, length) from the saved season and the saved facts in `folder`: no
	request. `{}` when the episode is in no saved season (the label stays the title). The season number is the digits of the saved season title ("עונה 2")."""
	seasons = SeasonIndex(folder).load()
	entry = episode_entry(seasons, key)
	if entry is None:
		return {}
	facts = EpisodeMeta(folder).load().get(key) or {}
	infos = {'mediatype': 'episode', 'title': entry['name'], 'tvshowtitle': entry.get('series_title') or ''}
	season = re.search(r'\d+', seasons[entry['season_url']].get('title') or '')
	if season:
		infos['season'] = int(season.group())
	if entry.get('number') is not None:
		infos['episode'] = entry['number']
	for name, value in (('plot', facts.get('plot')), ('aired', entry.get('aired') or facts.get('aired')), ('duration', facts.get('duration'))):
		if value:
			infos[name] = value
	return {name: value for name, value in infos.items() if value != ''}


def next_entry(seasons, key):
	"""The episode after `key` in its saved season (see `episode_entry`), or None when `key` is not in a saved season or is the last one saved
	(new episodes may exist, but this answers from the files only)."""
	for season in seasons.values():
		order = season.get('order', [])
		if key in order:
			i = order.index(key)
			return episode_entry(seasons, order[i + 1]) if i + 1 < len(order) else None
	return None


def choose_entry(source_entry, seasons, key):
	"""The episode the next-episode card offers after `key`. `source_entry` is what the site itself says comes next (or None). The site wins
	over the saved season, and the saved season fills in the title, number and picture when it knows that episode; with no site entry the
	saved season's next row is used; with neither, None. A site entry that points at `key` itself is ignored."""
	if source_entry and source_entry.get('key') != key:
		known = episode_entry(seasons, source_entry['key'])
		if known:
			return dict(source_entry, **{k: known[k] for k in ('name', 'icon', 'number', 'url', 'play_mode') if known.get(k) not in (None, '')})
		return source_entry
	return next_entry(seasons, key)


def clock(seconds):
	"""`m:ss`, or `h:mm:ss` from an hour up."""
	seconds = int(seconds)
	if seconds >= 3600:
		return '{0}:{1:02d}:{2:02d}'.format(seconds // 3600, seconds % 3600 // 60, seconds % 60)
	return '{0}:{1:02d}'.format(seconds // 60, seconds % 60)


def plugin_url(addon_id, mode, module, url, name='', icon='', more_data=''):
	"""A plugin url in the shape `addDir` puts on a row: `mode` of `module` with `url` (and the display `name`, `icon`, `more_data`)."""
	params = {'name': name, 'url': quote_plus(url), 'mode': mode, 'iconimage': quote_plus(icon), 'module': module, 'moredata': quote_plus(more_data)}
	return 'plugin://{0}/?{1}'.format(addon_id, urlencode(params))


def play_url(addon_id, entry, more_data=''):
	"""The plugin url that plays `entry`: the entry's `play_mode` (4 when it has none) of the entry's module."""
	return plugin_url(addon_id, entry.get('play_mode', 4), entry['key'].split(':')[0], entry['url'], entry['name'], entry.get('icon', ''), more_data)


def season_descriptor(descriptor, module, season_url):
	"""`(mode, url, more_data)` that reopens a saved season: the stored descriptor, else (data saved before descriptors existed) the channel's base url plus the
	season path in mode 3; None when neither is known."""
	if descriptor:
		return tuple(descriptor)
	base = BASE_URLS.get(module)
	return (3, base + season_url, '') if base else None


def series_descriptor(descriptor, module, series_key):
	"""`(mode, url, more_data)` that opens the program's season list: the stored descriptor, else the base url plus the program path in mode 2; None if unknown."""
	if descriptor:
		return tuple(descriptor)
	base = BASE_URLS.get(module)
	return (2, base + series_key, '') if base and series_key else None


def continue_rows(seasons, progress, hidden=None):
	"""One row per series, newest activity first, built only from the two files (no network).

	`hidden` (`read_hidden`) lists series the owner removed: such a series has no row unless it was watched after it was removed.

	A row is a dict: `kind`, `series`, `series_title`, `season_url`, `key`, `name`, `icon`, `number`, `url`, `play_mode`, `open` (the season's reopen descriptor), `position`, `total`.
	`kind` is `resume` (part-watched episode), `next` (the episode after a finished one), `season_end` (finished the last
	episode of the saved list: new episodes may exist, so the row opens the season listing again) or `play` (barely started).
	"""
	where = {}  # episode key -> (season_url, season entry)
	for season_url, season in seasons.items():
		for key in season.get('order', []):
			where[key] = (season_url, season)
	latest = {}  # series key -> (time, episode key)
	for key, rec in progress.items():
		if key not in where:
			continue
		series = where[key][1].get('series')
		if series not in latest or rec.get('t', 0) > latest[series][0]:
			latest[series] = (rec.get('t', 0), key)
	rows = []
	for series, (when, key) in latest.items():
		if (hidden or {}).get(series, -1) >= when:
			continue
		season_url, season = where[key]
		rec = progress[key]
		target, kind = key, 'play'
		if rec.get('fin'):
			order = season['order']
			i = order.index(key)
			if i + 1 < len(order):
				target, kind = order[i + 1], 'next'
			else:
				kind = 'season_end'
		elif rec.get('pos', 0) >= RESUME_MIN_SECONDS:
			kind = 'resume'
		meta = season['eps'][target]
		shown = progress.get(target, {}) if kind != 'next' else {}
		rows.append({
			'kind': kind, 'series': series, 'series_title': season.get('series_title', ''), 'season_url': season_url,
			'key': target, 'name': meta['name'], 'icon': meta.get('icon', ''), 'number': meta.get('number'), 'url': meta.get('url', ''), 'play_mode': meta.get('play_mode', 4), 'open': season.get('open'),
			'position': shown.get('pos', 0) if kind == 'resume' else 0, 'total': shown.get('total', 0), 'when': when,
		})
	rows.sort(key=lambda r: r['when'], reverse=True)
	return rows
