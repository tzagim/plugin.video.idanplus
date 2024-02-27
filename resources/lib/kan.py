# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import re, json, os
import resources.lib.common as common

module = 'kan'
moduleIcon = common.GetIconFullPath("kan.jpg")
baseUrl = 'https://www.kan.org.il'
baseKidsUrl = 'https://www.kankids.org.il'
archiveUrl = 'https://archive.kan.org.il'
userAgent = common.GetUserAgent()
headers={"User-Agent": userAgent}
kanSeriesNamesFile = os.path.join(common.profileDir, 'kanSeriesNames.json')
kanSeriesNamesURL = 'https://bit.ly/kanSeriesNames'

def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 4, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התוכניות", bold=True, color="none")
	common.addDir(name, '{0}/lobby/kan11'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData=common.GetLocaleString(30602))
	name = common.GetLabelColor("תוכניות אקטואליה", bold=True, color="none")
	common.addDir(name, '{0}/lobby/newstv'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData=common.GetLocaleString(30602))
	name = common.GetLabelColor("דיגיטל", bold=True, color="none")
	common.addDir(name, '{0}/lobby/digital-lobby'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData=common.GetLocaleString(30602))
	name = common.GetLabelColor(common.GetLocaleString(30607), bold=True, color="none")
	common.addDir(name, '{0}/lobby/kan-kids'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData=common.GetLocaleString(30607))
	#name = common.GetLabelColor('{0} - אתר ישן'.format(common.GetLocaleString(30607)), bold=True, color="none")
	#common.addDir(name, 'https://www.kankids.org.il', 5, iconimage, infos={"Title": name}, module=module, moreData='{0} - אתר ישן'.format(common.GetLocaleString(30607)))
	name = common.GetLabelColor("כאן - ארכיון", bold=True, color="none")
	common.addDir(name, archiveUrl, 41, iconimage, infos={"Title": name}, module=module, moreData="כאן ארכיון")
	name = common.GetLabelColor("תכניות רדיו", bold=True, color="none")
	common.addDir(name, '', 21, iconimage, infos={"Title": name}, module=module)
	name = common.GetLabelColor("פודקאסטים", bold=True, color="none")
	common.addDir(name, '', 31, iconimage, infos={"Title": name}, module=module)
	name = common.GetLabelColor("פודקאסטים לילדים", bold=True, color="none")
	common.addDir(name, '', 33, iconimage, infos={"Title": name}, module=module)

def GetSeriesList(url, catName):
	text = common.GetCF(url, userAgent)
	if not ('kankids' in url):
		kanSeriesNames = common.GetUpdatedList(kanSeriesNamesFile, kanSeriesNamesURL, headers={'Referer': 'http://idan-{0}.Kodi-{1}.fish'.format(common.AddonVer, common.GetKodiVer())}, deltaInSec=86400, isZip=True)
		matches = re.compile('digitalSeries:.*?\[(.*?)}\]', re.S).findall(text)
		if len(matches) > 0:
			matches = json.loads('{"series":['+matches[0].strip()+'}]}')
			for serie in matches['series']:
				link = serie['Url']
				image = common.quoteNonASCII(serie['Image'])
				description = serie['Description']
				name = kanSeriesNames.get(link)
				if name is None:
					name = link[link.rfind('/', 0, len(link)-1)+1:len(link)-1].replace('-', ' ')
				name = common.GetLabelColor(name, keyColor="prColor", bold=True)
				if not link.startswith('http'):
					link = '{0}{1}'.format(baseUrl, link)
				common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
			return
		else:
			links = []
			#matches = re.compile('<div class="block-media card-media ">(.*?)</button>', re.S).findall(text)
			matches = re.compile('"background-image: url\((.*?)\).*?"h1">(.*?)</h.*?"info-description">(.*?)</div>.*?<a href="(.*?)"', re.S).findall(text)
			for match in matches:
				link = match[3]
				if link in links:
					continue
				links += [link]
				image = common.quoteNonASCII(common.UnEscapeXML(match[0]))
				name = common.GetLabelColor(common.UnEscapeXML(match[1].strip()), keyColor="prColor", bold=True)
				description = common.UnEscapeXML(match[2].strip())
				common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
			matches = re.compile('"section-title">עוד אקטואליה(.*?)</ul>', re.S).findall(text)
			matches = re.compile('<li>.*?<a href="(.*?)".*?<img src="(.*?)".*?"font-weight-normal">(.*?)</.*?</li>', re.S).findall(matches[0])
			for match in matches:
				link = match[0]
				if link in links:
					continue
				links += [link]
				image = common.quoteNonASCII(common.UnEscapeXML(match[1]))
				description = common.UnEscapeXML(match[2].strip())
				name = common.GetLabelColor(description, keyColor="prColor", bold=True)
				common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
			return
	
	text = common.OpenURL(url, headers=headers)
	matches = re.compile('<div class="component_sm_item news">(.*?)</a>', re.S).findall(text)
	for match in matches:
		m = re.compile('<a.*?href="(.+?)".+?"background-image: url\(\'(.+?)\'\);.*?"\s*title="(.*?)">.*?"news_up_txt">(.*?)</div>', re.S).findall(match)
		AddSeries(m, catName)
	
	matches = re.compile('<a class="magazine_info_link w-inline-block.+?href=\'(.+?)\'.+?"background-image: url\(\'(.+?)\'\);.+?"magazine_info_title">(.*?)</h2>.*?"magazine_info_txt">(.*?)</div>', re.S|re.I).findall(text)
	AddSeries(matches, catName)
	for match in matches:
		item = match[0]
		description = match[1]
		m = re.compile('url\(\'(.+?)\'\);.+?href=".+?/Program/\?catId=(.+?)["\'].+?class="it_small_title">(.*?)</div>', re.S|re.I).findall(item)
		if len(m) == 0:
			continue
		iconimage, id, name = m[0]
		name = common.GetLabelColor(name.strip(), keyColor="prColor", bold=True)
		common.addDir(name, id, 6, iconimage, infos={"Title": name, "Plot": description.strip(),'mediatype': 'movie'}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})

