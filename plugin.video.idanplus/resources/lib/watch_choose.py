# -*- coding: utf-8 -*-
"""What the Continue-watching chooser offers for an episode: the same list that the series-tracker windows of other Kodi video addons show.

In their order, with the episode the row points at in the middle and preselected: the next episode, this episode, the previous episode, the
season's episode list, the season list. Only what exists is offered (no previous for the first saved episode, no next for the last saved one).
Each choice carries the Kodi builtin to run when it is picked (`PlayMedia(...)` or `Container.Update(...)`), so the route that shows the window
only has to run the picked one. Pure: no Kodi imports; built from the two history files and the plugin url helpers in `watch_store`.

Every play is `PlayMedia(url,noresume)`: without `noresume` Kodi asks "Resume from ... / Play from beginning" by itself whenever its own video database holds a
bookmark for the url (it writes one when a video started from a plugin item stops; `PlayerBuiltins.cpp` `askToResume`, `SaveFileStateJob.cpp`, Kodi 21.3). The
addon resumes by its own record instead, silently: the play route resolves the item with a resume point, which `noresume` leaves in force
(`CPluginDirectory::GetPluginResult`).

Preview (the plot box of each episode choice), up to three lines: the description; `שודר: DD.MM.YYYY · משך: H:MM:SS`; where a part-watched episode would
resume. The picture, name and air date come from the saved season (every episode has them); the description and the length only exist once the site
has told them: with the play answer of that episode or of the one before it (`watch_store.EpisodeMeta`). A fact that is missing or odd is left out.
"""
import re
from collections import namedtuple

from resources.lib import watch_store   # imported the way watch_ui imports it: one module object on the plugin side

LABEL_NEXT = 'הפרק הבא'
LABEL_THIS = 'הפרק הנוכחי'
LABEL_PREVIOUS = 'הפרק הקודם'
LABEL_SEASON = 'פרקי העונה'
LABEL_SEASONS = 'בחירת עונה'

Choice = namedtuple('Choice', 'label label2 plot thumb builtin current')   # `current`: the row the list opens on


def _second_line(entry):
	"""`פרק 3  title`, or just the title for an episode without a number."""
	if entry.get('number') is None:
		return entry['name']
	return 'פרק {0}  {1}'.format(entry['number'], entry['name'])


def _resume_line(progress, key):
	"""Where a part-watched episode would resume (empty when it would start from the beginning)."""
	position = watch_store.resume_point(progress, key)
	if not position:
		return ''
	total = progress[key].get('total') or 0
	if total > 0:
		return 'המשך מ-{0} מתוך {1}'.format(watch_store.clock(position), watch_store.clock(total))
	return 'המשך מ-{0}'.format(watch_store.clock(position))


def _date(iso):
	"""`YYYY-MM-DD` as `DD.MM.YYYY`, or '' when it is not a date."""
	found = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', iso) if isinstance(iso, str) else None
	return '{0}.{1}.{2}'.format(found.group(3), found.group(2), found.group(1)) if found else ''


def _facts_line(aired, duration):
	parts = []
	if _date(aired):
		parts.append('שודר: ' + _date(aired))
	if isinstance(duration, int) and not isinstance(duration, bool) and duration > 0:
		parts.append('משך: ' + watch_store.clock(duration))
	return ' · '.join(parts)


def _preview(entry, facts, resume_line=''):
	"""The plot box text of an episode choice (see the module docstring)."""
	facts = facts if isinstance(facts, dict) else {}
	plot = facts.get('plot').strip() if isinstance(facts.get('plot'), str) else ''
	lines = [plot, _facts_line(entry.get('aired') or facts.get('aired'), facts.get('duration')), resume_line]
	return '\n'.join(line for line in lines if line)


def choices(key, seasons, progress, addon_id, quality_for, meta=None):
	"""The chooser for episode `key`, or `[]` when it is in no saved season. `quality_for(module)` gives the `moredata` a play url of that module carries;
	`meta` is `watch_store.EpisodeMeta.load()` (facts per episode key)."""
	meta = meta or {}
	here = watch_store.episode_entry(seasons, key)
	if here is None:
		return []
	season = seasons[here['season_url']]
	order = season['order']
	position = order.index(key)
	module = key.split(':')[0]
	more = quality_for(module)

	def play(entry):
		return 'PlayMedia({0},noresume)'.format(watch_store.play_url(addon_id, entry, more))   # see the module docstring

	result = []
	if position + 1 < len(order):
		nxt = watch_store.episode_entry(seasons, order[position + 1])
		result.append(Choice(LABEL_NEXT, _second_line(nxt), _preview(nxt, meta.get(order[position + 1])), nxt.get('icon', ''), play(nxt), False))
	result.append(Choice(LABEL_THIS, _second_line(here), _preview(here, meta.get(key), _resume_line(progress, key)), here.get('icon', ''), play(here), True))
	if position > 0:
		previous = watch_store.episode_entry(seasons, order[position - 1])
		result.append(Choice(LABEL_PREVIOUS, _second_line(previous), _preview(previous, meta.get(order[position - 1])), previous.get('icon', ''), play(previous), False))
	opened = watch_store.season_descriptor(season.get('open'), module, here['season_url'])
	if opened:
		season_url = watch_store.plugin_url(addon_id, opened[0], module, opened[1], season.get('title', ''), here.get('icon', ''), opened[2])
		result.append(Choice(LABEL_SEASON, '', '', here.get('icon', ''), 'Container.Update({0})'.format(season_url), False))
	listed = watch_store.series_descriptor(season.get('series_open'), module, season.get('series'))
	if opened and listed:
		seasons_url = watch_store.plugin_url(addon_id, listed[0], module, listed[1], season.get('series_title', ''), here.get('icon', ''), listed[2])
		result.append(Choice(LABEL_SEASONS, '', '', here.get('icon', ''), 'Container.Update({0})'.format(seasons_url), False))
	return result


def preselect(options):
	"""The position the list opens on: the current episode (what opening the row would have played)."""
	return next((i for i, choice in enumerate(options) if choice.current), 0)
