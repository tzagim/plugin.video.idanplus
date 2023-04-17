# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import sys, gzip, os, io, random, re, json, urllib, requests, time, collections, xml.parsers.expat as expat
import resources.lib.cloudscraper as cloudscraper
#import zipfile

try:
	# For Python 3.0 and later
	import urllib.parse as urlparse
	py2 = False
except ImportError:
	# Fall back to Python 2
	py2 = True
	import urlparse

AddonID = 'plugin.video.idanplus'
Addon = xbmcaddon.Addon(AddonID)
icon = Addon.getAddonInfo('icon')
AddonVer = Addon.getAddonInfo('version')
AddonName = "Idan Plus"

def decode(text, dec, force=False):
	if py2:
		text = text.decode(dec)
	elif force:
		text= bytearray(text, 'utf-8').decode(dec)
	return text

def encode(text, dec):
	if py2:
		text = text.encode(dec)
	return text

def translatePath(path):
	if py2:
		text = xbmc.translatePath(path)
	else:
		import xbmcvfs
		text = xbmcvfs.translatePath(path)
	return text

profileDir = decode(translatePath(Addon.getAddonInfo("profile")), "utf-8")
if not os.path.exists(profileDir):
	os.makedirs(profileDir)

imagesDir = decode(translatePath(os.path.join(Addon.getAddonInfo('path'), 'resources', 'images')), "utf-8")
epgFile = os.path.join(profileDir, 'epg.json')
seriesFile = os.path.join(profileDir, 'series.json')
seriesUrl = 'https://raw.githubusercontent.com/Fishenzon/repo/master/zips/plugin.video.idanplus/series.json.zip'
youtubePlugin = 'plugin://plugin.video.youtube'

userAgents = [
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',
	'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
	'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12',
	'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240',
	'Mozilla/5.0 (Windows NT 6.1; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/7.1.8 Safari/537.85.17',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.5.17 (KHTML, like Gecko) Version/8.0.5 Safari/600.5.17',
	'Mozilla/5.0 (X11; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:39.0) Gecko/20100101 Firefox/39.0',
	'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/600.6.3 (KHTML, like Gecko) Version/8.0.6 Safari/600.6.3',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36',
	'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.56 (KHTML, like Gecko) Version/9.0 Safari/601.1.56',
	'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.50 (KHTML, like Gecko) Version/9.0 Safari/601.1.50',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.125 Safari/537.36',
	'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3 Safari/600.3.18',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/43.0.2357.130 Chrome/43.0.2357.130 Safari/537.36',
	'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0;  Trident/5.0)',
	'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;  Trident/5.0)',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36',
	'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.155 Safari/537.36 OPR/31.0.1889.174',
	'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:40.0) Gecko/20100101 Firefox/40.0',
	'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.1; rv:38.0) Gecko/20100101 Firefox/38.0',
	'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0',
	'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.78.2 (KHTML, like Gecko) Version/6.1.6 Safari/537.78.2',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/7.1.7 Safari/537.85.16',
	'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36',
	'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0',
	'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
	'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
	'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36'
]
userAgent = random.choice(userAgents)


def GetAddon():
	Addon = xbmcaddon.Addon(AddonID)
	return Addon

def GetAddonSetting(key):
	Addon = xbmcaddon.Addon(AddonID)
	value = Addon.getSetting(key)
	if '_res' in key:
		if value == '':
			value = 'best'
	return value

def SetAddonSetting(key, value):
	Addon.setSetting(key, value)

def GetHandle():
	try:
		handle = int(sys.argv[1])
	except:
		handle = -1
	return handle

def GetIconFullPath(icon):
	return os.path.join(imagesDir, icon)

def GetKodiVer():
	return float(re.split(' |\-',xbmc.getInfoLabel('System.BuildVersion'))[0])

def NewerThanPyVer(ver):
	runnigVer = ver.split('.')
	for i in range(len(runnigVer)):
		if sys.version_info[i] > int(runnigVer[i]):
			return True
	return False

def IsAddonInstalled(addonid):
	return xbmc.getCondVisibility('System.HasAddon({0})'.format(addonid)) == 1