def GetSubCategoriesList(url, catName):
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url)
	matches = re.compile('class="gallery_sec\s*w-clearfix(.+?)<script>', re.S).findall(text)
	for match in matches:
		m = re.compile('img src="(.*?)".*?<h2.*?>(.*?)</h2>.*?<a href=\'(.*?)\'.*?/a>', re.S).findall(match)
		if len(m) < 1:
			continue
		iconimage, name, url = m[0]
		name = common.GetLabelColor(name.strip(), keyColor="prColor", bold=True)
		common.addDir(name, url, 1, iconimage, infos={"Title": name}, module=module, urlParamsData={'catName': catName})

def AddSeries(matches, catName):
	for link, iconimage, name, description in matches:
		i = link.lower().find('catid=')
		if i > 0:
			link = link[i+6:]
		elif 'page.aspx' in link.lower():
			try:
				t = common.GetCF(link, userAgent)
				#t = common.OpenURL(link)
				m = re.compile('magazine_info_link w-inline-block\s*"\s*href=\'.*?catid=(.*?)&').findall(t)
				link = m[0]
			except:
				pass
		name = common.GetLabelColor(name.strip(), keyColor="prColor", bold=True)
		common.addDir(name, link, 6, common.quoteNonASCII(iconimage), infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})

def GetSeasonsList(data, iconimage, moreData=''):
	d = data.split(';')
	catId = d[0]
	md = moreData.split('|||')
	site = md[0]
	catName = '' if len(md) < 2 else md[1]
	domain = baseKidsUrl if 'kankids' in data else baseUrl

	if site == 'youtube':
		xbmc.executebuiltin('container.Update({0}/playlist/{1}/)'.format(common.youtubePlugin, catId))
		return

	text = common.GetCF(data)
	seasons = re.compile('<div class="dropdown">(.*?)</div>', re.S).findall(text)
	if len(seasons) == 0:
		GetEpisodesList(data, iconimage, moreData)
		return
	
	seasons = re.compile('href="(.*?)">(.*?)</a>', re.S).findall(seasons[0])
	for season in seasons:
		description = common.UnEscapeXML(season[1].strip())
		name = common.GetLabelColor(description, keyColor="prColor")
		link = season[0]
		if not link.startswith('http'):
			link = '{0}{1}'.format(domain, link)
		common.addDir(name, link, 2, iconimage, infos={"Title": name, "Plot": description}, module=module, urlParamsData={'catName': catName})

