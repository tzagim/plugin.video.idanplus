# -*- coding: utf-8 -*-
"""The "next episode" offer shown near the end of a tracked episode: `NextPrompt` (the behaviour, no Kodi imports) and `KodiCard` (the window).

Behaviour: when the card is due (see `NextPrompt.lead`) it offers the next episode. Two settings decide the rest:
  * `autoplay` (the addon's default is OFF): on = the card counts down and the next episode starts when the item ends (or stops within
    `CLOSE_TO_END_SECONDS` of its end), also when the card never showed (an unknown length, a sampling gap); off = the card is a plain offer in
    "hold" mode (no countdown, `HOLD_TEXT`) and nothing starts by itself; "Play now" always works.
  * `show_card` (default ON): off = no card at all; the next episode then still starts at the end when `autoplay` is on.
"Close" keeps the viewer here and nothing starts afterwards. An episode shorter than `MIN_TOTAL_SECONDS` or without a next episode gets no card.

Threads: everything runs on the service's main thread (Player callbacks, the loop's ticks and the window's clicks are all delivered
there, inside `Monitor.waitForAbort`), so no locking. The window is shown non-modally so the loop keeps ticking while it is up.
"""

PROMPT_SECONDS = 30      # the card opens when this many seconds are left (when the site gives no usable credits time)
MIN_TOTAL_SECONDS = 300  # shorter items never get a card
NEAR_END_MARGIN = 15     # the service ticks every second from this many seconds before the card is due (it asks `near_end`)
MIN_LEAD_SECONDS, MAX_LEAD_SECONDS = 10, 180   # a credits time that would open the card outside this is not trusted
LENGTH_TOLERANCE_SECONDS = 60   # the site's episode length must be this close to the player's real one for its credits time to be trusted
CLOSE_TO_END_SECONDS = 10       # a stop this close to the end counts as the end (the player sometimes reports a stop instead of an end)

CLOSE_BUTTON, PLAY_BUTTON, PROGRESS = 3011, 3012, 3014   # control ids in idanplus-up-next.xml
SKIN_FILE, SKIN_NAME, SKIN_RESOLUTION = 'idanplus-up-next.xml', 'Default', '1080i'

HEADING = 'הפרק הבא'
BTN_PLAY = 'נגן עכשיו'
BTN_CLOSE = 'סגור'
COUNTDOWN = 'הפרק הבא מתחיל בעוד %d שניות'
HOLD_TEXT = 'ההפעלה האוטומטית כבויה'   # the line under the card when nothing will start by itself


