# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin
import re, json, os, datetime
from urllib.parse import quote
import resources.lib.common as common
from resources.lib import cache as cache
from resources.lib import watch_store, watch_ui

module = 'kan'
moduleIcon = common.iconKan
module23Icon = common.iconKan23
baseUrl = 'https://www.kan.org.il'
baseKidsUrl = 'https://www.kankids.org.il'
archiveUrl = 'https://archive.kan.org.il'
baseMobApiUrl = 'https://mobapi.kan.org.il'
mobapi = 'https://mobapi.kan.org.il/api/mobile/subClass'

# One fixed, complete, current browser string. The add-on's random pick (`common.GetUserAgent()`) includes entries cut short ("... Safari/604.", "... Firefox/121.")
# and Kan's Cloudflare answers those with 403 for every page, so on a start that drew one no Kan page could be read and nothing played (real log 2026-10-25,
# reproduced with the add-on's own `GetCF`: cut strings give an empty page, this one the full page).
userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36'
headers={"User-Agent": userAgent}
kanSeriesFile = os.path.join(common.profileDir, 'kanSeries.json')
kanSeriesURL = 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/kanSeries.json.zip'

saveKanImages = common.Addon.getSettingBool('saveKanImages')
logosDir = os.path.join(common.profileDir, 'logos', 'kan')
if not os.path.exists(logosDir):
    os.makedirs(logosDir)

mobProgramApi = 'https://mobapi.kan.org.il/api/mobile/program'
WATCH_MIN_SECONDS = 300   # a shorter item (trailer, clip, song) is not an episode for the watch history

def _extractKanIds(url):
    match = re.search(r'/p-(\d+)(?:/s(\d+))?(?:/(\d+))?', url)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None

MOB_PAGE_SIZE = 200   # the feed answers at most this many entries per request
MOB_MAX_PAGES = 10    # a bound for the loop below (2,000 entries)

def _fetchMobProgram(url):
    """The program feed with ALL its entries: the feed holds at most `MOB_PAGE_SIZE` per answer, `&from=N` (1-based) gives the next ones, and a few entries repeat
    at the seam (checked on the real server), so they are joined by id. It stops at a short page, at a page that adds nothing new (a server that ignored `from`
    would otherwise be asked for ever), and after `MOB_MAX_PAGES` requests. A later page that fails keeps what was read."""
    result = common.OpenURL(url, headers=headers, responseMethod='json')
    if not result:
        return {}
    entries = result.get('entry') or []
    page = result
    for _ in range(MOB_MAX_PAGES - 1):
        if len(page.get('entry') or []) < MOB_PAGE_SIZE:
            break
        page = common.OpenURL('{0}&from={1}'.format(url, len(entries) + 1), headers=headers, responseMethod='json') or {}
        known = {e.get('id') for e in entries}
        added = [e for e in page.get('entry') or [] if e.get('id') not in known]
        if not added:
            break
        entries = entries + added
    return dict(result, entry=entries)

def GetMobProgram(programId):
    url = '{0}?id={1}'.format(mobProgramApi, programId)
    result = cache.get(_fetchMobProgram, 24, url, table='mobapi')
    if not result:
        result = cache.get(_fetchMobProgram, 0, url, table='mobapi')
    return result or {}

def _mobEpisodeImage(entry):
    image = _pick_image_from_media_group(entry)
    if image:
        return image.split('|', 1)[0].split('?', 1)[0]
    return moduleIcon

def _mobProps(entry):
    """The feed entry's `analyticsCustomProperties` (season, episode number, length, broadcast date ...); `{}` when it has none."""
    props = (entry.get('extensions') or {}).get('analyticsCustomProperties')
    return props if isinstance(props, dict) else {}

def _mobHref(entry):
    """The entry's page address without `?app=true`; '' when it has none (an announced episode comes with `href: null` and nothing to play)."""
    link = entry.get('link')
    href = link.get('href') if isinstance(link, dict) else None
    return href.replace('?app=true', '') if isinstance(href, str) else ''

def _mobProgramLink(serie):
    """The address a show of the show lists opens by. A show whose link has a name instead of a program number
    (".../kids/hinuchit-main/the_serials/", 24 of about 100 kids shows) gets the canonical ".../p-<id>/" form built from its own id: the feed answers `program?id=<id>`
    for it (24 of 24 checked), so the season list, the history and the page fixes all work for it too."""
    link = _mobHref(serie)
    if link and serie.get('id') is not None and not re.search(r'/p-\d+', link):
        link = re.sub(r'/[^/]+/$', '/p-{0}/'.format(serie['id']), link.rstrip('/') + '/')
    return link

def _mobEpisodeSeason(entry):
    season = _mobProps(entry).get('season')
    try:
        return int(season)
    except (TypeError, ValueError):
        return None

def _mobStreamFromEntry(entry):
    content = entry.get('content') or {}
    ctype = content.get('type', '')
    src = (content.get('src') or '').strip()
    if ctype == 'youtube-id' and src:
        return 'youtube', 'https://www.youtube.com/watch?v={0}'.format(src)
    if src.startswith('http'):
        return 'stream', src
    return None, None

def _mobFindEntry(entries, episode_id=None, url=''):
    if episode_id:
        for entry in entries:
            if str(entry.get('id')) == str(episode_id):
                return entry
    if url:
        clean = url.split('?')[0].rstrip('/')
        for entry in entries:
            href = _mobHref(entry).rstrip('/')
            if href == clean or clean.endswith('/{0}'.format(entry.get('id'))):
                return entry
    return None