def GetEpisodesList(url, iconimage, moreData=''):
	md = moreData.split('|||')
	site = md[0]
	catName = '' if len(md) < 2 else md[1]
	text = common.GetCF(url)
	body = re.compile('<main id="main"(.*?)</main>', re.S).findall(text)
	if 'kankids' in url:
		matches = re.compile('class="seasons"(.*?)<script', re.S).findall(body[0])
		domain = baseKidsUrl
	else:
		matches = re.compile('class="seasons">(.*?)<div class="ec-section section', re.S).findall(body[0])
		domain = baseUrl
	if len(matches) > 0:
		episodes = re.compile('<li(.*?)</li>', re.S).findall(matches[0])
		for item in episodes:
			episode = re.compile('href="(.*?)".*?img src="(.*?)".*?"card-body">(.*?)</a>', re.S).findall(item)[0]
			name = re.compile('"card-title">(.*?)</div>', re.S).findall(episode[2])
			name = common.GetLabelColor(common.UnEscapeXML(name[0].strip()), keyColor="chColor")
			description = re.compile('"card-text">(.*?)</div>', re.S).findall(episode[2])
			description = common.UnEscapeXML(description[0].strip()) if len(description) > 0 else ''
			image = common.quoteNonASCII(common.UnEscapeXML(episode[1]))
			link = episode[0]
			if not link.startswith('http'):
				link = '{0}{1}'.format(domain, link)
			common.addDir(name, link, 3, image, infos={"Title": name, "Plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
	else:
		matches1 = re.compile('<div class="block-media card-media(.*?)</div>\s*?</div>\s*?</div>\s*?</div>', re.S).findall(body[0])
		#matches = re.compile('<div class="media-wrap(.*?)<div class="ec-section section', re.S).findall(body[0])
		if len(matches1) > 0:
			matches = re.compile('desktop-vod-bg-image: url\(\'(.*?)\'\).*?"title.*?>(.*?)</h(.*?"info-description">(.*?)</div>.*?|.*?)<a href="(.*?)"', re.S).findall(matches1[0])
			if len(matches) < 1:
				matches = re.compile('desktop-vod-bg-image: url\(\'(.*?)\'\).*?"d-md-none.*?>(.*?)</.*?(.*?"info-description">(.*?)</div>.*?|.*?)<a href="(.*?)"', re.S).findall(matches1[0])
			name = common.GetLabelColor(common.UnEscapeXML(matches[0][1].strip()), keyColor="chColor")
			description = common.UnEscapeXML(matches[0][3].strip())# if len(matches[0]) > 4 ''
			link = '{0}/{1}'.format(domain, matches[0][4])# if len(matches[0]) > 4 else '{0}/{1}'.format(domain, matches[0][2])
			common.addDir(name, link, 3, common.quoteNonASCII(matches[0][0]), infos={"Title": name, "Plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
		else:
			matches = re.compile('<div class="youtube-player(.*?)<div class="ec-section section', re.S).findall(body[0])
			matches = re.compile('data-video-src="(.*?)".*?"h2">(.*?)</h2>.*?"info-description">(.*?)</div>', re.S).findall(matches[0])
			name = common.GetLabelColor(common.UnEscapeXML(matches[0][1].strip()), keyColor="chColor")
			description = common.UnEscapeXML(matches[0][2].strip())
			url = matches[0][0].replace('/embed', '')
			common.addDir(name, matches[0][0].replace('/embed', ''), 3, iconimage, infos={"Title": name, "Plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})

def GetKidsEpisodesList(data, iconimage, moreData=''):
	d = data.split(';')
	catId = d[0]
	page = 0 if len(d) < 2 else int(d[1])
	stopPage = page + pagesPerList
	prevPage = page - pagesPerList if page  >= pagesPerList else 0
	while True:
		page += 1
		url = 'https://www.kankids.org.il/program/getMoreProgram.aspx?count={0}&catId={1}'.format(page, catId)
		text = common.GetCF(url, userAgent).replace('\u200b', '')
		#text = common.OpenURL(url)
		matches = re.compile('program_list_videoblock">.*?url\(\'(.*?)\'\).*?"application/json">(.*?)</script>.*?"content_title">(.*?)</h2>.*?<p>(.*?)</p>', re.S).findall(text)
		for image, link, name, description in matches:
				name = common.GetLabelColor(common.UnEscapeXML(name.replace('\r', '').replace('\n', '').strip()), keyColor="chColor")
				description = common.UnEscapeXML(description.replace('\r', '').replace('\n', '').strip())
				link = json.loads(link)['items'][0]['html']
				link = re.compile('src="(.*?)"').findall(link)[0]
				if 'kaltura' in link:
					link = re.compile('entry_id=(.*?)"').findall(link+'"')[0]
					link = 'kaltura:{0}'.format(link)
				common.addDir(name, link, 3, image, infos={"Title": name, "Plot": description}, module=module, isFolder=False, isPlayable=True, urlParamsData={'catName': 'חינוכית 23'})
		if len(matches) < 9:
			if page > pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(catId, prevPage), 6, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'חינוכית 23'})
			break
		if page == stopPage:
			if page > pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(catId, prevPage), 6, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'חינוכית 23'})
			name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
			common.addDir(name, '{0};{1}'.format(catId, page), 6, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'חינוכית 23'})
			break
		
def GetRadioCategoriesList(iconimage):
	name = common.GetLabelColor("כאן ב", bold=True, color="none")
	common.addDir(name, 'kan-b', 22, common.GetIconFullPath("bet.png"), infos={"Title": name}, module=module)
	name = common.GetLabelColor("כאן גימל", bold=True, color="none")
	common.addDir(name, 'kan-gimel', 22, common.GetIconFullPath("gimel.png"), infos={"Title": name}, module=module)
	name = common.GetLabelColor("כאן 88", bold=True, color="none")
	common.addDir(name, 'kan-88', 22, common.GetIconFullPath("88.png"), infos={"Title": name}, module=module)
	name = common.GetLabelColor("כאן תרבות", bold=True, color="none")
	common.addDir(name, 'kan-tarbut', 22, common.GetIconFullPath("culture.png"), infos={"Title": name}, module=module)
	name = common.GetLabelColor("כאן קול המוסיקה", bold=True, color="none")
	common.addDir(name, 'kan-music', 22, common.GetIconFullPath( "music.png"), infos={"Title": name}, module=module)
	name = common.GetLabelColor("כאן מורשת", bold=True, color="none")
	common.addDir(name, 'kan-moreshet', 22, common.GetIconFullPath("moreshet.png"), infos={"Title": name}, module=module)
	name = common.GetLabelColor("כאן Reka", bold=True, color="none")
	common.addDir(name, 'kan-reka', 22, common.GetIconFullPath("reka.png"), infos={"Title": name}, module=module)

def GetRadioSeriesList(url, catName):
	text = common.GetCF('{0}/content/kan/{1}/'.format(baseUrl, url), userAgent)
	#text = common.OpenURL(url)
	match = re.compile('<div class="tab-pane fade show active(.*?)</ul>', re.S).findall(text)
	matches = re.compile('<a href="(.*?)".*?background-image: url\((.*?)\).*?"card-title">(.*?)</.*?"text-on-hover">.*?<div>(.*?)</div>.*?</li>', re.S).findall(match[0])
	for link, iconimage, name, description in matches:
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="prColor", bold=True)
		common.addDir(name, link, 23, common.UnEscapeXML(iconimage), infos={"Title": name, "Plot": common.UnEscapeXML(description)}, module=module, moreData=catName, urlParamsData={'catName': catName})

