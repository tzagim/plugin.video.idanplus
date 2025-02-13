# -*- coding: utf-8 -*-
import resources.lib.common as common

module = 'knesset'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = {
		'99': 'https://kneset.gostreaming.tv/p2-kneset/_definst_/myStream/index.m3u8',
		'99c': 'https://kneset.gostreaming.tv/p2-Accessibility/_definst_/myStream/index.m3u8',
	}
	url = channels[url]
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	link = common.GetStreams(url, headers=headers, quality=quality)
	final = '{0}|User-Agent={1}'.format(link, userAgent)
	common.PlayStream(final, quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')