def InstallAddon(addonid):
	xbmc.executebuiltin('InstallAddon({0})'.format(addonid))

def IsAddonEnabled(addonid):
	return json.loads(xbmc.executeJSONRPC('{{"jsonrpc":"2.0","method":"Addons.GetAddonDetails","params":{{"addonid":"{0}", "properties": ["enabled"]}},"id":1}}'.format(addonid)))['result']['addon']['enabled']

def EnableAddon(addonid):
	if GetKodiVer() >= 19:
		xbmc.executebuiltin('EnableAddon({0})'.format(addonid))
	else:
		xbmc.executeJSONRPC('{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{{"addonid":"{0}","enabled":true}},"id":1}}'.format(addonid))

def DisableAddon(addonid):
	xbmc.executeJSONRPC('{{"jsonrpc":"2.0","method":"Addons.SetAddonEnabled","params":{{"addonid":"{0}","enabled":false}},"id":1}}'.format(addonid))

def GetTextFile(filename):
	content = ''
	if os.path.isfile(filename):
		with io.open(filename, 'r', encoding="utf-8") as f:
			content = f.read()
	return content

def ReadList(fileName):
	try:
		with io.open(fileName, 'r', encoding='utf-8') as f:
			content = json.load(f, object_pairs_hook=collections.OrderedDict) if NewerThanPyVer('2.6.99') else json.load(f)
	except Exception as ex:
		xbmc.log(str(ex), 3)
		content=[]
	return content

def WriteList(filename, list):
	try:
		with io.open(filename, 'w', encoding='utf-8') as f:
			f.write(uni_code(json.dumps(list, indent=2, ensure_ascii=False)))
		success = True
	except Exception as ex:
		xbmc.log(str(ex), 3)
		success = False
	return success

def isFileOld(filename, deltaInSec=86400):
	lastUpdate = 0 if not os.path.isfile(filename) else int(os.path.getmtime(filename))
	return (time.time() - lastUpdate) > deltaInSec

def GetUserAgent():
	return userAgent

def GetSession():
	return requests.session()

def OpenURL(url, headers={}, user_data=None, session=None, cookies=None, retries=1, responseMethod='text', verify=True):
	link = ""
	if headers.get('Accept-encoding', '') == '':
		headers['Accept-encoding'] = 'gzip'
	if headers.get('User-agent', '') == '':
		headers['User-agent'] = userAgent
	for i in range(retries):
		try:
			if session is None:
				if user_data is None:
					response = requests.get(url, headers=headers, cookies=cookies, verify=verify)
				else:
					response = requests.post(url, headers=headers, cookies=cookies, data=user_data, verify=verify)
			else:
				if user_data is None:
					response = session.get(url, headers=headers, cookies=cookies, verify=verify)
				else:
					response = session.post(url, data=user_data, headers=headers, cookies=cookies, verify=verify)
			if responseMethod == 'text':
				if int(response.status_code) > 400:
					xbmc.log('{0}  -  response {1}.'.format(url, response.status_code), 3)
					xbmc.log(response.text, 3)
					continue
				link = response.text
			elif responseMethod == 'content':
				link = response.content
			elif responseMethod == 'json':
				link = response.json()
			break
		except Exception as ex:
			xbmc.log(str(ex), 3)
			return None
	return link

def GetRedirect(url, headers={}):
	try:
		response = requests.head(url, headers=headers, allow_redirects=False)
		if response.status_code in set([301, 302, 303, 307]) and 'location' in response.headers:
			url = response.headers['location']
		if response.status_code >= 400 and response.status_code < 500:
			url = None
	except Exception as ex:
		xbmc.log(str(ex), 3)
	return url

