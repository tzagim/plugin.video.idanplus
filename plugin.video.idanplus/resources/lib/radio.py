# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = 'radio'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = {
		'90fm': { 'link': 'http://live1.co.il/90fm/', 'regex': 'mp3:\s*"(.*?)"'},
		'91fm': { 'link': 'https://cdn.cybercdn.live/Lev_Hamedina/Audio/icecast.audio', 'final': True},
		'97fm': { 'link': 'https://cdn.cybercdn.live/Darom_97FM/Live/icecast.audio', 'final': True},
		'891fm': { 'link': 'http://www.891fm.co.il/', 'regex': 'data-mp3="(.*?)"'},
		'1015fm': { 'link': 'http://radio.2net.co.il/hatahana', 'regex': 'width="100%" src="(.*?)"'},
		'102fm': { 'link': 'https://102fm.co.il/', 'regex': "src:\s*'(.*?)'"},
		'102fmEilat': { 'link': 'https://www.fm102.co.il/LiveBroadcast', 'regex': 'mp3:\s*"(.*?)"'},
		'103fm': { 'link': 'http://103fm.maariv.co.il/include/OnLineView.aspx', 'regex': 'data-file="(.*?)"'},
		'1045fm': { 'link': 'https://1045fm.maariv.co.il/include/OnLineView.aspx', 'regex': 'data-file="(.*?)"'},
		'1075fm': { 'link': 'https://1075.livecdn.biz/radiohaifa', 'final': True},
		'kolhay': { 'link': 'https://media2.93fm.co.il/live-new', 'final': True},
		'kolhaymusic': { 'link': 'https://media2.93fm.co.il/livemusic', 'final': True},
		'kolbarama': { 'link': 'https://cdn.cybercdn.live/Kol_Barama/Live_Audio/icecast.audio', 'final': True},
		'kolplay': { 'link': 'https://cdn.cybercdn.live/Kol_Barama/Music/icecast.audio', 'final': True},
		'gly': { 'link': 'https://cdn.cybercdn.live/Galei_Israel/Live/icecast.audio', 'final': True},
		'mizrahit': { 'link': 'https://mzr.mediacast.co.il/mzradio','final': True},
		'fm995': { 'link': 'https://995.livecdn.biz/995fm','final': True}
	}
	
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	regex = channels[url].get('regex')
	if regex:
		text = common.OpenURL(channels[url]['link'], headers=headers)
		link = re.compile(channels[url]['regex'], channels[url].get('flags', 0)).findall(text)[0]
	else:
		link = channels[url]['link']
	if link.find('://') < 0:
		link = 'http://' + link

	final = '{0}|User-Agent={1}&verifypeer=false'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 11:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')