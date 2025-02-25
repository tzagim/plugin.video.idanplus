# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import re, json, os
import resources.lib.common as common
from resources.lib import cache as cache

module = 'kan'
moduleIcon = common.GetIconFullPath("kan.jpg")
baseUrl = 'https://www.kan.org.il'
baseKidsUrl = 'https://www.kankids.org.il'
archiveUrl = 'https://archive.kan.org.il'
baseMobApiUrl = 'https://mobapi.kan.org.il'
mobapi = 'https://mobapi.kan.org.il/api/mobile/subClass'

userAgent = common.GetUserAgent()
headers={"User-Agent": userAgent}
kanSeriesFile = os.path.join(common.profileDir, 'kanSeries.json')
kanSeriesURL = 'https://bit.ly/kanSeries'

saveKanImages = common.Addon.getSettingBool('saveKanImages')
logosDir = os.path.join(common.profileDir, 'logos', 'kan')
if not os.path.exists(logosDir):
	os.makedirs(logosDir)


def GetImageLink(imageUrl, imageName):
	i = imageUrl.find('?')
	if i > 0:
		imageLink = imageUrl[:i]
	imageUrl = imageUrl.replace(baseUrl, baseMobApiUrl).replace(baseKidsUrl, baseMobApiUrl)
	if imageUrl.startswith('/'):
		imageLink = imageUrl = '{0}{1}'.format(baseMobApiUrl, imageUrl)
	if saveKanImages:
		imageLink = os.path.join(logosDir, common.slugify(imageName, allow_unicode=True))
		common.SaveImage(imageUrl, imageLink)
	return imageLink

