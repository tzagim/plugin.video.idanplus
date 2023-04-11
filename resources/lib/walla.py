# -*- coding: utf-8 -*-
import re, json
import resources.lib.common as common

module = 'walla'
baseUrl = 'https://www.walla.co.il'

def WatchLive(name='', iconimage='', quality='best'):
	url = 'http://walla-metadata-rr-d.vidnt.com/live/walla/ulpan/hls/metadata.xml'
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	text = common.OpenURL(baseUrl, headers=headers)
	match = re.compile('id="iframePlayer"\s*src="(.*?)"').findall(text)
	if len(match) > 0:
		text = common.OpenURL('{0}{1}'.format(baseUrl, match[0]), headers=headers)
		match = re.compile("data-player='(.*?)'").findall(text)
		if len(match) > 0:
			jsn = json.loads(match[0])
			liveStream = jsn.get('liveStream', 'ulpan')
			url = 'http://walla-metadata-rr-d.vidnt.com/live/walla/{0}/hls/metadata.xml'.format(liveStream)
	text = common.OpenURL(url, headers=headers)
	if quality == 'best':
		#match = re.compile('FileURL bitrate="(\d*)".*?>\s*(.*?)\s*</FileURL>').findall(text)
		#url = match[-1][1].replace('amp;', '')
		resolutions = [x for x in re.compile('FileURL bitrate="(\d*)".*?>\s*(.*?)\s*</FileURL>').findall(text)]
		resolutions = sorted(resolutions,key=lambda resolutions: int(resolutions[0]), reverse=True)
		url = resolutions[0][1].replace('amp;', '')
	else:
		match = re.compile("<SmilURL.*>(.*?)</SmilURL>").findall(text)
		url = match[0].replace('amp;', '')
	match = re.compile("<Server priority=['\"]1['\"]>(.+)</Server>").findall(text)
	server = match[0]
	link = common.urlunparse(common.url_parse(url)._replace(netloc=server))
	link = common.GetStreams(link, headers=headers, quality=quality)
	common.PlayStream('{0}|User-Agent={1}'.format(link, userAgent), quality, name, iconimage)
	
def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(name, iconimage, moreData)
		
	common.SetViewMode('episodes')