def GetRadioEpisodesList(data, iconimage, catName):
	d = data.split(';')
	progUrl = d[0]
	page = 0 if len(d) < 2 else int(d[1])
	stopPage = page + pagesPerList
	prevPage = page - pagesPerList if page >= pagesPerList else 0
	while True:
		page += 1
		url = '{0}?currentPage={1}'.format(progUrl, page)
		text = common.GetCF(url, userAgent)
		#text = common.OpenURL(url)
		matches = re.compile('radio-title">(.*?)</h3>.*?data-player-src="(.*?)"', re.S).findall(text)
		for name, link in matches:
			name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="chColor")
			common.addDir(name, '{0}|||radio'.format(link), 3, iconimage, infos={"Title": name}, module=module, moreData='best', isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
		if len(matches) < 10:
			if page > pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 23, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': catName})
			break
		if page == stopPage:
			if page > pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 23, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': catName})
			name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
			common.addDir(name, '{0};{1}'.format(progUrl, page), 23, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': catName})
			break

def Play(url, name='', iconimage='', quality='best'):
	u = url.split('|||')
	url = u[0]
	if (common.GetAddonSetting("kanPreferYoutube") != "true") and (len(u) > 1) and ('youtube' in url or 'youtu.be' in url):
		text = common.GetCF('{0}/Item/?itemId={1}'.format(baseUrl, u[1]), userAgent)
		#text = common.OpenURL('{0}/Item/?itemId={1}'.format(baseUrl, u[1]))
		match = re.compile('<script class="w-json" type="application/json">(.*?)</script>').findall(text)
		match = re.compile('src=\\\\"(.*?)\\\\"').findall(match[0])
		if len(match) == 1:
			url = match[0]
	if 'youtube' in url or 'youtu.be' in url:
		final = common.GetYouTube(url)
	elif (len(u) > 1) and (u[1] == 'radio'):
		final = '{0}|User-Agent={1}'.format(url, userAgent)
	elif 'omny.fm' in url:
		#text = common.OpenURL(url)
		text = common.GetCF(url, userAgent)
		matches = re.compile('AudioUrl":"(.+?)"').findall(text)
		if len(matches) == 0:
			return
		#final = 'https://omny.fm{1}'.format(matches[-1])
		#final = '{0}{1}'.format(url[:-1], '.mp3')
		final = '{0}|User-Agent={1}'.format(matches[-1], userAgent)
		#final = url
	elif 'kan/podcasts' in url:
		text = common.GetCF(url, userAgent)
		matches = re.compile('data-player-src="(.*?)"').findall(text)
		final = '{0}|User-Agent={1}'.format(matches[-1], userAgent)
	elif 'kaltura' in url:
		link = common.GetKaltura(url.replace('kaltura:', ''), 2717431, baseUrl, userAgent, quality=quality)
		final = '{0}|User-Agent={1}'.format(link, userAgent)
	else:
		final = GetPlayerKanUrl(url, headers=headers, quality=quality)
	
	listitem = xbmcgui.ListItem(path=final)
	listitem.setInfo(type="Video", infoLabels={"Title": name})
	xbmcplugin.setResolvedUrl(handle=common.GetHandle(), succeeded=True, listitem=listitem)

def GetPlayerKanUrl(url, headers={}, quality='best'):
	url = url.replace('https', 'http')
	i = url.rfind('http://')
	if i > 0:
		url = url[i:]
	url = url.replace('HLS/HLS', 'HLS')
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url, headers=headers)
	if 'kanPlayers' in url:
		match = re.compile("dailymotion.*?video:\s*?'(.*?)'", re.S).findall(text)
		return 'dailymotion-video/{0}|'.format(match[0])
	elif 'ByPlayer' in url:
		match = re.compile('bynetURL:\s*"(.*?)"').findall(text)
		if len(match) == 0:
			match = re.compile('"UrlRedirector":"(.*?)"').findall(text)
		link = match[0].replace('https', 'http').replace('\u0026', '&')
	elif len(re.compile('media\.(ma)?kan\.org\.il').findall(url)) > 0:
		match = re.compile('hls:\s*?"(.*?)"').findall(text)
		link = match[0]
	elif 'kaltura' in url:
		text = common.GetCF(url, userAgent)
		#text = common.OpenURL(url, headers=headers)
		match = re.compile('window\.kalturaIframePackageData\s*=\s*{(.*?)};').findall(text)
		result = json.loads('{'+match[0]+'}')
		link = result['entryResult']['meta']['hlsStreamUrl']
		link = common.GetStreams(link, headers=headers, quality=quality)
	else:
		'''
		match = re.compile("var\s*metadataURL\s*?=\s*?'(.+?)'").findall(text)
		text = common.GetCF(match[0].replace('https_streaming=true', 'https_streaming=false'), userAgent)
		#text = common.OpenURL(match[0].replace('https_streaming=true', 'https_streaming=false'), headers=headers)
		match = re.compile("<SmilURL.*>(.+)</SmilURL>").findall(text)
		smil = match[0].replace('amp;', '')
		match = re.compile("<Server priority=['\"]1['\"]>(.+)</Server>").findall(text)
		server = match[0]
		link = common.urlunparse(common.url_parse(smil)._replace(netloc=server))
		'''
		match = re.compile('<div id="video_item".*?data-entryId="(.*?)"', re.S).findall(text)
		if len(match) > 0:
			domain = baseKidsUrl if 'kankids' in url else baseUrl
			link = common.GetKaltura(match[0], 2717431, domain, userAgent, quality=quality)
		else:
			match = re.compile('data-video-src="(.*?)"').findall(text)
			return common.GetYouTube(match[0].replace('/embed', ''))
	if 'api.bynetcdn.com/Redirector' not in link:
		link = common.GetStreams(link, headers=headers, quality=quality)
	return '{0}|User-Agent={1}'.format(link, userAgent)

def WatchLive(url, name='', iconimage='', quality='best', type='video'):
	channels = {
		#'11': '{0}/live/tv.aspx?stationid=2'.format(baseUrl),
		'11': 'https://kan11.media.kan.org.il/hls/live/2024514/2024514/master.m3u8',
		#'11c': '{0}/live/tv.aspx?stationid=23'.format(baseUrl),
		'11c': 'https://kan11sub.media.kan.org.il/hls/live/2024678/2024678/master.m3u8',
		#'23': '{0}/live/tv.aspx?stationid=20'.format(baseUrl),
		'23': 'https://kan23.media.kan.org.il/hls/live/2024691/2024691/master.m3u8',
		#'33': 'https://www.makan.org.il/live/tv.aspx?stationid=25',
		'33': 'https://makan.media.kan.org.il/hls/live/2024680/2024680/master.m3u8',
		#'kan4K': '{0}/live/tv.aspx?stationid=18'.format(baseUrl),
		#'wfb2019': '{0}/Item/?itemId=53195'.format(baseUrl),
		#'yfb2019': '{0}/Item/?itemId=52450'.format(baseUrl),
		#'bet': '{0}/radio/player.aspx?stationId=3'.format(baseUrl),
		'bet': 'https://kanbet.media.kan.org.il/hls/live/2024811/2024811/playlist.m3u8',
		#'gimel': '{0}/radio/player.aspx?stationid=9'.format(baseUrl),
		'gimel': 'https://kangimmel.media.kan.org.il/hls/live/2024813/2024813/playlist.m3u8',
		#'culture': '{0}/radio/player.aspx?stationid=5'.format(baseUrl),
		'culture': 'https://kantarbut.media.kan.org.il/hls/live/2024816/2024816/playlist.m3u8',
		#'88': '{0}/radio/player.aspx?stationid=4'.format(baseUrl),
		'88': 'https://kan88.media.kan.org.il/hls/live/2024812/2024812/playlist.m3u8',
		#'moreshet':'{0}/radio/player.aspx?stationid=6'.format(baseUrl),
		'moreshet':'https://kanmoreshet.media.kan.org.il/hls/live/2024814/2024814/playlist.m3u8',
		#'music': '{0}/radio/player.aspx?stationid=7'.format(baseUrl),
		'music': 'https://kankolhamusica.media.kan.org.il/hls/live/2024817/2024817/playlist.m3u8',
		#'kankids': 'https://www.kankids.org.il/radio/radio-kids.aspx',
		'kankids': '',
		#'reka': '{0}/radio/player.aspx?stationid=10'.format(baseUrl),
		'reka': 'https://kanreka.media.kan.org.il/hls/live/2024815/2024815/playlist.m3u8',
		#'makan': '{0}/radio/player.aspx?stationId=13'.format(baseUrl)
		'makan': 'https://makanradio.media.kan.org.il/hls/live/2024818/2024818/playlist.m3u8'
		#'persian': 'http://farsi.kan.org.il/',
		#'nos': '{0}/radio/radio-nos.aspx'.format(baseUrl),
		#'oriental': '{0}/radio/oriental.aspx'.format(baseUrl),
		#'international': '{0}/radio/radio-international.aspx'.format(baseUrl)
	}
	channelUrl = channels[url]
	#text = common.GetCF(url, userAgent)
	#text = common.OpenURL(channelUrl, headers=headers)
	'''
	if text is None:
		return
	if url == 'persian':
		match = re.compile('id="playerFrame".*?src="(.*?)"', re.S).findall(text)
	elif '?itemId=' in channelUrl:
		match = re.compile('<div class=\'videoWrapper\'><iframe.*?src="(.*?)"').findall(text)
	elif type == 'video':
		match = re.compile('<iframe.*id="streamIframe" data-src="(.+?)"').findall(text)
		if len(match) == 0: 
			match = re.compile('<iframe.*class="embedly-embed".*src="(.+?)"').findall(text)
	else:
		match = re.compile('<div class="player_content">.*?iframe src="(.*?)"', re.S).findall(text)
		if len(match) == 0:
			match = re.compile('iframeLink\s*?=\s*?"(.*?)"').findall(text)
	if 'dailymotion' in match[0]:
		#id = re.compile('.*?video/(.*?)\?').findall(match[0])
		#link = 'plugin://plugin.video.dailymotion_com/?url={0}&mode=playLiveVideo'.format(id[0])
		link = match[0]
	else:
		link = GetPlayerKanUrl(match[0], headers=headers, quality=quality)
	'''
	#Play(channelUrl, name, iconimage, quality)
	#link = common.GetKaltura(channelUrl, 2717431, baseUrl, userAgent)
	link = common.GetStreams(channelUrl, quality=quality)
	common.PlayStream(link, quality, name, iconimage)

def GetPodcastsList(iconimage):
	url = '{0}/lobby/aod/'.format(baseUrl)
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url)
	matches = re.compile('class="podcast-item".*?<a href="(.*?)".*?title="(.*?)".*?src="(.*?)".*?"text">(.*?)</div>', re.S).findall(text)
	for link, name, image, description in matches:
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="prColor", bold=True)
		common.addDir(name, link, 32, common.UnEscapeXML(image), infos={"Title": name, "Plot": common.UnEscapeXML(description.strip())}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})

