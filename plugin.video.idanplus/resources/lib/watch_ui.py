# -*- coding: utf-8 -*-
"""The "Continue watching" screen: one row per series, built from the watch history files only (no network)."""
import xbmc
import xbmcgui
import resources.lib.common as common
from resources.lib import watch_choose, watch_store



def RowTexts(row):
	"""(label, plot) of one row: `series · פרק N · title`, plus `(m:ss)` for a resume row, `הבא:` before the title of a next-episode row."""
	parts = [row['series_title']] if row['series_title'] else []
	if row['kind'] == 'season_end':
		parts.append('סיימת את העונה - בדיקת פרקים חדשים')
		return ' · '.join(parts), row['name']
	if row['number'] is not None:
		parts.append('פרק {0}'.format(row['number']))
	title = row['name']
	plot = title
	if row['kind'] == 'next':
		title = 'הבא: ' + title
	elif row['kind'] == 'resume':
		title = '{0} ({1})'.format(title, watch_store.clock(row['position']))
		plot = 'המשך מ-{0} מתוך {1}'.format(watch_store.clock(row['position']), watch_store.clock(row['total']))
	parts.append(title)
	return ' · '.join(parts), plot


def ChooserOn():
	"""The `watch_chooser` setting (default on): a click on a Continue row opens the chooser instead of playing."""
	return common.GetAddonSetting('watch_chooser') != 'false'


def ShowContinue(iconimage):
	"""List the rows. With the chooser setting on (default) a click on any row opens the chooser (`ShowChooser`); off, a row plays directly and a
	`season_end` row opens its season listing again (fresh, so new episodes show)."""
	folder = watch_store.watch_folder(common.profileDir)
	# stamp the version this list is built from BEFORE reading the files: if they change meanwhile the list is marked older than they are and gets refreshed
	xbmcgui.Window(10000).setProperty(watch_store.LIST_VERSION_PROPERTY, watch_store.progress_version(folder))
	rows = watch_store.continue_rows(watch_store.SeasonIndex(folder).load(), watch_store.read_progress(folder))
	chooser = ChooserOn()
	meta = watch_store.EpisodeMeta(folder).load()
	for row in rows:
		module = row['key'].split(':')[0]
		label, plot = RowTexts(row)
		description = (meta.get(row['key']) or {}).get('plot')
		if isinstance(description, str) and description.strip():
			plot = '\n'.join(line for line in (description.strip(), plot if plot != row['name'] else '') if line)
		infos = {"title": label, "plot": plot}
		if chooser:
			common.addDir(label, row['key'], 28, row['icon'] or iconimage, infos=infos, isFolder=False, addFav=False)
		elif row['kind'] == 'season_end' and watch_store.season_descriptor(row.get('open'), module, row['season_url']):
			mode, url, more = watch_store.season_descriptor(row.get('open'), module, row['season_url'])
			common.addDir(label, url, mode, row['icon'] or iconimage, infos=infos, module=module, moreData=more, addFav=False)
		else:
			common.addDir(label, row['url'], row.get('play_mode', 4), row['icon'] or iconimage, infos=infos, module=module,
				moreData=common.GetAddonSetting('{0}_res'.format(module)), isFolder=False, isPlayable=True, addFav=False, noResume=True)


def ShowChooser(key):
	"""Open the chooser for episode `key` and run what is picked. Nothing happens for an episode that is in no saved season or on Back."""
	from resources.lib import watch_chooser
	folder = watch_store.watch_folder(common.profileDir)
	seasons = watch_store.SeasonIndex(folder).load()
	options = watch_choose.choices(key, seasons, watch_store.read_progress(folder), common.AddonID, lambda module: common.GetAddonSetting('{0}_res'.format(module)),
		watch_store.EpisodeMeta(folder).load())
	if not options:
		return
	heading = watch_store.episode_entry(seasons, key).get('series_title') or common.AddonName
	picked = watch_chooser.choose(common.Addon.getAddonInfo('path'), heading, options, preselect=watch_choose.preselect(options))
	if picked >= 0:
		xbmc.executebuiltin(options[picked].builtin)


def ChooseResume(key, name, icon):
	"""Before a play: `(proceed, (seconds, total) or None)` by the `watch_resume` setting (auto resumes silently, ask puts the question first, before any
	request to the site). The question names what is about to play from the saved season, else from the label `name`; Back cancels (`proceed` False)."""
	from resources.lib import watch_chooser
	folder = watch_store.watch_folder(common.profileDir)
	progress = watch_store.read_progress(folder)
	mode = watch_store.resume_mode(common.GetAddonSetting('watch_resume'))

	def ask(position):
		entry = watch_store.episode_entry(watch_store.SeasonIndex(folder).load(), key)
		if entry:
			parts = [entry.get('series_title') or '', 'פרק {0}'.format(entry['number']) if entry.get('number') is not None else '', entry['name']]
			heading, still = ' · '.join(part for part in parts if part), entry.get('icon') or icon
		else:
			heading, still = common.GetUnColor(name), icon
		labels = ['המשך מ-{0}'.format(watch_store.clock(position)), 'התחל מההתחלה']
		picked = watch_chooser.ask_resume(common.Addon.getAddonInfo('path'), heading, labels, still=still)
		return {0: watch_store.ASK_RESUME, 1: watch_store.ASK_START_OVER}.get(picked, watch_store.ASK_CANCEL)

	return watch_store.decide_resume(progress, key, mode, ask)