def addDir(name, url, mode, iconimage='DefaultFolder.png', infos=None, contextMenu=None, module='', moreData='', totalItems=None, isFolder=True, isPlayable=False, addFav=True, urlParamsData={}):
	urlParams = {'name': name.replace('?', '|||'), 'url': quote_plus(url), 'mode': mode, 'iconimage': quote_plus(iconimage), 'module': module, 'moredata': quote_plus(moreData)}
	u = '{0}?{1}'.format(sys.argv[0], urlencode(urlParams))
	try:
		listitem = xbmcgui.ListItem(name)
		listitem.setArt({'thumb' : iconimage, 'fanart': iconimage, 'icon': iconimage})
	except:
		listitem = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
	if infos is not None:
		listitem.setInfo(type="Video", infoLabels=infos)
	if isPlayable:
		listitem.setProperty("IsPlayable", "true")
	for param in list(urlParamsData.keys()):
		urlParams[param] = urlParamsData[param].replace('?', '|||')
	if addFav:
		urlParams['isFolder'] = isFolder
		urlParams['isPlayable'] = isPlayable
		item = (GetLocaleString(30026), 'RunPlugin({0}?url={1}&mode=8)'.format(sys.argv[0], quote_plus(urlencode(urlParams))))
		if contextMenu is None:
			contextMenu = [item]
		else:
			contextMenu.append(item)
	if contextMenu is not None:
		listitem.addContextMenuItems(items=contextMenu)
	handle = GetHandle()
	if totalItems is None:
		xbmcplugin.addDirectoryItem(handle=handle, url=u, listitem=listitem, isFolder=isFolder)
	else:
		xbmcplugin.addDirectoryItem(handle=handle, url=u, listitem=listitem, isFolder=isFolder, totalItems=totalItems)

def DelFile(aFile):
	try:
		if os.path.isfile(aFile):
			os.unlink(aFile)
	except Exception as ex:
		xbmc.log(str(ex), 3)

def DelCookies():
	tempDir = decode(translatePath('special://temp/'), "utf-8")
	for the_file in os.listdir(tempDir):
		if not '.fi' in the_file and the_file != 'cookies.dat':
			continue
		DelFile(os.path.join(tempDir, the_file))

def GetStreams(url, headers={}, user_data=None, session=None, retries=1, quality='best'):
	if quality.startswith('set'):
		addonKey = quality[4:]
		quality = 'set'
	base = urlparse.urlparse(url)
	baseUrl = '{0}://{1}{2}'.format(base.scheme, base.netloc, base.path)
	text = OpenURL(url, headers=headers, user_data=user_data, session=session, retries=retries)
	if text is None:
		return url
	resolutions = [x for x in re.compile('^#EXT-X-STREAM-INF:.*?BANDWIDTH=(\d+)(.*?)\n(.*?)$', re.M).findall(text)]
	resolutions = sorted(resolutions,key=lambda resolutions: int(resolutions[0]), reverse=True)
	link = url
	if quality == 'best':
		for resolution in resolutions:
			link = resolution[2].strip()
			if not link.startswith('http'): 
				link = urlparse.urljoin(baseUrl, link)
			check = OpenURL(link, headers=headers, user_data=user_data, session=session, retries=retries)
			if check is not None:
				break
	elif quality == 'choose' or quality == 'set':
		if quality == 'set':
			resolutions.insert(0, (GetLocaleString(30024), '', ''))
		resNames = []
		for item in resolutions:
			resNames.append(item[0]) 
			if 'RESOLUTION' in item[1]:
				resNames[-1] += '  [{0}]'.format(re.compile('RESOLUTION=(\d+)x(\d+)').findall(item[1])[0][1])
			elif 'NAME' in item[1]:
				resNames[-1] += '  [{0}]'.format(re.compile('NAME="(.*?)"').findall(item[1])[0])
		qualityInd = xbmcgui.Dialog().select(GetLocaleString(30005), resNames)
		if qualityInd > -1:
			if quality == 'set':
				Addon.setSetting(addonKey, '' if qualityInd == 0 else resolutions[qualityInd][0])
			link = resolutions[qualityInd][2]
	else:
		quality = int(quality)
		res = 0
		for resolution in resolutions:
			_res = int(resolution[0])
			if _res >=  res and _res <=  quality:
				res = _res
				link = resolution[2]
	if not link.startswith('http'): 
		link = urlparse.urljoin(baseUrl, link)
	return link