def GetPodcastEpisodesList(data, iconimage):
	d = data.split(';')
	progUrl = d[0]
	page = 0 if len(d) < 2 else int(d[1])
	stopPage = page + pagesPerList
	prevPage = page - pagesPerList if page >= pagesPerList else 0
	while True:
		page += 1
		url = '{0}?currentPage={1}'.format(progUrl, page)
		text = common.GetCF(url, userAgent)
		#text = common.OpenURL(url)
		body = re.compile('<div class="card card-row">(.*?)</li>', re.S).findall(text)
		for b in body:
			matches = re.compile('href="(.*?)".*?src="(.*?)".*?"card-title">(.*?)</h.*?description">(.*?)</div>', re.S).findall(b)
			for link, image, name, description in matches:
				name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="chColor")
				common.addDir(name, link, 3, common.UnEscapeXML(image), infos={"Title": name, "Plot": common.UnEscapeXML(description.strip())}, module=module, isFolder=False, isPlayable=True, urlParamsData={'catName': 'כאן פודקאסטים'})
		if len(body) < 8:
			if page > pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 32, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
			break
		if page == stopPage:
			if page > pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 32, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
			name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
			common.addDir(name, '{0};{1}'.format(progUrl, page), 32, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
			break

def GetKidsPodcastsList():
	text = common.GetCF('https://kankids.azurewebsites.net/page.aspx?landingPageId=1275', userAgent)
	#text = common.OpenURL('https://kankids.azurewebsites.net/page.aspx?landingPageId=1275')
	matches = re.compile('class="video_it_full.*?url\(\'(.*?)\'\).+?href=\'.+?\?progId=(.+?)\'.*?sm_il_videotitle">(.*?)<.*?sm_it_videotxt">(.*?)<', re.S|re.I).findall(text)
	for image, id, name, description in matches:
		name = common.GetLabelColor(name.strip(), keyColor="prColor", bold=True)
		common.addDir(name, id, 34, image, infos={"Title": name, "Plot": description.replace('&nbsp;', '').strip()}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})

