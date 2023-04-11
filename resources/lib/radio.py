# -*- coding: utf-8 -*-
import xbmc
import re
import resources.lib.common as common

module = 'radio'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = {
		'90fm': { 'link': 'http://live1.co.il/90fm/', 'regex': 'mp3:\s*"(.*?)"'},
		'91fm': { 'link': 'https://acdn.streamgates.net/91fm', 'final': True},
		'97fm': { 'link': 'https://www.ytn.co.il/radiodarom/97fm/', 'regex': '<video.*src="(.*?)"'},
		'891fm': { 'link': 'http://www.891fm.co.il/', 'regex': 'data-mp3="(.*?)"'},
		'1015fm': { 'link': 'https://www.ytn.co.il/radiodarom/1015fm/', 'regex': '<video.*src="(.*?)"'},
		'102fm': { 'link': 'https://102fm.co.il/', 'regex': "src:\s*'(.*?)'"},
		'102fmEilat': { 'link': 'https://www.fm102.co.il/LiveBroadcast', 'regex': 'mp3:\s*"(.*?)"'},
		'103fm': { 'link': 'http://103fm.maariv.co.il/include/OnLineView.aspx', 'regex': 'data-file="(.*?)"'},
		'1045fm': { 'link': 'https://1045fm.maariv.co.il/include/OnLineView.aspx', 'regex': 'data-file="(.*?)"'},
		'1075fm': { 'link': 'http://www.1075.fm/%d7%a0%d7%92%d7%9f/', 'regex': 'mp3:\s*"(.*?)"'},
		'kolhay': { 'link': 'https://media2.93fm.co.il/live-new', 'final': True},
		'kolhaymusic': { 'link': 'https://media2.93fm.co.il/livemusic', 'final': True},
		'kolbarama': { 'link': 'https://icy.streamgates.net/Radio_CDN/Kol_Barama/icecast.audio', 'final': True},
		'kolplay': { 'link': 'https://radio.streamgates.net/stream/kbmusic', 'final': True},
		'gly': { 'link': 'http://gly-audioswitch1.ecast.co.il/live', 'final': True},
		'mizrahit': { 'link': 'https://mizrahit.fm/', 'regex': '<aside id="sidebar">.*?data-audio="(.+?)"', 'flags': re.S},
		'ynet': { 'link': 'https://yradio.livecdn.biz/ynet-live', 'final': True}
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