def PlayStream(url, quality='best', name='', iconimage=''):
	plot = xbmc.getInfoLabel("ListItem.Plot")
	year = xbmc.getInfoLabel("ListItem.Year")
	infos = {"title": name, "plot": plot, "year": year}
	if 'dailymotion' in url:
		url = GetDailymotion(url)
	try:
		listitem = xbmcgui.ListItem(name, path=url)
		listitem.setArt({'thumb' : iconimage, 'fanart': iconimage, 'icon': iconimage})
	except:
		listitem = xbmcgui.ListItem(name, path=url, iconImage=iconimage, thumbnailImage=iconimage)
	listitem.setInfo(type="Video", infoLabels=infos)
	if (quality == 'choose' or quality.startswith('set')) and '.m3u8' in url:
		xbmc.Player().play(url, listitem)
	else:
		xbmcplugin.setResolvedUrl(handle=GetHandle(), succeeded=True, listitem=listitem)

def GetLocaleString(id):
	return encode(Addon.getLocalizedString(id), 'utf-8')

def EscapeXML(text):
	return text.replace('&', '&amp;').replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")

def UnEscapeXML(st):
	st = st.replace("&hellip;", "").replace("&nbsp;", " ")
	want_unicode = False
	if py2 and isinstance(st, unicode):
		st = encode(st, "utf-8")
		want_unicode = True
	# the rest of this assumes that `st` is UTF-8
	list = []
	# create and initialize a parser object
	p = expat.ParserCreate("utf-8")
	p.buffer_text = True
	if py2:
		p.returns_unicode = want_unicode
	p.CharacterDataHandler = list.append
	# parse the data wrapped in a dummy element
	# (needed so the "document" is well-formed)
	p.Parse("<e>", 0)
	p.Parse(st, 0)
	p.Parse("</e>", 1)
	# join the extracted strings and return
	es = ""
	if want_unicode:
		es = u""
	return es.join(list)

def GetLabelColor(text, keyColor=None, bold=False, color=None):
	if not color:
		color = Addon.getSetting(keyColor)
	if bold and Addon.getSetting("boldLables") == "true":
		text = '[B]{0}[/B]'.format(text)
	return text if color == 'none' else '[COLOR {0}]{1}[/COLOR]'.format(color, text)

def getDisplayName(title, subtitle, programNameFormat, bold=False):
	if programNameFormat == 0:
		displayName = ' {0} - {1} '.format(GetLabelColor(title, keyColor="prColor", bold=bold) , GetLabelColor(subtitle, keyColor="chColor"))
	elif programNameFormat == 1:
		displayName = ' {0} - {1} '.format(GetLabelColor(subtitle, keyColor="chColor") , GetLabelColor(title, keyColor="prColor", bold=bold))
	return displayName

def GetUnColor(text):
	regex = re.compile("(\[/?(?:COLOR|B).*?\])", re.IGNORECASE)
	return regex.sub('', text).strip()

def GetImageUrl(iconimage):
	if iconimage is not None:
		i = iconimage.find('://')
		iconimage = iconimage[:i+3] + quote(encode(iconimage[i+3:], "utf-8"))
	return iconimage

def SetViewMode(content):
	xbmcplugin.setContent(GetHandle(), content)
	viewMode = Addon.getSetting("viewModeEpisodes").strip()
	if viewMode != 'Auto' and viewMode != '':
		xbmc.executebuiltin("Container.SetViewMode({0})".format(viewMode))

def ToggleSortMethod(id, sortBy):
	if sortBy == 0:
		Addon.setSetting(id, "1")
	else:
		Addon.setSetting(id, "0")
	xbmc.executebuiltin("Container.Refresh()")

def GetIntSetting(k, v=0):
	if not Addon.getSetting(k).isdigit():
		Addon.setSetting(k, str(v))
	return int(Addon.getSetting(k))

def MoveInList(index, step, listFile):
	theList = ReadList(listFile)
	if index + step >= len(theList) or index + step < 0:
		return
	if step == 0:
		step = GetIndexFromUser(GetLabelColor(GetLocaleString(30034), bold=True, color="none"), len(theList))
		if step != 0:
			step = step - 1 - index
	if step < 0:
		tempList = theList[0:index + step] + [theList[index]] + theList[index + step:index] + theList[index + 1:]
	elif step > 0:
		tempList = theList[0:index] + theList[index +  1:index + 1 + step] + [theList[index]] + theList[index + 1 + step:]
	else:
		return
	WriteList(listFile, tempList)
	xbmc.executebuiltin("Container.Refresh()")