def GetKidsPodcastEpisodesList(data, iconimage):
	d = data.split(';')
	progId = d[0]
	page = -1 if len(d) < 2 else int(d[1])
	stopPage = page + 1 + pagesPerList
	prevPage = page - pagesPerList if page  >= pagesPerList else -1
	while True:
		page += 1
		url = 'https://www.kankids.org.il/Podcast/getMorePodcasts.aspx?index={0}&leftToRight=0&progId={1}'.format(page, progId)
		text = common.GetCF(url, userAgent)
		#text = common.OpenURL(url)
		matches = re.compile('<iframe src="(.+?)embed.+?<h2.+?>(.+?)</h2>.+?<p.+?>(.*?)</p>', re.S).findall(text)
		for link, name, description in matches:
			name = common.GetLabelColor(name.strip(), keyColor="chColor")
			common.addDir(name, link, 3, iconimage, infos={"Title": name, "Plot": description.replace('&nbsp;', '').strip()}, module=module, isFolder=False, isPlayable=True, urlParamsData={'catName': 'כאן פודקאסטים'})
		if len(matches) < 10:
			if page >= pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(progId, prevPage), 34, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
			break
		if page + 1 == stopPage:
			if page >= pagesPerList:
				name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
				common.addDir(name, '{0};{1}'.format(progId, prevPage), 34, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
			name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
			common.addDir(name, '{0};{1}'.format(progId, page), 34, iconimage, infos={"Title": name, "Plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
			break

def GetArchiveCategoriesList(url, iconimage, catName):
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url)
	matches = re.compile('id="mainNav">(.*?)</ul>', re.S).findall(text)
	matches = re.compile('<a class="nav-link" href="(.*?)".*?>\s*?(.*?)</a>', re.S).findall(matches[0])
	for url, name in matches:
		if url == '/main/about/' or url == '/main/zinuk-podcast/':
			continue
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="prColor", bold=True)
		common.addDir(name, '{0}/{1}'.format(archiveUrl, url), 42, iconimage, infos={"Title": name}, module=module, urlParamsData={'catName': catName})

def GetArchiveSeriesList(url, iconimage, catName):
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url)
	series = re.compile('<div class="archiveItem topImg articlePage">\s*<div class="embed-responsive embed-responsive-16by9">.*?"background-image:url\((.*?)\);".*?<a href="(.*?)" title="(.*?)".*?<p class="spoiler">(.*?)</p>', re.S).findall(text)
	
	matches = re.compile('<div role="main"(.*?)</section>', re.S).findall(text)
	if len(matches) == 0:
		return
	matches = re.compile('<ul class="navbar-nav categoriesMenu">(.*?)</ul>', re.S).findall(matches[0])
	if len(matches) == 0:
		for icon, url, name, description in series:
			if url == '/main/vod/':
				continue
			name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="prColor", bold=True)
			icon = '{0}/{1}'.format(archiveUrl,icon)
			description = common.UnEscapeXML(description.strip())
			#icon = iconimage
			#description = ''
			common.addDir(name, '{0}/{1}'.format(archiveUrl, url), 43, icon, infos={"Title": name, "Plot": description}, module=module, urlParamsData={'catName': catName})
		return
	matches = re.compile('href="/(.*?)" title="(.*?)">', re.S).findall(matches[0])
	for url, name in matches:
		if url == 'main/vod/':
			continue
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="prColor", bold=True)
		serie = [serie for serie in series if serie[1] == '/'+url]
		if len(serie) > 0:
			icon = '{0}/{1}'.format(archiveUrl, serie[0][0])
			description = common.UnEscapeXML(serie[0][3].strip())
		else:
			icon = iconimage
			description = ''
		common.addDir(name, '{0}/{1}'.format(archiveUrl, url), 43, icon, infos={"Title": name, "Plot": description}, module=module, urlParamsData={'catName': catName})