def _mobSeasonLinks(base_url, entries):
    seasons = {}
    for entry in entries:
        season = _mobEpisodeSeason(entry)
        if season and season > 0:
            seasons[season] = common.GetLabelColor('עונה {0}'.format(season), keyColor="prColor")
    if len(seasons) <= 1:
        return None
    base = re.sub(r'/s\d+/?.*$', '/', base_url.rstrip('/') + '/')
    return [(num, name, '{0}s{1}/'.format(base, num)) for num, name in sorted(seasons.items())]

def _mobSeconds(entry):
    """The episode length in seconds from the feed's "HH:MM:SS"; 0 when it is missing or odd."""
    try:
        hours, minutes, seconds = (int(part) for part in _mobProps(entry).get('duration').split(':'))
    except (AttributeError, ValueError):
        return 0
    return max(hours * 3600 + minutes * 60 + seconds, 0)

def _mobNumber(entry):
    """The episode number viewers see: the one in the title ("פרק 3 - ..."), else the feed's `episode_number`; None when neither is a positive number."""
    found = re.search(r'פרק\s*(\d+)', entry.get('title') or '')
    if found:
        return int(found.group(1))
    number = _mobProps(entry).get('episode_number')
    return number if isinstance(number, int) and not isinstance(number, bool) and number > 0 else None

def _mobAired(entry):
    """`YYYY-MM-DD` of the BROADCAST date (`content_customDimension_7`, "12-11-2024"); '' when it is missing or not a real date. The entry's `published` is the
    upload date and is not used: a whole imported season shares one (checked on the real feed: season 5 of קופה ראשית is "published" 2024-10-06 and aired
    weekly from 12-11-2024)."""
    found = re.match(r'^(\d{2})-(\d{2})-(\d{4})$', _mobProps(entry).get('content_customDimension_7') or '')
    if not found:
        return ''
    try:
        return datetime.date(int(found.group(3)), int(found.group(2)), int(found.group(1))).isoformat()
    except ValueError:
        return ''

def ShortName(title):
    """The episode's own title out of "פרק N - title" (the part after the number); the whole text when it has no number."""
    text = (title or '').strip()
    found = re.search(r'^פרק\s*\d+\s*[:\-\u2013]\s*(.+)$', text)
    return found.group(1).strip() if found else text

def _mobTracked(entry):
    """Whether the watch history follows this entry: it has an id and a page to play and lasts at least `WATCH_MIN_SECONDS`. A `youtube-id` entry counts too: its
    page names the site's own stream like any other (20 of 20 checked), which is what `Play` uses (see `PageStream`)."""
    return entry.get('id') is not None and _mobHref(entry) != '' and _mobSeconds(entry) >= WATCH_MIN_SECONDS

def _mobWatchGroup(entries, season_filter):
    """`(season number, entries)` the history follows for one listing: the listed season when a season was asked for; for the whole-program listing (the program
    has at most one numbered season) its single numbered season, else season 0 (a program of loose items). Several numbered seasons without a choice: nothing."""
    if season_filter:
        return season_filter, [e for e in entries if _mobEpisodeSeason(e) == season_filter]
    numbered = {_mobEpisodeSeason(e) for e in entries if (_mobEpisodeSeason(e) or 0) > 0}
    if len(numbered) > 1:
        return None, []
    season = numbered.pop() if numbered else 0
    return season, [e for e in entries if (_mobEpisodeSeason(e) or 0) == season]

def WatchEpisodes(entries):
    """The tracked episodes of one season as the watch history stores them, OLDEST FIRST: by number, then broadcast date, then the feed's own order (the feed
    lists them in no useful order). Trailers, clips, YouTube entries and entries without a page are left out."""
    listed = []
    for index, entry in enumerate(entries or []):
        if not _mobTracked(entry):
            continue
        number = _mobNumber(entry)
        aired = _mobAired(entry)
        title = (entry.get('title') or '').strip()
        listed.append((number if number is not None else 10 ** 6, aired, index, {
            'key': watch_store.episode_key(module, entry['id']), 'name': ShortName(title) or title, 'icon': _mobEpisodeImage(entry), 'number': number,
            'url': _mobHref(entry), 'aired': aired, 'play_mode': 3}))
    listed.sort(key=lambda item: item[:3])
    return [item[3] for item in listed]

def EpisodeFacts(entries):
    """`{episode key: {plot, aired, duration}}` from the listing itself: the feed gives every episode's description, broadcast date and length up front."""
    facts = {}
    for entry in entries or []:
        if not _mobTracked(entry):
            continue
        one = {}
        plot = common.UnEscapeXML((entry.get('description') or entry.get('summary') or '').strip())
        if plot:
            one['plot'] = plot
        if _mobAired(entry):
            one['aired'] = _mobAired(entry)
        one['duration'] = _mobSeconds(entry)
        facts[watch_store.episode_key(module, entry['id'])] = one
    return facts

def RememberSeason(programId, programTitle, entries, season_filter, url, moreData):
    """Save the season just listed (ids, numbers, dates, how to reopen it) and every episode's facts; returns the set of tracked episode keys (empty when there is
    nothing to track). A failure here must never break a listing."""
    try:
        season, group = _mobWatchGroup(entries, season_filter)
        listed = WatchEpisodes(group)
        if not listed:
            return set()
        md = moreData.split('|||')
        catName = '' if len(md) < 2 else md[1]
        programUrl = re.sub(r'/s\d+/?.*$', '/', url.split('?')[0].rstrip('/') + '/')
        folder = watch_store.watch_folder(common.profileDir)
        watch_store.SeasonIndex(folder).remember_season('kan/{0}/{1}'.format(programId, season), 'kan/{0}'.format(programId), common.UnEscapeXML((programTitle or '').strip()),
            'עונה {0}'.format(season) if season > 0 else '', listed, open_season=[2, url, moreData], open_series=[7, programUrl, 'kan|||{0}'.format(catName)])
        meta = watch_store.EpisodeMeta(folder)
        for key, facts in EpisodeFacts(group).items():
            meta.remember(key, **facts)
        return {episode['key'] for episode in listed}
    except Exception as ex:
        xbmc.log("kan RememberSeason: {0}".format(ex), xbmc.LOGERROR)
        return set()