def GetNumFromUser(title, defaultt=''):
	dialog = xbmcgui.Dialog()
	choice = dialog.input(title, defaultt=defaultt, type=xbmcgui.INPUT_NUMERIC)
	return None if choice is None or choice == '' else int(choice)

def GetIndexFromUser(title, listLen):
	location = GetNumFromUser('{0} (1-{1})'.format(title, listLen))
	return 0 if location is None or location > listLen or location <= 0 else location

def GetUpdatedList(listFile, listUrl, headers={}, deltaInSec=86400, isZip=False, sort=False, decode_text=None):
	if isFileOld(listFile, deltaInSec=deltaInSec):
		try:
			if isZip:
				aFile = '{0}.zip'.format(listFile)
				DelFile(aFile)
			else:
				aFile = listFile
			data = OpenURL(listUrl, headers=headers, responseMethod='content')
			with io.open(aFile, 'wb') as f:
				if decode_text is not None:
					data = data.decode(decode_text).encode('utf-8')
				f.write(data)
			if isZip:
				#with zipfile.ZipFile(aFile, 'r') as zip_ref:
				#	zip_ref.extractall(profileDir)
				xbmc.executebuiltin("Extract({0}, {1})".format(aFile, profileDir), True)
				DelFile(aFile)
		except Exception as ex:
			xbmc.log("{0}".format(ex), 3)
	items = ReadList(listFile)
	return sorted(items,key=lambda items: items['name']) if sort else items

def GetKeyboardText(title = '', defaultText = ''):
	keyboard = xbmc.Keyboard(defaultText, title)
	keyboard.doModal()
	return '' if not keyboard.isConfirmed() else keyboard.getText()

def quote(text):
	if py2:
		return urllib.quote(text)
	else:
		return urlparse.quote(text)

def unquote(text):
	if py2:
		return urllib.unquote(text)
	else:
		return urlparse.unquote(text)

def quote_plus(text):
	if py2:
		return urllib.quote_plus(text)
	else:
		return urlparse.quote_plus(text)

def unquote_plus(text):
	if py2:
		return urllib.unquote_plus(text)
	else:
		return urlparse.unquote_plus(text)

def urlencode(text):
	if py2:
		return urllib.urlencode(text)
	else:
		return urlparse.urlencode(text)

def parse_qs(text):
	return urlparse.parse_qs(text)

def parse_qsl(text):
	return urlparse.parse_qsl(text)

def url_parse(text):
	return urlparse.urlparse(text)

def urlunparse(text):
	return urlparse.urlunparse(text)

def uni_code(text):
	if py2:
		return unicode(text)
	else:
		return str(text)

def items(d):
	if py2:
		return d.iteritems()
	else:
		return d.items()

def isnumeric(text):
	return uni_code(text).isnumeric()

def GetKaltura(entryId, partnerId, baseUrl, userAgent, quality='best'):
	headers = {
		'accept': '*/*',
		'accept-language': 'en',
		'content-type': 'application/json',
		'sec-fetch-dest': 'empty',
		'sec-fetch-mode': 'cors',
		'sec-fetch-site': 'cross-site',
		'referrer': baseUrl,
		'referrerPolicy': 'strict-origin-when-cross-origin',
		'User-Agent': userAgent
	}
	payload = json.dumps({"1":{"service":"session","action":"startWidgetSession","widgetId":"_{0}".format(partnerId)},"2":{"service":"baseEntry","action":"list","ks":"{1:result:ks}","filter":{"redirectFromEntryId":entryId},"responseProfile":{"type":1,"fields":"id,referenceId,name,description,thumbnailUrl,dataUrl,duration,msDuration,flavorParamsIds,mediaType,type,tags,dvrStatus,externalSourceType,status"}},"3":{"service":"baseEntry","action":"getPlaybackContext","entryId":"{2:result:objects:0:id}","ks":"{1:result:ks}","contextDataParams":{"objectType":"KalturaContextDataParams","flavorTags":"all"}},"4":{"service":"metadata_metadata","action":"list","filter":{"objectType":"KalturaMetadataFilter","objectIdEqual":entryId,"metadataObjectTypeEqual":"1"},"ks":"{1:result:ks}"},"apiVersion":"3.3.0","format":1,"ks":"","clientTag":"html5:v0.56.1","partnerId":partnerId})
	link = ''
	try:
		response = OpenURL("https://cdnapisec.kaltura.com/api_v3/service/multirequest", headers=headers, user_data=payload, responseMethod='json')
		#xbmc.log(str(response[2]["sources"]), 5)
		for s in response[2]["sources"]:
			if s["format"] == "applehttp":
				link = s["url"]
				break
		xbmc.log(link, 5)
		link = GetStreams(link, quality=quality)
		xbmc.log(link, 5)
	except Exception as ex:
		xbmc.log(str(ex), 3)
	return link