def GetArchiveEpisodesList(url, iconimage, catName):
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url)
	GetArchiveEpisodes(url, iconimage, text, catName)

def GetArchiveEpisodes(url, iconimage, text, catName):
	j = url.find('?')
	_url = url if j < 0 else url[:j]
	matches = re.compile('<section class="PageSection categoryPage(.*?)</section>', re.S).findall(text)
	if len(matches) == 0:
		return
	matches = re.compile('<a title="(.*?)" href="(.*?)".*?"background-image:url\((.*?)\);".*?</a>(.*?)</div>\s*?</div>', re.S).findall(matches[0])
	for name, url, image, rest in matches:
		m = re.compile('entry_id=(.*)').findall(url)
		if len(m) != 0:
			entryId = 'kaltura:' + m[0]
		else:
			entryId = url
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="chColor")
		match = re.compile('<h4>(.*?)</h4>').findall(rest)
		if len(match) == 0:
			match = re.compile('<p class="spoiler">(.*?)</p>').findall(rest)
		description = common.UnEscapeXML(match[0]) if len(match) == 1 else ""
		image = common.quoteNonASCII(image)
		if image.startswith('http') == False:
			image = '{0}{1}'.format(archiveUrl, image)
		common.addDir(name, common.encode(entryId, 'utf-8').replace('​&amp;', '&'), 3, image, infos={"Title": name, "Plot": description.replace('&nbsp;', '').strip()}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
	matches = re.compile('<ul class="pagination">(.*?)</div>', re.S).findall(text)
	if len(matches) < 1:
		return
	page = int(re.compile('<span class="page-link curPage">(.*?)</span>').findall(matches[0])[0])
	li = re.compile('<li(.*?)>(.*?)</li>', re.S).findall(matches[0])
	last = re.compile('<a.*?page=(.*?)"').findall(li[-1][1])
	pages = int(last[0]) if len(last) > 0 else page

	if page > 1:
		name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
		common.addDir(name, '{0}?page={1}'.format(_url, page-1), 43, iconimage, infos={"Title": name, "Plot": name}, module=module)
	if pages > page:
		name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
		common.addDir(name, '{0}?page={1}'.format(_url, page+1), 43, iconimage, infos={"Title": name, "Plot": name}, module=module)
	if pages > 1:
		name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
		common.addDir(name, '{0}?p={1}&pages={2}'.format(_url, page, pages), 44, iconimage, infos={"Title": name, "Plot": name}, module=module)
	
def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy, bitrate, pagesPerList
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	pagesPerList = int(common.GetAddonSetting("kanPagesPerList"))
	
	if mode == 0:	#------------- Categories: ----------------------
		GetCategoriesList(moduleIcon)
	elif mode == 5:	#------------- Sub-Categories: ------------------
		GetSubCategoriesList(url, moreData)
	elif mode == 1:	#------------- Series: -------------------------
		GetSeriesList(url, moreData)
	elif mode == 7:	#------------- Seasons: ------------------------
		GetSeasonsList(url, iconimage, moreData)
	elif mode == 2:	#------------- Episodes: ------------------------
		GetEpisodesList(url, iconimage, moreData)
	elif mode == 6:	#------------- Kids Episodes: -------------------
		GetKidsEpisodesList(url, iconimage, moreData)
	elif mode == 3:	#------------- Playing episode  -----------------
		Play(url, name, iconimage, moreData)
	elif mode == 4:	#------------- Toggle Lists' sorting method -----
		common.ToggleSortMethod('kanSortBy', sortBy)
	elif mode == 21: #------------- Radio Categories: ---------------
		GetRadioCategoriesList(moduleIcon)
	elif mode == 22: #------------- Radio Series: -------------------
		GetRadioSeriesList(url, common.GetUnColor(name))
	elif mode == 23: #------------- Radio Episodes: -----------------
		GetRadioEpisodesList(url, iconimage, moreData)
	elif mode == 31: #------------- Podcast Series: -----------------
		GetPodcastsList(moduleIcon)
	elif mode == 32: #------------- Podcast Episodes: ---------------
		GetPodcastEpisodesList(url, iconimage)
	elif mode == 33: #------------- Kids Podcast Series: ------------
		GetKidsPodcastsList()
	elif mode == 34: #------------- Kids Podcast Episodes: ------------
		GetKidsPodcastEpisodesList(url, iconimage)
	elif mode == 10:
		WatchLive(url, name, iconimage, moreData, type='video')
	elif mode == 11:
		WatchLive(url, name, iconimage, moreData, type='radio')
	elif mode == 41:	#------------- Archive-Categories: ----------
		GetArchiveCategoriesList(url, moduleIcon, moreData)
	elif mode == 42:	#------------- Archive-Series: --------------
		GetArchiveSeriesList(url, iconimage, moreData)
	elif mode == 43:	#------------- Archive-Series: --------------
		GetArchiveEpisodesList(url, iconimage, moreData)
	elif mode == 44:		#--- Move to a specific episodes' page  --
		urlp = common.url_parse(url)
		prms = common.parse_qs(urlp.query)
		page = common.GetIndexFromUser(name, int(prms['pages'][0]))
		if page == 0:
			page = int(prms['p'][0])
		url = '{0}?page={1}'.format(urlp.path, page)
		GetArchiveEpisodesList(url)
		
	if mode != 0:
		common.SetViewMode('episodes')
	if sortBy == 1 and (mode == 1 or mode == 2):
		xbmcplugin.addSortMethod(common.GetHandle(), 1)