def EpisodeDetails(key):
    """Video info of the playing episode (title, show, season, episode, plot, air date, length) from the saved season and facts: no request. `{}` when the episode
    is in no saved season (the label stays the title)."""
    try:
        return watch_store.episode_details(watch_store.watch_folder(common.profileDir), key)
    except Exception as ex:
        xbmc.log("kan EpisodeDetails: {0}".format(ex), xbmc.LOGERROR)
        return {}

def _kanEpisodeId(url):
    """The episode id of an episode page address: the number after `/p-<id>/s<n>/`, or the last number of a name-based address
    (".../the_serials/s1/123/", ".../thats_joey/123/"): it equals the feed entry's id (285 of 285 checked). None for a season or programme address."""
    episodeId = _extractKanIds(url)[2]
    if episodeId:
        return episodeId
    found = re.search(r'/(\d+)/?$', url.split('?')[0])
    return found.group(1) if found else None

def WatchKey(url):
    """The watch-history key of the episode page `url`, or '' when the history does not follow it: only an episode that is in a saved season (listed by this
    add-on from the feed) is followed, the same rule as the other channels."""
    try:
        episodeId = _kanEpisodeId(url)
        if not episodeId:
            return ''
        key = watch_store.episode_key(module, episodeId)
        seasons = watch_store.SeasonIndex(watch_store.watch_folder(common.profileDir)).load()
        return key if watch_store.episode_entry(seasons, key) is not None else ''
    except Exception as ex:
        xbmc.log("kan WatchKey: {0}".format(ex), xbmc.LOGERROR)
        return ''

def PageCredits(text):
    """Seconds at which the credits start, from the player settings in the episode page (`"creditsStart":1431`); None when absent or not positive."""
    found = re.search(r'"creditsStart"\s*:\s*(\d+)', text or '')
    return int(found.group(1)) if found and int(found.group(1)) > 0 else None

def PageStream(text):
    """The site's own stream address from the player settings in the episode page (`"file":{"dash":..., "hls":...}`): the HLS one, else the DASH one; '' when
    the page has none. Checked on the real server (2026-10-25): it needs no token and no particular user agent, plays (h264 + aac, four sizes), and is the
    stream the site's own player uses; the Kaltura route answers "the specified partner is blocked" now."""
    found = re.search(r'"file"\s*:\s*(\{[^{}]*\})', text or '')
    try:
        files = json.loads(found.group(1)) if found else {}
    except ValueError:
        return ''
    for kind in ('hls', 'dash'):
        link = files.get(kind) if isinstance(files, dict) else None
        if isinstance(link, str) and link.startswith('//'):    # the YouTube-type and kids pages name it without a scheme ("//r.il.cdn-redge.media/...")
            link = 'https:' + link
        if isinstance(link, str) and link.startswith('http'):
            return link
    return ''

def PromptProps(key, credits):
    """The ListItem property `idanplus_prompt` for the next-episode card: where the credits start, with the length (from the saved facts) it refers to. The site
    gives no next-episode hint that can be trusted (its `play_next_feed_url` is just the next entry in the feed's own order), so the card's next episode is
    always the next row of the saved season. `{}` when there is no credits time (the card then opens at its default time)."""
    if not credits:
        return {}
    data = {'credits': credits}
    try:
        total = watch_store.EpisodeMeta(watch_store.watch_folder(common.profileDir)).load().get(key, {}).get('duration')
    except Exception as ex:
        xbmc.log("kan PromptProps: {0}".format(ex), xbmc.LOGERROR)
        total = None
    if isinstance(total, int) and not isinstance(total, bool) and total > 0:
        data['total'] = total
    return {'idanplus_prompt': json.dumps(data)}

