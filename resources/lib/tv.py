# -*- coding: utf-8 -*-
import re
import resources.lib.common as common

module = 'tv'

def WatchLive(url, name='', iconimage='', quality='best'):
	channels = {
		'891fm': {'link': 'https://www.oles.tv/891fm/player/', 'regex': "streamSource\s*=\s*'(.*?)'"},
		'100fm': {'link': 'https://100fm.multix.co.il/', 'regex': "hls:\s*'(.*?)'", 'direct': 'https://video_cdn.streamgates.net/radios100fm/feed720/playlist.m3u8'},
		'11b': {'link': 'http://kan11.media.kan.org.il/hls/live/2024514/2024514/source1_2.5k/chunklist.m3u8', 'final': True},
		#'11b2': {'link': 'plugin://plugin.video.dailymotion_com/?url=x7wjmog&mode=playLiveVideo', 'final': True},
		'11b2': {'link': 'https://www.dailymotion.com/video/x7wjmog', 'final': True},
		#'11c2': {'link': 'https://www.dailymotion.com/video/x80xsiq', 'final': True},
		'n12': {'link': 'https://keshethlslive-lh.akamaihd.net/i/c2n_1@195269/index_3100_av-p.m3u8', 'final': True},
		'13b': {'link': 'https://d18b0e6mopany4.cloudfront.net/out/v1/08bc71cf0a0f4712b6b03c732b0e6d25/index.m3u8', 'referer': 'https://13tv.co.il/live/'},
		'23b': {'link': 'https://kan23.media.kan.org.il/hls/live/2024691/2024691/source1_2.5k/chunklist.m3u8', 'final': True},
		#'23b2': {'link': 'plugin://plugin.video.dailymotion_com/?url=k55PfgB8EU6SpzwA46D&mode=playLiveVideo', 'final': True},
		'23b2': {'link': 'https://www.dailymotion.com/video/k55PfgB8EU6SpzwA46D', 'final': True},
		'33b': {'link': 'https://makan.media.kan.org.il/hls/live/2024680/2024680/source1_2.5k/chunklist.m3u8', 'final': True},
		#'33b2': {'link': 'plugin://plugin.video.dailymotion_com/?url=k2slq6Tpsh2bm4wA43P&mode=playLiveVideo', 'final': True},
		'33b2': {'link': 'https://www.dailymotion.com/video/k2slq6Tpsh2bm4wA43P', 'final': True},
		'bbb': {'link': 'https://d2lckchr9cxrss.cloudfront.net/out/v1/c73af7694cce4767888c08a7534b503c/index.m3u8', 'referer': 'https://13tv.co.il/home/bb-livestream/', 'final': True},
		'musayof': {'link': 'http://wowza.media-line.co.il/Musayof-Live/livestream.sdp/playlist.m3u8', 'referer': 'http://media-line.co.il/Media-Line-Player/musayof/livePlayer.aspx'},
		'ynet': {'link': 'https://www.ynet.co.il/video/live/0,20658,1-5259927,00.html', 'regex': "progresivePath: function.*?return replacePath\(decodeURIComponent\('(.*?)'\).*?}", 'flags': re.S, 'direct': 'https://yitlivevid.mmdlive.lldns.net/yitlivevid/1dafd6053fb24d7fa905fb99eb4635be/manifest.m3u8'}
	}
	userAgent = common.GetUserAgent()
	headers={"User-Agent": userAgent}
	regex = channels[url].get('regex')
	if regex:
		text = common.OpenURL(channels[url]['link'], headers=headers)
		link = re.compile(regex, channels[url].get('flags', 0)).findall(text)
		if len(link) > 0:
			link = link[0]
		else:
			link = channels[url]['direct']
	else:
		link = channels[url]['link']
	if link.startswith('//'):
		link = 'http:{0}'.format(link)
	referer = channels[url].get('referer')
	if referer:
		headers['referer'] = referer
	if not channels[url].get('final') == True:
		link = common.GetStreams(link, headers=headers, quality=quality)
	if referer:
		common.PlayStream('{0}|User-Agent={1}&Referer={2}'.format(link, userAgent, referer), quality, name, iconimage)
	else:
		common.PlayStream('{0}|User-Agent={1}'.format(link, userAgent), quality, name, iconimage)

def Run(name, url, mode, iconimage='', moreData=''):
	if mode == 10:
		WatchLive(url, name, iconimage, moreData)
		
	common.SetViewMode('episodes')