def s(elem):
	if elem[0] == "auto":
		return 1
	else:
		return int(elem[0].split("@")[0])

def GetDailymotion(url):
	vid = re.compile('.*?video/(.*?)[\?|]').findall(url)
	if len(vid) < 1:
		return ''
	vid = vid[0]
	headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.1; Pixel Build/NMF26O) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.91 Mobile Safari/537.36',
	   'Origin': 'https://www.dailymotion.com',
	   'Referer': 'https://www.dailymotion.com/'}
	cookie = {'lang': 'en_US', 'ff': 'off'}
	session = GetSession()
	content = OpenURL("https://www.dailymotion.com/player/metadata/video/{0}".format(vid), session=session, headers=headers, cookies=cookie, responseMethod='json')
	if content.get('error') is not None:
		return ''
	else:
		cc = content['qualities']
		cc = list(cc.items())
		cc = sorted(cc, key=s, reverse=True)
		for source, json_source in cc:
			for item in json_source:
				m_url = item.get('url', None)
				if m_url:
					m_url = m_url.replace('dvr=true&', '')
					if '.m3u8?sec' in m_url:
						text = OpenURL(m_url, headers=headers, cookies=session.cookies.get_dict())
						mb = re.findall('NAME="([^"]+)"\n(.+)', text)
						mb = sorted(mb, key=s, reverse=True)
						for quality, strurl in mb:
							quality = quality.split("@")[0]
							if not strurl.startswith('http'):
								strurl1 = re.findall('(.+/)', m_url)[0]
								strurl = strurl1 + strurl
							strurl = '{0}|{1}'.format(strurl.split('#cell')[0], urlencode(headers))
							return strurl

def GetYouTube(url):
	if url.endswith('/'):
		url = url[:-1]
	video_id = url[url.rfind('/')+1:]
	if '?' in video_id:
		video_id = video_id[:video_id.find('?')]
	return '{0}/play/?video_id={1}'.format(youtubePlugin, video_id)

class TLSAdapter(requests.adapters.HTTPAdapter):
	def init_poolmanager(self, connections, maxsize, block=False):
		import ssl, urllib3
		ctx = ssl.create_default_context()
		ctx.set_ciphers('DEFAULT@SECLEVEL=1')
		ctx.check_hostname = False
		self.poolmanager = urllib3.poolmanager.PoolManager(num_pools=connections, maxsize=maxsize, block=block, ssl_version=ssl.PROTOCOL_TLSv1_2, ssl_context=ctx)	
														   
def GetCF(url, ua=None, retries=10, responseMethod='text'):
	if ua is None:
		ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
	scraper = cloudscraper.create_scraper(delay=10)
	scraper.mount('https://', TLSAdapter())
	scraper.headers.update({'User-Agent': ua})
	
	
	for i in range(retries):
		try:
			response = scraper.get(url)
			if response.status_code in [503, 429, 403]:
				if response.status_code == 503:
					xbmc.sleep(6000)
				if response.status_code == 429:
					xbmc.sleep(4000)
				else:
					xbmc.sleep(100)
				xbmc.log('{0}  -  response {1}.'.format(url, response.status_code), 3)
				continue
			if responseMethod == 'json':
				return response.json()
			else:
				return response.text
		except Exception as ex:
			xbmc.log(str(ex), 3)
			return None
	return ''