def _addMobEpisodes(entries, iconimage, moreData, season_filter=None, tracked=()):
    """List the feed's episodes (only `season_filter`'s when given). A row whose key is in `tracked` carries the zero resume point (see `common.addDir`)."""
    md = moreData.split('|||')
    catName = '' if len(md) < 2 else md[1]
    season_filter = int(season_filter) if season_filter else None
    for entry in entries:
        if season_filter and _mobEpisodeSeason(entry) != season_filter:
            continue
        name = common.GetLabelColor(common.UnEscapeXML(entry.get('title', '').strip()), keyColor="chColor")
        description = common.UnEscapeXML((entry.get('description') or entry.get('summary') or '').strip())
        image = _mobEpisodeImage(entry)
        link = _mobHref(entry)
        if not link:
            continue
        isTracked = entry.get('id') is not None and watch_store.episode_key(module, entry['id']) in tracked
        common.addDir(name, link, 3, image, infos={"title": name, "plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName}, noResume=isTracked)


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
    common.addDir(name, "toggleSortingMethod", 4, iconimage, {"title": name, "plot": "{0}[CR]{1}[CR]{2} / {3}".format(name, common.GetLocaleString(30004), common.GetLocaleString(30002), common.GetLocaleString(30003))}, module=module, isFolder=False)
    #name = common.GetLabelColor("כל התוכניות - קטגוריות", bold=True, color="none")
    #common.addDir(name, '{0}/lobby/kan-box'.format(baseUrl), 1, iconimage, infos={"title": name}, module=module, moreData=common.GetLocaleString(30602))
    name = common.GetLabelColor("כל התוכניות", bold=True, color="none")
    common.addDir(name, '{0}/lobby/kan11'.format(baseUrl), 1, iconimage, infos={"title": name}, module=module, moreData='{0}__4444'.format(common.GetLocaleString(30602)))
    name = common.GetLabelColor("תוכניות אקטואליה", bold=True, color="none")
    common.addDir(name, '{0}/lobby/newstv'.format(baseUrl), 1, iconimage, infos={"title": name}, module=module, moreData=common.GetLocaleString(30602))
    name = common.GetLabelColor("דיגיטל", bold=True, color="none")
    common.addDir(name, '{0}/lobby/digital-lobby'.format(baseUrl), 1, iconimage, infos={"title": name}, module=module, moreData='{0}__4464'.format(common.GetLocaleString(30602)))
    name = common.GetLabelColor(common.GetLocaleString(30607), bold=True, color="none")
    common.addDir(name, baseKidsUrl, 5, module23Icon, infos={"title": name}, module=module, moreData=common.GetLocaleString(30607))
    name = common.GetLabelColor("כאן - ארכיון", bold=True, color="none")
    common.addDir(name, '{0}/lobby/archive/'.format(baseUrl), 41, iconimage, infos={"title": name}, module=module, moreData="כאן ארכיון")
    name = common.GetLabelColor("תכניות רדיו", bold=True, color="none")
    common.addDir(name, '', 21, iconimage, infos={"title": name}, module=module)
    name = common.GetLabelColor("פודקאסטים", bold=True, color="none")
    common.addDir(name, '4451', 31, iconimage, infos={"title": name}, module=module)
    name = common.GetLabelColor("פודקאסטים לילדים", bold=True, color="none")
    common.addDir(name, '{0}/lobby-kids/podcasts-kids/'.format(baseKidsUrl), 33, module23Icon, infos={"title": name}, module=module)

UA = userAgent  # אם יש לך משתנה קיים ל-UA
REF = 'https://www.kan.org.il/'

def _encode_url(u: str) -> str:
    # מקודד רק את החלק שאחרי הדומיין (כולל עברית/רווחים)
    # וגם מסיר פרמטרים מיותרים אם רוצים
    if not u:
        return u
    # פיצול על "://" כדי לשמר את הפרוטוקול והדומיין בלי קידוד
    try:
        scheme, rest = u.split("://", 1)
    except ValueError:
        return u
    if "/" in rest:
        host, path = rest.split("/", 1)
        path = quote(path, safe="/:?=&._-")  # משאיר תווים בטוחים, מקודד עברית/רווחים
        return f"{scheme}://{host}/{path}"
    else:
        return u

def _with_headers(u: str) -> str:
    # הוספת כותרות בקוד קודי (Pipe) כדי לעקוף חסימות HEAD/GET
    if not u:
        return u
    # אל תקודד את ה־UA/Referer פעמיים; Kodi דורש raw או percent-encode
    return f"{u}|User-Agent={quote(UA)}&Referer={quote(REF)}&Accept=*/*"

def _pick_image_from_media_group(serie: dict) -> str:
    # עובר על כל media_item ובוחר את הראשון התקין (מהגדול לקטן)
    try:
        items = serie['media_group'][0]['media_item']
    except Exception:
        return ''
    # נסה מהסוף להתחלה (בד"כ הגדלים הגדולים בסוף)
    for it in reversed(items):
        src = it.get('src') or ''
        if not src:
            continue
        src = _encode_url(src.split('?')[0])  # הסרת query + קידוד עברית
        if src:
            return _with_headers(src)
    return ''

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
                link = _mobProgramLink(serie)      # one entry without a link or a description (the feed has them) must not take the whole list down
                if not link:
                    continue
                name = common.GetLabelColor(serie.get('title') or '', keyColor="prColor", bold=True)
                description = serie.get('description') or ''
                image = _pick_image_from_media_group(serie)
                
                common.addDir(name, link, 7, image[:image.find('?')], infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
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
            common.addDir(name, link, 7, image, infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
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
            common.addDir(name, link, 7, image, infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
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
                common.addDir(name, link, 8, iconimage, infos={"title": name, "plot": name}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
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
                common.addDir(name, link, 7, image, infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
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
        common.addDir(name, link, 7, image, infos={"title": name, "plot": description}, module=module, moreData=catName, urlParamsData={'catName': catName})
    
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
        common.addDir(name, '{0}?page={1}'.format(_url, page-1), 9, iconimage, infos={"title": name, "plot": name}, module=module, moreData=catName)
    if pages > page:
        name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
        common.addDir(name, '{0}?page={1}'.format(_url, page+1), 9, iconimage, infos={"title": name, "plot": name}, module=module, moreData=catName)
    if pages > 1:
        name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
        common.addDir(name, '{0}?p={1}&pages={2}'.format(_url, page, pages), 45, iconimage, infos={"title": name, "plot": name}, module=module, moreData=catName)

def GetSubCategoriesList(url, iconimage):
    name = common.GetLabelColor("קטנטנים", bold=True, color="none")
    common.addDir(name, '{0}/lobby-kids/tiny/'.format(baseKidsUrl), 1, iconimage, infos={"title": name}, module=module, moreData='{0}__4462'.format(common.GetLocaleString(30607)))
    name = common.GetLabelColor("ילדים ונוער", bold=True, color="none")
    common.addDir(name, '{0}/lobby-kids/kids-teens/'.format(baseKidsUrl), 1, iconimage, infos={"title": name}, module=module, moreData='{0}__4453'.format(common.GetLocaleString(30607)))

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
        common.addDir(name, link, 6, common.quoteNonASCII(iconimage), infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})

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

    programId, _, _ = _extractKanIds(data)
    if programId:
        prog = GetMobProgram(programId)
        entries = prog.get('entry') or []
        if entries:
            seasonLinks = _mobSeasonLinks(data, entries)
            if seasonLinks:
                for _, name, link in seasonLinks:
                    if not link.startswith('http'):
                        link = '{0}{1}'.format(domain, link)
                    common.addDir(name, link, 2, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': catName})
                return
            GetEpisodesList(data, iconimage, moreData)
            return

    #text = common.GetCF(data)
    text = cache.get(common.GetCF, 24, data, table='pages')
    if text==[]:
        text = cache.get(common.GetCF, 0, data, table='pages')
    if not text:
        return
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
        common.addDir(name, link, 2, iconimage, infos={"title": name, "plot": description}, module=module, urlParamsData={'catName': catName})

def GetEpisodesList(url, iconimage, moreData=''):
    md = moreData.split('|||')
    site = md[0]
    catName = '' if len(md) < 2 else md[1]

    programId, seasonFilter, _ = _extractKanIds(url)
    if programId:
        prog = GetMobProgram(programId)
        entries = prog.get('entry') or []
        if entries:
            tracked = RememberSeason(programId, prog.get('title'), entries, int(seasonFilter) if seasonFilter else None, url, moreData)
            _addMobEpisodes(entries, iconimage, moreData, seasonFilter, tracked)
            return

    #text = common.GetCF(url)
    text = cache.get(common.GetCF, 24, url, table='pages')
    if text==[]:
        text = cache.get(common.GetCF, 0, url, table='pages')
    if not text:
        return
    #text = common.OpenURL(url)
    body = re.compile('<main id="main"(.*?)</main>', re.S).findall(text)
    if len(body) < 1:
        return
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
            common.addDir(name, link, 3, image, infos={"title": name, "plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
    else:
        matches1 = re.compile('<div class="block-media card-media(.*?)</div>\s*?</div>\s*?</div>\s*?</div>', re.S).findall(body[0])
        #matches = re.compile('<div class="media-wrap(.*?)<div class="ec-section section', re.S).findall(body[0])
        if len(matches1) > 0:
            matches = re.compile('desktop-vod-bg-image: url\(\'(.*?)\'\).*?"title.*?>(.*?)</h(.*?"info-description">(.*?)</div>.*?|.*?)<a href="(.*?)"', re.S).findall(matches1[0])
            if len(matches) < 1:
                matches = re.compile('desktop-vod-bg-image: url\(\'(.*?)\'\).*?info-name.*?title="(.*?)"(.*?"info-description">(.*?)</div>.*?|.*?)<a href="(.*?)"', re.S).findall(matches1[0])
            name = common.UnEscapeXML(matches[0][1].strip())
            image = GetImageLink(common.quoteNonASCII(matches[0][0]), name)
            name = common.GetLabelColor(name, keyColor="chColor")
            description = common.UnEscapeXML(matches[0][3].strip())# if len(matches[0]) > 4 ''
            link = '{0}/{1}'.format(domain, matches[0][4])# if len(matches[0]) > 4 else '{0}/{1}'.format(domain, matches[0][2])
            common.addDir(name, link, 3, image, infos={"title": name, "plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
        else:
            matches = re.compile('<div class="youtube-player(.*?)<div class="ec-section section', re.S).findall(body[0])
            matches = re.compile('data-video-src="(.*?)".*?"h2">(.*?)</h2>.*?"info-description">(.*?)</div>', re.S).findall(matches[0])
            name = common.GetLabelColor(common.UnEscapeXML(matches[0][1].strip()), keyColor="chColor")
            description = common.UnEscapeXML(matches[0][2].strip())
            url = matches[0][0].replace('/embed', '')
            common.addDir(name, matches[0][0].replace('/embed', ''), 3, iconimage, infos={"title": name, "plot": description}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})

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
            common.addDir(name, link, 3, image, infos={"title": name, "plot": description}, module=module, isFolder=False, isPlayable=True, urlParamsData={'catName': 'חינוכית 23'})
        if len(matches) < 9:
            if page > pagesPerList:
                name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
                common.addDir(name, '{0};{1}'.format(catId, prevPage), 6, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': 'חינוכית 23'})
            break
        if page == stopPage:
            if page > pagesPerList:
                name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
                common.addDir(name, '{0};{1}'.format(catId, prevPage), 6, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': 'חינוכית 23'})
            name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
            common.addDir(name, '{0};{1}'.format(catId, page), 6, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': 'חינוכית 23'})
            break
        
def GetRadioCategoriesList(iconimage):
    name = common.GetLabelColor("כאן ב", bold=True, color="none")
    common.addDir(name, 'kan-b', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/bet.png', infos={"title": name}, module=module, moreData='4483')
    name = common.GetLabelColor("כאן גימל", bold=True, color="none")
    common.addDir(name, 'kan-gimel', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/gimel.png', infos={"title": name}, module=module, moreData='4490')
    name = common.GetLabelColor("כאן 88", bold=True, color="none")
    common.addDir(name, 'kan-88', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/88fm.png', infos={"title": name}, module=module, moreData='4504')
    name = common.GetLabelColor("כאן תרבות", bold=True, color="none")
    common.addDir(name, 'kan-tarbut', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/culture.png', infos={"title": name}, module=module, moreData='4497')
    name = common.GetLabelColor("כאן קול המוסיקה", bold=True, color="none")
    common.addDir(name, 'kan-music', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/music.png', infos={"title": name}, module=module, moreData='4518')
    name = common.GetLabelColor("כאן מורשת", bold=True, color="none")
    common.addDir(name, 'kan-moreshet', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/moreshet.png', infos={"title": name}, module=module, moreData='4511')
    name = common.GetLabelColor("כאן Reka", bold=True, color="none")
    common.addDir(name, 'kan-reka', 22, 'https://raw.githubusercontent.com/Fishenzon/repo/master/plugin.video.idanplus/images/reka.png', infos={"title": name}, module=module, moreData='4525')

def GetRadioSeriesList(url, catName, id=None):
    if id:
        i = 1
        while (i > 0):
            url = '{0}?from={1}&id={2}'.format(mobapi, i, id)
            matches = common.OpenURL(url, responseMethod='json').get('entry')
            i = 0 if len(matches) < 200 else 200 + i
            for serie in matches:
                link = _mobHref(serie)      # one entry without a link or a description (the feed has them) must not take the whole list down
                if not link:
                    continue
                name = common.GetLabelColor(serie.get('title') or '', keyColor="prColor", bold=True)
                description = serie.get('description') or ''
                image = serie['media_group'][0]['media_item'][2]['src']
                common.addDir(name, link, 23, image[:image.find('?')], infos={"title": name, "plot": description}, module=module, moreData=catName, urlParamsData={'catName': catName})
        return
    text = common.GetCF('{0}/content/kan/{1}/'.format(baseUrl, url), userAgent)
    #text = common.OpenURL(url)
    match = re.compile('<div class="tab-pane fade show active(.*?)</ul>', re.S).findall(text)
    matches = re.compile('<a href="(.*?)".*?background-image: url\((.*?)\).*?"card-title">(.*?)</.*?"text-on-hover">.*?<div>(.*?)</div>.*?</li>', re.S).findall(match[0])
    for link, iconimage, name, description in matches:
        name = common.UnEscapeXML(name.strip())
        iconimage = GetImageLink(common.UnEscapeXML(iconimage), name)
        name = common.GetLabelColor(name, keyColor="prColor", bold=True)
        common.addDir(name, link, 23, iconimage, infos={"title": name, "plot": common.UnEscapeXML(description)}, module=module, moreData=catName, urlParamsData={'catName': catName})

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
            common.addDir(name, '{0}|||radio'.format(link), 3, iconimage, infos={"title": name}, module=module, moreData='best', isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
        if len(matches) < 10:
            if page > pagesPerList:
                name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
                common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 23, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': catName})
            break
        if page == stopPage:
            if page > pagesPerList:
                name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
                common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 23, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': catName})
            name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
            common.addDir(name, '{0};{1}'.format(progUrl, page), 23, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': catName})
            break

def Play(url, name='', iconimage='', quality='best'):
    props, resume, details = None, None, None
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
        # the watch history follows the episodes of a saved season; its "resume or start over" question (setting watch_resume) comes before any request
        key = WatchKey(url)
        if key:
            proceed, resume = watch_ui.ChooseResume(key, name, iconimage)
            if not proceed:
                if common.GetHandle() >= 0:   # run as a script (handle -1) nothing waits for an answer: cancelling is quiet
                    xbmcplugin.setResolvedUrl(common.GetHandle(), False, xbmcgui.ListItem())
                return
        page = {}
        final = GetPlayerKanUrl(url, headers=headers, quality=quality, page=page)
        if key:
            props = {'idanplus_key': key}
            props.update(PromptProps(key, page.get('credits')))
            details = EpisodeDetails(key)
    common.PlayStream(final, quality, name, iconimage, adaptive=True, props=props, resume=resume, details=details)

def _mobKalturaEntryId(entry):
    content = entry.get('content') or {}
    src = (content.get('src') or '').strip()
    if src:
        match = re.search(r'entryId/([^/?&]+)', src)
        if match:
            return match.group(1)
    return None

def _kanShowReferer(page_url):
    clean = page_url.split('?')[0].rstrip('/')
    if re.search(r'/\d+/?$', clean):
        return clean.rsplit('/', 1)[0] + '/'
    return baseKidsUrl if 'kankids' in page_url else baseUrl

def _kanStreamReferer(page_url):
    ref = page_url.split('?')[0]
    return ref if ref.endswith('/') else ref + '/'

def _kanStreamHeaders(stream_url, page_url, ua):
    ref = _kanStreamReferer(page_url)
    origin = baseKidsUrl.rstrip('/') if 'kankids' in page_url else baseUrl.rstrip('/')
    if stream_url.startswith('//'):
        stream_url = 'https:' + stream_url
    return "{0}|User-Agent={1}&Referer={2}&Origin={3}&Accept=*/*".format(
        stream_url, quote(ua), quote(ref), quote(origin))

def KanPageAddress(url):
    """Where to read the episode page `url` from. `www.kan.org.il` answers Kodi's own network stack with 403 (measured in a real Kodi 21 on 2026-10-25: Python
    `requests` and `urllib` and Kodi's curl, every header set, while the same PC's other Python gets 200), but the mobile API host serves the very same page, and
    its `?app=true` form is half the size with the same player settings (stream, credits time). The kids host is not blocked and is read as it is."""
    clean = url.split('?')[0]
    if clean.startswith(baseUrl + '/'):
        return baseMobApiUrl + clean[len(baseUrl):] + '?app=true'
    return clean

def _fetchKanPage(url, ua):
    page = common.OpenURL(KanPageAddress(url), headers={'User-Agent': ua, 'Accept-Language': 'he-IL,he;q=0.9'}, responseMethod='text')
    if page and 'Just a moment' not in page:
        return page
    text = common.GetCF(url, ua, referer=_kanShowReferer(url))    # the old route, for a page the first one could not give
    if not text:
        return None
    return text

def _getKanPage(url, fresh=False):
    if fresh:
        return _fetchKanPage(url, userAgent) or ''
    text = cache.get(_fetchKanPage, 24, url, userAgent, table='pages')
    if not text:
        text = cache.get(_fetchKanPage, 0, url, userAgent, table='pages')
    return text or ''

def GetPlayerKanUrl(url, headers={}, quality='best', page=None):
    """The playable address of the episode page `url`. `page`, when given, is a dict that receives what the page itself says about the episode (`credits`)."""
    last_ex = None
    for attempt in range(3):
        try:
            return _resolvePlayerKanUrl(url, headers, quality, page)
        except Exception as ex:
            last_ex = ex
            common.ResetCFSession()
            if attempt < 2:
                xbmc.sleep(600)
    raise last_ex

def _resolvePlayerKanUrl(url, headers={}, quality='best', page=None):
    from urllib.parse import urlsplit, urlunsplit, quote

    def _normalize_master(u):
        # מחזיר (base, original) כדי למנוע כפילויות בפרמטרים
        if u.startswith('//'):
            u = 'https:' + u
        parts = urlsplit(u)
        base = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
        return base, u

    def _pipe_headers(u, ua, page_url):
        return _kanStreamHeaders(u, page_url, ua)

    ref = baseKidsUrl if 'kankids' in url else baseUrl
    programId, _, episodeId = _extractKanIds(url)
    mobEntry = None

    text = _getKanPage(url, fresh=True)
    if page is not None and PageCredits(text):
        page['credits'] = PageCredits(text)
    if text:
        hls_match = re.search(r'data-hls-url="([^"]+)"', text)
        dash_match = re.search(r'data-dash-url="([^"]+)"', text)
        if hls_match or dash_match:
            master_raw = (hls_match.group(1) if hls_match else dash_match.group(1)).strip()
            _, master_with_query = _normalize_master(master_raw)
            return _pipe_headers(master_with_query, userAgent, url)
        # the site's own stream, named in the page's player settings: tried before the feed's YouTube / Redge / Kaltura addresses (a page without one falls to them)
        if PageStream(text):
            return _pipe_headers(PageStream(text), userAgent, url)

    if programId:
        prog = GetMobProgram(programId)
        mobEntry = _mobFindEntry(prog.get('entry') or [], episodeId, url)
        if mobEntry:
            streamType, streamUrl = _mobStreamFromEntry(mobEntry)
            if streamType == 'youtube':
                return common.GetYouTube(streamUrl)
            if streamType == 'stream' and 'redge' in streamUrl:
                return _pipe_headers(streamUrl, userAgent, url)

    if not text:
        raise Exception('Unable to resolve playable URL from page')

    # DailyMotion player
    if 'kanPlayers' in url:
        match = re.compile(r"dailymotion.*?video:\s*?'(.*?)'", re.S).findall(text)
        if match:
            return 'dailymotion-video/{0}|'.format(match[0])

    # ByPlayer / Redirector
    if 'ByPlayer' in url:
        match = re.compile(r'bynetURL:\s*"(.*?)"').findall(text)
        if not match:
            match = re.compile(r'"UrlRedirector":"(.*?)"').findall(text)
        if match:
            link = match[0].replace('\u0026', '&')
            # חלק מה-Redirector עובד ב-http
            if link.startswith('https://api.bynetcdn.com/Redirector'):
                link = link.replace('https', 'http', 1)
            if 'api.bynetcdn.com/Redirector' not in link:
                link = common.GetStreams(link, headers=headers, quality=quality)
            return _pipe_headers(link, userAgent, url)

    # Redge CDN (data-hls-url / data-dash-url) - fallback if early check missed
    hls_match = re.search(r'data-hls-url="([^"]+)"', text)
    dash_match = re.search(r'data-dash-url="([^"]+)"', text)
    if hls_match or dash_match:
        master_raw = (hls_match.group(1) if hls_match else dash_match.group(1)).strip()
        _, master_with_query = _normalize_master(master_raw)
        return _pipe_headers(master_with_query, userAgent, url)

    # ישנים: media.(ma)kan.org.il עם hls:"..."
    if re.search(r'media\.(ma)?kan\.org\.il', url):
        match = re.compile(r'hls:\s*?"(.*?)"').findall(text)
        if match:
            link = common.GetStreams(match[0], headers=headers, quality=quality)
            return _pipe_headers(link, userAgent, url)

    # Kaltura ישיר
    if 'kaltura' in url:
        text2 = cache.get(common.GetCF, 24, url, userAgent, table='pages')
        if text2 == []:
            text2 = cache.get(common.GetCF, 0, url, userAgent, table='pages')
        match = re.compile(r'window\.kalturaIframePackageData\s*=\s*{(.*?)};').findall(text2)
        if match:
            result = json.loads('{'+match[0]+'}')
            link = result['entryResult']['meta'].get('hlsStreamUrl') or ''
            if link:
                link = common.GetStreams(link, headers=headers, quality=quality)
                return _pipe_headers(link, userAgent, url)

    # entryId → Kaltura / YouTube
    match = re.compile(r'<div id="video_item".*?data-entryId="(.*?)"', re.S).findall(text)
    if match:
        domain = baseKidsUrl if 'kankids' in url else baseUrl
        link = common.GetKaltura(match[0], 2717431, domain, userAgent, quality=quality)
        return _pipe_headers(link, userAgent, url)

    yt = re.compile(r'data-video-src="(.*?)"').findall(text)
    if yt:
        return common.GetYouTube(yt[0].replace('/embed', ''))

    if mobEntry:
        entryId = _mobKalturaEntryId(mobEntry)
        if entryId:
            link = common.GetKaltura(entryId, 2717431, ref, userAgent, quality=quality)
            if link:
                return _pipe_headers(link, userAgent, url)

    raise Exception('Unable to resolve playable URL from page')


def WatchLive(channelID, name='', iconimage='', quality='best', type='video'):
    channel = common.GetChannel(channelID)
    isAdaptive = common.GetChannelAdaptive(channel)
    linkDetails = channel.get('linkDetails')
    link = linkDetails['link']
    if '.m3u8' in link and not isAdaptive:
        isAdaptive = True
    final = '{0}|User-Agent={1}&Referer={2}'.format(link, quote(userAgent), quote(baseUrl))
    common.PlayStream(final, quality, name, iconimage, adaptive=isAdaptive)

def GetPodcastsList(id=None):
    if id:
        i = 1
        while (i > 0):
            url = '{0}?from={1}&id={2}'.format(mobapi, i, id)
            matches = common.OpenURL(url, responseMethod='json').get('entry')
            i = 0 if len(matches) < 200 else 200 + i
            for serie in matches:
                link = _mobHref(serie)      # one entry without a link or a description (the feed has them) must not take the whole list down
                if not link:
                    continue
                name = common.GetLabelColor(serie.get('title') or '', keyColor="prColor", bold=True)
                description = serie.get('description') or ''
                image = serie['media_group'][0]['media_item'][2]['src']
                common.addDir(name, link, 32, image[:image.find('?')], infos={"title": name, "plot": description}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
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
        common.addDir(name, link, 32, image, infos={"title": name, "plot": common.UnEscapeXML(description.strip())}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})

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
                common.addDir(name, link, 3, image, infos={"title": name, "plot": common.UnEscapeXML(description.strip())}, module=module, isFolder=False, isPlayable=True, urlParamsData={'catName': 'כאן פודקאסטים'})
        if len(body) < 8:
            if page > pagesPerList:
                name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
                common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 32, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
            break
        if page == stopPage:
            if page > pagesPerList:
                name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
                common.addDir(name, '{0};{1}'.format(progUrl, prevPage), 32, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
            name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
            common.addDir(name, '{0};{1}'.format(progUrl, page), 32, iconimage, infos={"title": name, "plot": name}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})
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
        common.addDir(name, '{0}{1}'.format(baseKidsUrl, link), 32, image, infos={"title": name, "plot": description.replace('&nbsp;', '').strip()}, module=module, urlParamsData={'catName': 'כאן פודקאסטים'})

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
        common.addDir(name, link, 2, iconimage, infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})
    
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
        common.addDir(name, link, 2, image, infos={"title": name, "plot": description}, module=module, moreData='kan|||{0}'.format(catName), urlParamsData={'catName': catName})

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
            common.addDir(name, '{0}/{1}'.format(archiveUrl, url), 43, icon, infos={"title": name, "plot": description}, module=module, urlParamsData={'catName': catName})
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
        common.addDir(name, '{0}/{1}'.format(archiveUrl, url), 43, icon, infos={"title": name, "plot": description}, module=module, urlParamsData={'catName': catName})

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
        common.addDir(name, common.encode(entryId, 'utf-8').replace('​&amp;', '&'), 3, image, infos={"title": name, "plot": description.replace('&nbsp;', '').strip()}, module=module, moreData=bitrate, isFolder=False, isPlayable=True, urlParamsData={'catName': catName})
    matches = re.compile('<ul class="pagination">(.*?)</div>', re.S).findall(text)
    if len(matches) < 1:
        return
    page = int(re.compile('<span class="page-link curPage">(.*?)</span>').findall(matches[0])[0])
    li = re.compile('<li(.*?)>(.*?)</li>', re.S).findall(matches[0])
    last = re.compile('<a.*?page=(.*?)"').findall(li[-1][1])
    pages = int(last[0]) if len(last) > 0 else page

    if page > 1:
        name = common.GetLabelColor(common.GetLocaleString(30011), color="green")
        common.addDir(name, '{0}?page={1}'.format(_url, page-1), 43, iconimage, infos={"title": name, "plot": name}, module=module)
    if pages > page:
        name = common.GetLabelColor(common.GetLocaleString(30012), color="green")
        common.addDir(name, '{0}?page={1}'.format(_url, page+1), 43, iconimage, infos={"title": name, "plot": name}, module=module)
    if pages > 1:
        name = common.GetLabelColor(common.GetLocaleString(30013), color="green")
        common.addDir(name, '{0}?p={1}&pages={2}'.format(_url, page, pages), 44, iconimage, infos={"title": name, "plot": name}, module=module)

def DeleteImages():
    for the_file in os.listdir(logosDir):
        file_path = os.path.join(logosDir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as ex:
            xbmc.log("{0}".format(ex), xbmc.LOGERROR)
            
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