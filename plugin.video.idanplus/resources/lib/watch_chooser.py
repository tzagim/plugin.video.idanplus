# -*- coding: utf-8 -*-
"""The Kodi half of the Continue-watching chooser: a skinned list window (`idanplus-chooser.xml`) with Kodi's own details dialog as the fallback.

The window is a "what to play" list window on a small contract: the skin
must declare a list with id 2000; each row is a ListItem whose label and label2 are the two text lines and whose properties `plot` and `thumb` are the preview;
the window properties are `heading`, `fanart` and `poster`. The skin shows the focused row's picture and plot beside the list on its own, so no code follows
the selection. Self-contained: idanplus needs no other addon for it.

The user is never left without a screen: if the window cannot be shown (its XML or textures missing, no list 2000) a log line says why and Kodi's own select dialog
with details (picture and plot per row) takes over.
"""
from collections import namedtuple

import xbmc
import xbmcgui

_Row = namedtuple('_Row', 'label label2 plot thumb')   # what the window reads of a row: only the label is used by the question

SKIN_FILE, SKIN_NAME, SKIN_RESOLUTION = 'idanplus-chooser.xml', 'Default', '1080i'
RESUME_SKIN_FILE = 'idanplus-resume.xml'   # the small "resume from ... / start over" question, on the same contract (list 2000 with a label per row)
LIST_ID = 2000
_BACK = (xbmcgui.ACTION_PARENT_DIR, xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK)


def _listitems(choices):
	items = []
	for choice in choices:
		item = xbmcgui.ListItem(label=choice.label, label2=choice.label2, offscreen=True)
		item.setProperties({'plot': choice.plot, 'thumb': choice.thumb})
		items.append(item)
	return items


class _Window(xbmcgui.WindowXMLDialog):
	"""The dialog: `selected` is the picked position, `None` after Back, `error` says why it closed itself (the skin has no list 2000)."""

	def __init__(self, *args, **kwargs):
		xbmcgui.WindowXMLDialog.__init__(self, *args)
		self._rows, self._window_props, self._start_on = kwargs['choices'], kwargs['props'], kwargs['preselect']   # names that cannot collide with Kodi's window attributes
		self.selected = None
		self.error = None

	def onInit(self):
		try:   # an exception in a callback is only logged and leaves an empty window open, so a skin without the list is caught here
			listing = self.getControl(LIST_ID)
		except RuntimeError as error:
			self.error = str(error)
			self.close()
			return
		for name, value in self._window_props.items():
			self.setProperty(name, value)
		listing.reset()
		listing.addItems(_listitems(self._rows))
		if 0 < self._start_on < len(self._rows):
			listing.selectItem(self._start_on)
		self.setFocusId(LIST_ID)

	def onClick(self, controlId):
		if controlId != LIST_ID or self.selected is not None:
			return
		position = self.getControl(LIST_ID).getSelectedPosition()
		if 0 <= position < len(self._rows):
			self.selected = position
			self.close()

	def onAction(self, action):
		if action.getId() in _BACK:
			self.selected = None
			self.close()


def _in_window(addon_path, heading, choices, fanart, poster, preselect, skin_file=None):
	"""The picked position (-1 for Back), or `None` when the window could not be shown. `skin_file` defaults to the chooser's."""
	skin_file = skin_file or SKIN_FILE
	props = {'heading': heading or '', 'fanart': fanart or '', 'poster': poster or ''}
	try:
		window = _Window(skin_file, addon_path, SKIN_NAME, SKIN_RESOLUTION, choices=choices, props=props, preselect=preselect)
		try:
			window.doModal()
			if window.error:
				raise RuntimeError('chooser skin {0}: {1}'.format(skin_file, window.error))
			return -1 if window.selected is None else window.selected
		finally:
			window.clearProperties()
	except RuntimeError as error:   # Kodi could not load the XML, or the skin lacks the list
		xbmc.log('idanplus chooser window not shown, using the plain dialog: {0}'.format(error), xbmc.LOGWARNING)
		return None


def _in_dialog(heading, choices, preselect):
	"""Kodi's own select dialog with details: picture and plot per row."""
	items = []
	for choice in choices:
		item = xbmcgui.ListItem(label=choice.label, label2=choice.label2, offscreen=True)
		if choice.thumb:
			item.setArt({'thumb': choice.thumb, 'icon': choice.thumb})
		item.getVideoInfoTag().setPlot(choice.plot)
		items.append(item)
	return xbmcgui.Dialog().select(heading, items, preselect=preselect, useDetails=True)


def choose(addon_path, heading, choices, preselect=0, fanart='', poster=''):
	"""Show `choices` (see `watch_choose.Choice`) and return the picked position, or -1 for Back."""
	if not choices:
		return -1
	picked = _in_window(addon_path, heading, choices, fanart, poster, preselect)
	if picked is None:
		picked = _in_dialog(heading, choices, preselect)
	return picked


def ask_resume(addon_path, heading, labels, still='', dialog_heading=''):
	"""The question before a part-watched episode plays: `labels` are the rows (resume first, preselected). `heading` says what is about to play and `still` is its
	picture. Returns the picked position, or -1 for Back (which cancels the play). Falls back to Kodi's select dialog like the chooser."""
	rows = [_Row(label, '', '', '') for label in labels]
	picked = _in_window(addon_path, heading, rows, '', still, 0, RESUME_SKIN_FILE)
	if picked is None:
		picked = xbmcgui.Dialog().select(dialog_heading or heading, list(labels))
	return picked
