# -*- coding: utf-8 -*-
import re 
import resources.lib.common as common

module = 'hidabroot'

def WatchLive(channelID, name='', iconimage='', quality='best'):
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	channel = common.GetChannel(channelID)
	isAdaptive = common.GetChannelAdaptive(channel)
	linkDetails = channel.get('linkDetails')
	text = common.OpenURL(linkDetails['link'], headers=headers)
	match = re.compile('<source\s*?src="(.*?)"', re.S).findall(text)
	#text = common.OpenURL('https://go.shidur.net/player/testlive.php', headers=headers)
	#match = re.compile('hls\.loadSource\(["\'](.*?)["\']\)').findall(text)
	link = common.GetStreams(match[0], headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')