class NextPrompt(object):
	"""One viewing's offer. `ui` has `show(entry, seconds_left)`, `update(seconds_left)`, `close()`; `play(entry, replace)` starts the
	next episode (`replace` True = the current one is still playing and must be stopped first).

	`credits_at` (seconds into the episode where the credits start) and `expected_total` (the site's own length of the episode) are optional
	hints from the site: the card then opens at the credits, `expected_total - credits_at` before the end, instead of `PROMPT_SECONDS`.
	They are used only when that lead is sane and the site's length matches the player's; anything else falls back to `PROMPT_SECONDS`."""

	def __init__(self, entry, ui, play, credits_at=None, expected_total=None, autoplay=True, show_card=True):
		self._entry, self._ui, self._play = entry, ui, play
		self._autoplay, self._show_card = autoplay, show_card
		self._credits_at, self._expected_total = credits_at, expected_total
		self._shown = self._dismissed = self._started = False

	def lead(self, total):
		"""Seconds before the end at which the card opens, for a player that reports `total`."""
		credits_at, expected = self._credits_at, self._expected_total
		if isinstance(credits_at, (int, float)) and not isinstance(credits_at, bool) and credits_at > 0:
			if expected is None:
				lead = total - credits_at
			elif abs(total - expected) <= LENGTH_TOLERANCE_SECONDS:
				lead = expected - credits_at
			else:
				return PROMPT_SECONDS
			if MIN_LEAD_SECONDS <= lead <= MAX_LEAD_SECONDS:
				return lead
		return PROMPT_SECONDS

	def near_end(self, position, total):
		"""True when the service should tick every second (the card is up or about to open, or a stop right before the end has to be recognised)."""
		if not (self._show_card or self._autoplay):
			return False
		return not self._dismissed and total >= MIN_TOTAL_SECONDS and 0 < total - position <= self.lead(total) + NEAR_END_MARGIN

	def tick(self, position, total):
		"""Feed the current position (the service does this every second once `near_end`)."""
		if self._dismissed or self._started or total < MIN_TOTAL_SECONDS or not self._show_card:
			return
		left = total - position
		if left > self.lead(total) or left <= 0:
			return
		if not self._shown:
			self._shown = True
			self._ui.show(self._entry, left, hold=not self._autoplay)
		elif self._autoplay:
			self._ui.update(left)   # in hold mode there is no countdown to update

	def play_now(self):
		"""The viewer pressed "Play now": the current episode is stopped and the next one starts."""
		if self._started:
			return
		self._started = True
		self._ui.close()
		self._play(self._entry, True)

	def dismiss(self):
		"""The viewer pressed "Close" (or Back): stay on this episode, start nothing."""
		self._dismissed = True
		self._ui.close()

	def ended(self):
		"""The item ran to its end by itself."""
		self._ui.close()
		if self._autoplay and not self._dismissed and not self._started:
			self._started = True
			self._play(self._entry, False)

	def stopped(self):
		"""The viewer stopped playback: take the card down, start nothing."""
		self._ui.close()


class KodiCard(object):
	"""The card window (`idanplus-up-next.xml`). Created and ticked on the service thread; its clicks call the bound prompt."""

	def __init__(self, addon_path):
		self._path = addon_path
		self._prompt = None
		self._window = None
		self._total = 1.0

	def bind(self, prompt):
		self._prompt = prompt

	def show(self, entry, seconds_left, hold=False):
		import xbmcgui
		listener = self._prompt
		self._total = max(1.0, seconds_left)

		class Window(xbmcgui.WindowXMLDialog):
			def __init__(self, *args, **kwargs):
				xbmcgui.WindowXMLDialog.__init__(self, *args)
				self._progress = None
				for key, value in kwargs['properties'].items():
					self.setProperty(key, value)

			def onInit(self):
				self._progress = self.getControl(PROGRESS)
				self._progress.setPercent(100.0)
				self.setFocusId(PLAY_BUTTON)

			def set_progress(self, percent):
				if self._progress is not None:
					self._progress.setPercent(max(0.0, min(100.0, percent)))

			def onClick(self, controlId):
				if controlId == PLAY_BUTTON:
					listener.play_now()
				elif controlId == CLOSE_BUTTON:
					listener.dismiss()

			def onAction(self, action):
				if action.getId() in (xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK):
					listener.dismiss()

		number = entry.get('number')
		properties = {
			'heading': HEADING, 'show_name': entry.get('series_title', ''), 'season_episode': 'פרק {0}'.format(number) if number is not None else '',
			'ep_title': entry['name'], 'thumb': entry.get('icon', ''), 'btn_play': BTN_PLAY, 'btn_close': BTN_CLOSE,
			'countdown': HOLD_TEXT if hold else COUNTDOWN % int(round(seconds_left)),
			'hide_progress': '1' if hold else '',
		}
		self._window = Window(SKIN_FILE, self._path, SKIN_NAME, SKIN_RESOLUTION, properties=properties)
		self._window.show()

	def update(self, seconds_left):
		if self._window is not None:
			self._window.setProperty('countdown', COUNTDOWN % int(round(seconds_left)))
			self._window.set_progress(100.0 * seconds_left / self._total)

	def close(self):
		window, self._window = self._window, None
		if window is not None:
			window.close()