def GetCategoriesList(iconimage):
	sortString = common.GetLocaleString(30002) if sortBy == 0 else common.GetLocaleString(30003)
	name = "{0}: {1}".format(common.GetLocaleString(30001), sortString)
	common.addDir(name, "toggleSortingMethod", 4, iconimage, {"Title": name, "Plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
	name = common.GetLabelColor("כל התוכניות - קטגוריות", bold=True, color="none")
	common.addDir(name, '{0}/lobby/kan-box'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData=common.GetLocaleString(30602))
	name = common.GetLabelColor("כל התוכניות", bold=True, color="none")
	common.addDir(name, '{0}/lobby/kan11'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData='{0}__4444'.format(common.GetLocaleString(30602)))
	name = common.GetLabelColor("תוכניות אקטואליה", bold=True, color="none")
	common.addDir(name, '{0}/lobby/newstv'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData=common.GetLocaleString(30602))
	name = common.GetLabelColor("דיגיטל", bold=True, color="none")
	common.addDir(name, '{0}/lobby/digital-lobby'.format(baseUrl), 1, iconimage, infos={"Title": name}, module=module, moreData='{0}__4464'.format(common.GetLocaleString(30602)))
	name = common.GetLabelColor(common.GetLocaleString(30607), bold=True, color="none")
	common.addDir(name, baseKidsUrl, 5, common.GetIconFullPath("23tv.jpg"), infos={"Title": name}, module=module, moreData=common.GetLocaleString(30607))
	name = common.GetLabelColor("כאן - ארכיון", bold=True, color="none")
	common.addDir(name, '{0}/lobby/archive/'.format(baseUrl), 41, iconimage, infos={"Title": name}, module=module, moreData="כאן ארכיון")
	name = common.GetLabelColor("תכניות רדיו", bold=True, color="none")
	common.addDir(name, '', 21, iconimage, infos={"Title": name}, module=module)
	name = common.GetLabelColor("פודקאסטים", bold=True, color="none")
	common.addDir(name, '4451', 31, iconimage, infos={"Title": name}, module=module)
	name = common.GetLabelColor("פודקאסטים לילדים", bold=True, color="none")
	common.addDir(name, '{0}/lobby-kids/podcasts-kids/'.format(baseKidsUrl), 33, common.GetIconFullPath("23tv.jpg"), infos={"Title": name}, module=module)

def GetSeriesList(url, iconimage, catName):
	cat = catName.split('__')
	catName = cat[0]
	if len(cat) > 1:
		i = 1
		while (i > 0):
			url = '{0}?from={1}&id={2}'.format(mobapi, i, cat[1])
			matches = common.OpenURL(url, responseMethod='json').get('entry')
			i = 0 if len(matches) < 200 else 200 + i
			for serie in matches:
				name = common.GetLabelColor(serie['title'], keyColor="prColor", bold=True)
				description = serie['description']
				link = serie['link']['href'].replace('?app=true', '')
				image = serie['media_group'][0]['media_item'][3]['src']
				common.addDir(name, link, 7, image[:image.find('?')], infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
		return
	
	#text = common.GetCF(url, userAgent)
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
	#if not ('kankids' in url):
	domain = baseKidsUrl if 'kankids' in url else baseUrl
	kanSeries = common.GetUpdatedList(kanSeriesFile, kanSeriesURL, headers={'Referer': 'http://idan-{0}.Kodi-{1}.fish'.format(common.AddonVer, common.GetKodiVer())}, deltaInSec=86400, isZip=True)
	matches = re.compile('digitalSeries:.*?\[(.*?)}\]', re.S).findall(text)
	if len(matches) > 0:
		matches = json.loads('{"series":['+matches[0].strip()+'}]}')
		for serie in matches['series']:
			link = serie['Url']
			if not link.startswith('http'):
				link = '{0}{1}'.format(domain, link)
			kanSerie = kanSeries.get(link)
			if kanSerie is not None:
				name = kanSerie['name']
				description = kanSerie['description']
				image = GetImageLink(common.quoteNonASCII(kanSerie['image']), name)
			else:
				name = link[link.rfind('/', 0, len(link)-1)+1:len(link)-1].replace('-', ' ')
				description = serie['Description']
				image = GetImageLink(common.quoteNonASCII(serie['Image']), name)
			name = common.GetLabelColor(name, keyColor="prColor", bold=True)
			common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
		return
	else:
		links = []
		matches = re.compile('<main id="main"(.*)</main>', re.S).findall(text)
		if len(matches) < 1:
			return
		
		series = re.compile('<div class="vod-section(.*?)<div class="section-content">', re.S).findall(matches[0])
		series = re.compile('<div aria-label="(.*?)">.*?url\((.*?)">.*?<div class="info-description">(.*?)</div>\s*<a href="(.*?)"', re.S).findall(series[0])
		for name, image, description, link in series:
			if not link.startswith('http'):
				link = '{0}{1}'.format(domain, link)
			if link in links:
				continue
			links += [link]
			image = GetImageLink(common.quoteNonASCII(image), name)
			name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="prColor", bold=True)
			description = common.UnEscapeXML(description.strip())
			common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
		categories = re.compile('<div class="section elem"(.*)<div class="ec-section', re.S).findall(matches[0])
		if len(categories) > 0:
			categories = re.compile('<div class="block-list-item">.*?<a href="(.*?)" class="unstyled-link">(.*?)</a>', re.S).findall(categories[0])
			for link, name in categories:
				if not link.startswith('http'):
					link = '{0}{1}'.format(domain, link)
				if link in links:
					continue
				links += [link]
				name = common.GetLabelColor(common.UnEscapeXML(name), color="none", bold=True)
				common.addDir(name, link, 8, iconimage, infos={"Title": name, "Plot": name}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
			return
		else:
			matches = re.compile('"section-title">עוד אקטואליה(.*?)</ul>', re.S).findall(text)
			matches = re.compile('<li>.*?<a href="(.*?)".*?<img src="(.*?)".*?"font-weight-normal">(.*?)</.*?</li>', re.S).findall(matches[0])
			for link, image, description in matches:
				if not link.startswith('http'):
					link = '{0}{1}'.format(domain, link)
				if link in links:
					continue
				links += [link]
				kanSerie = kanSeries.get(link)
				if kanSerie is not None:
					name = kanSerie['name']
					description = kanSerie['description']
					image = GetImageLink(common.quoteNonASCII(kanSerie['image']), name)
				else:
					name = description
				image = GetImageLink(common.quoteNonASCII(common.UnEscapeXML(image)), name)
				description = common.UnEscapeXML(description.strip())
				name = common.GetLabelColor(name, keyColor="prColor", bold=True)
				common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
			return

def GetSubCategories(url, iconimage, catName):
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
	domain = baseKidsUrl if 'kankids' in url else baseUrl
	kanSeries = common.GetUpdatedList(kanSeriesFile, kanSeriesURL, headers={'Referer': 'http://idan-{0}.Kodi-{1}.fish'.format(common.AddonVer, common.GetKodiVer())}, deltaInSec=86400, isZip=True)
	links = []
	matches = re.compile('<div class="card">\s*<a href="(.*?)".*?<img src="(.*?)".*?"card-title">(.*?)<', re.S).findall(text)
	if len(matches) < 1:
		return
	for link, image, name in matches:
		if not link.startswith('http'):
			link = '{0}{1}'.format(domain, link)
		if link in links:
			continue
		links += [link]
		kanSerie = kanSeries.get(link)
		if kanSerie is not None:
			name = kanSerie['name']
			description = kanSerie['description']
			image = kanSerie['image']
		else:
			description = name
		name = common.GetLabelColor(common.UnEscapeXML(name.strip()), keyColor="prColor", bold=True)
		description = common.UnEscapeXML(description.strip())
		image = GetImageLink(common.quoteNonASCII(image), name.strip())
		common.addDir(name, link, 7, image, infos={"Title": name, "Plot": description}, module=module, moreData=catName, urlParamsData={'catName': catName})
	
	pages = int(re.compile('name="NumberOfPages" type="hidden" value="(\d*)"').findall(text)[0])
	if pages < 2:
		return
	
	j = url.find('?')
	if j < 0:
		_url = url
		page = 1
	else:
		_url = url[:j]
		page = int(re.compile('page=(\d*)').findall(url)[0])
	
	if page > 1:
		name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
		common.addDir(name, '{0}?page={1}'.format(_url, page-1), 9, iconimage, infos={"Title": name, "Plot": name}, module=module, moreData=catName)
	if pages > page:
		name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
		common.addDir(name, '{0}?page={1}'.format(_url, page+1), 9, iconimage, infos={"Title": name, "Plot": name}, module=module, moreData=catName)
	if pages > 1:
		name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
		common.addDir(name, '{0}?p={1}&pages={2}'.format(_url, page, pages), 45, iconimage, infos={"Title": name, "Plot": name}, module=module, moreData=catName)

def GetSubCategoriesList(url, iconimage):
	name = common.GetLabelColor("קטנטנים", bold=True, color="none")
	common.addDir(name, '{0}/lobby-kids/tiny/'.format(baseKidsUrl), 1, iconimage, infos={"Title": name}, module=module, moreData='{0}__4462'.format(common.GetLocaleString(30607)))
	name = common.GetLabelColor("ילדים ונוער", bold=True, color="none")
	common.addDir(name, '{0}/lobby-kids/kids-teens/'.format(baseKidsUrl), 1, iconimage, infos={"Title": name}, module=module, moreData='{0}__4453'.format(common.GetLocaleString(30607)))

def AddSeries(matches, catName):
	for link, iconimage, name, description in matches:
		i = link.lower().find('catid=')
		if i > 0:
			link = link[i+6:]
		elif 'page.aspx' in link.lower():
			try:
				#t = common.GetCF(link, userAgent)
				t = cache.get(common.GetCF, 24, link, userAgent, table='pages')
				if t==[]:
						t = cache.get(common.GetCF, 0, link, userAgent, table='pages')
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
	#text = common.GetCF(data)
	text = cache.get(common.GetCF, 24, data, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, data, table='pages')
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
	#text = common.GetCF(url)
	text = cache.get(common.GetCF, 24, url, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, table='pages')
	#text = common.OpenURL(url)
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
			nameArr = re.compile('"card-title">(.*?)</div>', re.S).findall(episode[2])
			name = common.GetLabelColor(common.UnEscapeXML(nameArr[0].strip()), keyColor="chColor")
			description = re.compile('"card-text">(.*?)</div>', re.S).findall(episode[2])
			description = common.UnEscapeXML(description[0].strip()) if len(description) > 0 else ''
			image = GetImageLink(common.quoteNonASCII(common.UnEscapeXML(episode[1])), nameArr[0].strip())
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
			name = common.UnEscapeXML(matches[0][1].strip())
			image = GetImageLink(common.quoteNonASCII(matches[0][0]), name)
			name = common.GetLabelColor(common.UnEscapeXML(matches[0][1].strip()), keyColor="chColor")
			description = common.UnEscapeXML(matches[0][3].strip())# if len(matches[0]) > 4 ''
			link = '{0}/{1}'.format(domain, matches[0][4])# if len(matches[0]) > 4 else '{0}/{1}'.format(domain, matches[0][2])
			common.addDir(name, link, 3, image, infos={"Title": name, "Plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
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
		#text = common.GetCF(url, userAgent).replace('\u200b', '')
		text = cache.get(common.GetCF, 24, url, userAgent, table='pages').replace('\u200b', '')
		if text==[]:
			text = cache.get(common.GetCF, 0, url, userAgent, table='pages').replace('\u200b', '')
		#text = common.OpenURL(url)
		matches = re.compile('program_list_videoblock">.*?url\(\'(.*?)\'\).*?"application/json">(.*?)</script>.*?"content_title">(.*?)</h2>.*?<p>(.*?)</p>', re.S).findall(text)
		for image, link, title, description in matches:
			name = common.UnEscapeXML(name.replace('\r', '').replace('\n', '').strip())
			image = GetImageLink(image, name)
			name = common.GetLabelColor(name, keyColor="chColor")
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
	common.addDir(name, 'kan-b', 22, common.GetIconFullPath("bet.png"), infos={"Title": name}, module=module, moreData='4483')
	name = common.GetLabelColor("כאן גימל", bold=True, color="none")
	common.addDir(name, 'kan-gimel', 22, common.GetIconFullPath("gimel.png"), infos={"Title": name}, module=module, moreData='4490')
	name = common.GetLabelColor("כאן 88", bold=True, color="none")
	common.addDir(name, 'kan-88', 22, common.GetIconFullPath("88.png"), infos={"Title": name}, module=module, moreData='4504')
	name = common.GetLabelColor("כאן תרבות", bold=True, color="none")
	common.addDir(name, 'kan-tarbut', 22, common.GetIconFullPath("culture.png"), infos={"Title": name}, module=module, moreData='4497')
	name = common.GetLabelColor("כאן קול המוסיקה", bold=True, color="none")
	common.addDir(name, 'kan-music', 22, common.GetIconFullPath( "music.png"), infos={"Title": name}, module=module, moreData='4518')
	name = common.GetLabelColor("כאן מורשת", bold=True, color="none")
	common.addDir(name, 'kan-moreshet', 22, common.GetIconFullPath("moreshet.png"), infos={"Title": name}, module=module, moreData='4511')
	name = common.GetLabelColor("כאן Reka", bold=True, color="none")
	common.addDir(name, 'kan-reka', 22, common.GetIconFullPath("reka.png"), infos={"Title": name}, module=module, moreData='4525')

def GetRadioSeriesList(url, catName, id=None):
	if id:
		i = 1
		while (i > 0):
			url = '{0}?from={1}&id={2}'.format(mobapi, i, id)
			matches = common.OpenURL(url, responseMethod='json').get('entry')
			i = 0 if len(matches) < 200 else 200 + i
			for serie in matches:
				name = common.GetLabelColor(serie['title'], keyColor="prColor", bold=True)
				description = serie['description']
				link = serie['link']['href'].replace('?app=true', '')
				image = serie['media_group'][0]['media_item'][2]['src']
				common.addDir(name, link, 23, image[:image.find('?')], infos={"Title": name, "Plot": description}, module=module, moreData=catName, urlParamsData={'catName': catName})
		return
	text = common.GetCF('{0}/content/kan/{1}/'.format(baseUrl, url), userAgent)
	#text = common.OpenURL(url)
	match = re.compile('<div class="tab-pane fade show active(.*?)</ul>', re.S).findall(text)
	matches = re.compile('<a href="(.*?)".*?background-image: url\((.*?)\).*?"card-title">(.*?)</.*?"text-on-hover">.*?<div>(.*?)</div>.*?</li>', re.S).findall(match[0])
	for link, iconimage, name, description in matches:
		name = common.UnEscapeXML(name.strip())
		iconimage = GetImageLink(common.UnEscapeXML(iconimage), name)
		name = common.GetLabelColor(name, keyColor="prColor", bold=True)
		common.addDir(name, link, 23, iconimage, infos={"Title": name, "Plot": common.UnEscapeXML(description)}, module=module, moreData=catName, urlParamsData={'catName': catName})

def GetRadioEpisodesList(data, iconimage, catName):
	d = data.split(';')
	progUrl = d[0]
	page = 0 if len(d) < 2 else int(d[1])
	stopPage = page + pagesPerList
	prevPage = page - pagesPerList if page >= pagesPerList else 0
	while True:
		page += 1
		url = '{0}?currentPage={1}'.format(progUrl, page)
		#text = common.GetCF(url, userAgent)
		text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
		if text==[]:
			text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
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
		#text = common.GetCF(url, userAgent)
		text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
		if text==[]:
			text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
		matches = re.compile('AudioUrl":"(.+?)"').findall(text)
		if len(matches) == 0:
			return
		#final = 'https://omny.fm{1}'.format(matches[-1])
		#final = '{0}{1}'.format(url[:-1], '.mp3')
		final = '{0}|User-Agent={1}'.format(matches[-1], userAgent)
		#final = url
	elif 'kan/podcasts' in url or 'kids-podcasts' in url:
		#text = common.GetCF(url, userAgent)
		text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
		if text==[]:
			text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
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
	#text = common.GetCF(url, userAgent)
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
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
		#text = common.GetCF(url, userAgent)
		text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
		if text==[]:
			text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
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
	channels = common.GetChannelsLinks("tv", module)
	radioChannelsLinks = common.GetChannelsLinks("radio", module)
	channels.update(radioChannelsLinks)
	channelUrl = channels[url]
	link = common.GetStreams(channelUrl, quality=quality)
	common.PlayStream(link, quality, name, iconimage)

def GetPodcastsList(id=None):
	if id:
		i = 1
		while (i > 0):
			url = '{0}?from={1}&id={2}'.format(mobapi, i, id)
			matches = common.OpenURL(url, responseMethod='json').get('entry')
			i = 0 if len(matches) < 200 else 200 + i
			for serie in matches:
				name = common.GetLabelColor(serie['title'], keyColor="prColor", bold=True)
				description = serie['description']
				link = serie['link']['href'].replace('?app=true', '')
				image = serie['media_group'][0]['media_item'][2]['src']
				common.addDir(name, link, 32, image[:image.find('?')], infos={"Title": name, "Plot": description}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
		return
	url = '{0}/lobby/aod/'.format(baseUrl)
	#text = common.GetCF(url, userAgent)
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
	#text = common.OpenURL(url)
	matches = re.compile('class="podcast-item".*?<a href="(.*?)".*?title="(.*?)".*?src="(.*?)".*?"text">(.*?)</div>', re.S).findall(text)
	for link, name, image, description in matches:
		name = common.UnEscapeXML(name.strip())
		image = GetImageLink(common.UnEscapeXML(image), name)
		name = common.GetLabelColor(name, keyColor="prColor", bold=True)
		common.addDir(name, link, 32, image, infos={"Title": name, "Plot": common.UnEscapeXML(description.strip())}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})

def GetPodcastEpisodesList(data, iconimage):
	d = data.split(';')
	progUrl = d[0]
	page = 0 if len(d) < 2 else int(d[1])
	stopPage = page + pagesPerList
	prevPage = page - pagesPerList if page >= pagesPerList else 0
	domain = baseKidsUrl if 'kankids' in progUrl else baseUrl
	while True:
		page += 1
		url = '{0}?currentPage={1}'.format(progUrl, page)
		#ext = common.GetCF(url, userAgent)
		text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
		if text==[]:
			text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
		#text = common.OpenURL(url)
		body = re.compile('<div class="card card-row">(.*?)</li>', re.S).findall(text)
		for b in body:
			matches = re.compile('href="(.*?)".*?src="(.*?)".*?"card-title">(.*?)</h.*?description">(.*?)</div>', re.S).findall(b)
			for link, image, name, description in matches:
				name = common.UnEscapeXML(name.strip())
				image = GetImageLink(common.UnEscapeXML(image), name)
				name = common.GetLabelColor(name, keyColor="chColor")
				if not link.startswith('http'):
					link = '{0}{1}'.format(domain, link)
				common.addDir(name, link, 3, image, infos={"Title": name, "Plot": common.UnEscapeXML(description.strip())}, module=module, isFolder=False, isPlayable=True, urlParamsData={'catName': 'כאן פודקאסטים'})
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
	url = 'https://www.kankids.org.il/umbraco/surface/RecommendedPodcast/GetRecommended?nodeId=419086&currentPageNumber=0&itemsPerPage=10000&componentItemsToSkip=0&componentItemsToTake=2147483647'
	#text = common.GetCF(url, userAgent)
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
	#text = common.OpenURL(url)
	matches = re.compile('<img src="(.*?)".*?<a href="(.*?)".*?"card-title">(.*?)</.*?"description">(.*?)</div>', re.S|re.I).findall(text)
	for image, link, name, description in matches:
		name = common.UnEscapeXML(name.strip())
		image = GetImageLink(common.quoteNonASCII(common.UnEscapeXML(image)), name)
		name = common.GetLabelColor(name, keyColor="prColor", bold=True)
		description = common.UnEscapeXML(description.strip())
		common.addDir(name, '{0}{1}'.format(baseKidsUrl, link), 32, image, infos={"Title": name, "Plot": description.replace('&nbsp;', '').strip()}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})

def GetArchiveCategoriesList(url, iconimage, catName):
	text = common.GetCF(url, userAgent)
	#text = common.OpenURL(url)
	domain = baseKidsUrl if 'kankids' in url else baseUrl
	links = []
	matches = re.compile('<main id="main"(.*)</main>', re.S).findall(text)
	if len(matches) < 1:
		return
	
	series = re.compile('<div class="vod-section(.*?)<div class="section-content">', re.S).findall(matches[0])
	series = re.compile('<div.*?aria-label="(.*?)">.*?class="video-article__text">(.*?)</div>\s*<a href="(.*?)"', re.S).findall(series[0])
	for name, description, link in series:
		if not link.startswith('http'):
			link = '{0}{1}'.format(domain, link)
		if link in links:
			continue
		links += [link]
		name = common.GetLabelColor(common.UnEscapeXML(name), keyColor="prColor", bold=True)
		description = common.UnEscapeXML(description.strip())
		common.addDir(name, link, 2, iconimage, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
	
	series = re.compile('<div class="ec-section(.*?)&#x5D1;&#x5D7;&#x5D9;&#x5E8;&#x5EA; &#x5D4;&#x5E2;&#x5D5;&#x5E8;&#x5DB;&#x5EA;', re.S).findall(matches[0])
	series = re.compile('<a.*?href="(.*?)".*?aria-label="(.*?)".*?img src="(.*?)"', re.S).findall(series[0])
	for link, name, image in series:
		if not link.startswith('http'):
			link = '{0}{1}'.format(domain, link)
		if link in links:
			continue
		links += [link]
		name = common.UnEscapeXML(name)
		image = GetImageLink(common.quoteNonASCII(image), name)
		name = common.GetLabelColor(name, keyColor="prColor", bold=True)
		description = name
		common.addDir(name, link, 2, image, infos={"Title": name, "Plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})

def GetArchiveSeriesList(url, iconimage, catName):
	#text = common.GetCF(url, userAgent)
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
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
	#text = common.GetCF(url, userAgent)
	text = cache.get(common.GetCF, 24, url, userAgent, table='pages')
	if text==[]:
		text = cache.get(common.GetCF, 0, url, userAgent, table='pages')
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
		name = common.UnEscapeXML(name.strip())
		image = common.quoteNonASCII(image)
		if image.startswith('http') == False:
			image = '{0}{1}'.format(archiveUrl, image)
		image = GetImageLink(image, name)
		name = common.GetLabelColor(name, keyColor="chColor")
		match = re.compile('<h4>(.*?)</h4>').findall(rest)
		if len(match) == 0:
			match = re.compile('<p class="spoiler">(.*?)</p>').findall(rest)
		description = common.UnEscapeXML(match[0]) if len(match) == 1 else ""
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

def DeleteImages():
	for the_file in os.listdir(logosDir):
		file_path = os.path.join(logosDir, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
		except Exception as ex:
			xbmc.log("{0}".format(ex), 3)
			
def Run(name, url, mode, iconimage='', moreData=''):
	global sortBy, bitrate, pagesPerList
	sortBy = int(common.GetAddonSetting('{0}SortBy'.format(module)))
	bitrate = common.GetAddonSetting('{0}_res'.format(module))
	pagesPerList = int(common.GetAddonSetting("kanPagesPerList"))
	
	if mode == 0:	#------------- Categories: ----------------------
		GetCategoriesList(moduleIcon)
	elif mode == 8:	#------------- Sub-Categories: ------------------
		GetSubCategories(url, iconimage, moreData)
	elif mode == 9:	#------------- Sub-Categories: ------------------
		GetSubCategories(url, iconimage, moreData)
	elif mode == 45:		#--- Move to a specific episodes' page  --
		urlp = common.url_parse(url)
		prms = common.parse_qs(urlp.query)
		page = common.GetIndexFromUser(name, int(prms['pages'][0]))
		if page == 0:
			page = int(prms['p'][0])
		url = '{0}://{1}{2}?page={3}'.format(urlp.scheme, urlp.netloc, urlp.path, page)
		GetSubCategories(url, iconimage, moreData)
	elif mode == 5:	#------------- Sub-Categories: ------------------
		GetSubCategoriesList(url, iconimage)
	elif mode == 1:	#------------- Series: -------------------------
		GetSeriesList(url, iconimage, moreData)
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
		GetRadioSeriesList(url, common.GetUnColor(name), moreData)
	elif mode == 23: #------------- Radio Episodes: -----------------
		GetRadioEpisodesList(url, iconimage, moreData)
	elif mode == 31: #------------- Podcast Series: -----------------
		GetPodcastsList(url)
	elif mode == 32: #------------- Podcast Episodes: ---------------
		GetPodcastEpisodesList(url, iconimage)
	elif mode == 33: #------------- Kids Podcast Series: ------------
		GetKidsPodcastsList()
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
	elif mode == 50:	#------------- Delete images: --------------
		DeleteImages()
		mode = 0
	
	if mode != 0:
		common.SetViewMode('episodes')
	if sortBy == 1 and (mode == 1 or mode == 2):
		xbmcplugin.addSortMethod(common.GetHandle(), 1)