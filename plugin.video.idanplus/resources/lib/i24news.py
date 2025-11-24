# -*- coding: utf-8 -*-
"""
i24NEWS VOD Integration for Kodi
================================
Clean, well-structured implementation using Wiztivi API

Features:
- Automatic authentication (no user action required)
- Multi-language support (English, Hebrew, French, Arabic)
- Browse TV shows by language
- Watch episodes via Brightcove player
- Smart caching for performance

"""

import time
import xbmc
import xbmcgui
import resources.lib.common as common


# ============================================================================
# CONSTANTS
# ============================================================================

module = 'i24news'
API_BASE = 'https://api.i24news.wiztivi.io'

# Language configuration with catalog IDs
LANGUAGES = {
    'en': {
        'name': 'English',
        'catalogId': '9e44d596-82e6-4c4c-8a1c-96f84ae49bd5',
        'searchKey': 'search_en'
    },
    'he': {
        'name': 'עברית',
        'catalogId': '0e8ab8d2-dd73-44ce-a563-bcf82757ad45',
        'searchKey': 'search_he'
    }
}

# ============================================================================
# AUTHENTICATION
# ============================================================================

def GetAuthToken():
    """
    Get valid authentication token automatically
    Returns cached token if valid, otherwise gets fresh one
    """
    cached_token = common.GetAddonSetting('i24news_token')
    if cached_token and IsTokenValid(cached_token):
        xbmc.log("i24news: Using cached token", xbmc.LOGINFO)
        return cached_token
    
    xbmc.log("i24news: Getting fresh token from Wiztivi", xbmc.LOGINFO)
    auth_data = GetAnonymousAuth()
    return auth_data.get('accessToken') if auth_data else None


def IsTokenValid(token):
    """Check if JWT token is still valid (not expired)"""
    try:
        import json, base64
        
        # Decode JWT payload
        parts = token.split('.')
        if len(parts) != 3:
            return False
        
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        data = json.loads(base64.b64decode(payload))
        exp = data.get('exp', 0)
        remaining = exp - int(time.time())
        
        if remaining > 60:
            xbmc.log("i24news: Token valid for {0} seconds".format(remaining), xbmc.LOGINFO)
            return True
        return False
    except:
        return False


def GetAnonymousAuth():
    """Get fresh authentication from Wiztivi - NO credentials needed!"""
    try:
        hardware_id = time.strftime("%Y-%m-%dT%H:%M:%S.000")
        auth_url = "{0}/authenticate?userName=I24News&hardwareId={1}&hardwareIdType=browser".format(
            API_BASE, hardware_id
        )
        
        session = common.GetSession()
        response = session.get(auth_url, timeout=10)
        
        if response.status_code == 200:
            auth_data = response.json()
            access_token = auth_data.get('accessToken')
            if access_token:
                common.SetAddonSetting('i24news_token', access_token)
                xbmc.log("i24news: ✅ Authentication SUCCESS!", xbmc.LOGINFO)
                return auth_data
        
        xbmc.log("i24news: Authentication failed - status {0}".format(response.status_code), xbmc.LOGERROR)
        return None
    except Exception as e:
        xbmc.log("i24news: Auth error: {0}".format(str(e)), xbmc.LOGERROR)
        return None


def GetHeaders(with_auth=True):
    """Build HTTP headers with optional authentication"""
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    }
    if with_auth:
        token = GetAuthToken()
        if token:
            headers['Authorization'] = 'Bearer {0}'.format(token)
    return headers


# ============================================================================
# API COMMUNICATION
# ============================================================================

def GetAPIData(endpoint, params=None):
    """Fetch data from Wiztivi API"""
    try:
        url = '{0}/{1}'.format(API_BASE, endpoint)
        if params:
            param_str = '&'.join(['{0}={1}'.format(k, common.quote_plus(str(v))) for k, v in params.items()])
            url = '{0}?{1}'.format(url, param_str)
        
        headers = GetHeaders(with_auth=True)
        xbmc.log("i24news: API call: {0}".format(url), xbmc.LOGINFO)
        
        session = common.GetSession()
        response = session.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        
        xbmc.log("i24news: API error {0}".format(response.status_code), xbmc.LOGERROR)
        return None
    except Exception as e:
        xbmc.log("i24news: API exception: {0}".format(str(e)), xbmc.LOGERROR)
        return None


# ============================================================================
# NAVIGATION MENUS
# ============================================================================

def ShowLanguages():
    """Display language selection: English, Hebrew"""
    xbmc.log("i24news: Showing language menu", xbmc.LOGINFO)
    
    for lang_code, lang_info in LANGUAGES.items():
        name = lang_info['name']
        url = 'action=catalog&language={0}'.format(lang_code)
        iconimage = common.GetIconFullPath('i24news.png')
        
        common.addDir(
            name=common.GetLabelColor(name, bold=True, color="none"),
            url=url,
            mode=-1,
            iconimage=iconimage,
            infos={
                'Title': name,
                'Plot': 'i24NEWS {0} - Watch TV Shows & News Programs'.format(lang_info['name'])
            },
            module=module,
            isFolder=True
        )


def ShowCatalog(language):
    """Display TV shows for selected language"""
    lang_info = LANGUAGES.get(language)
    if not lang_info:
        return
    
    xbmc.log("i24news: Loading {0} catalog".format(lang_info['name']), xbmc.LOGINFO)
    
    # Fetch catalog
    catalog_id = lang_info['catalogId']
    endpoint = 'catalogs/{0}/cms/categories/tvshows'.format(catalog_id)
    
    # Try cache first
    from resources.lib import cache
    data = cache.get(GetAPIData, 24, endpoint, {'depth': 2}, table='pages')
    if not data:
        data = GetAPIData(endpoint, {'depth': 2})
    
    if not data or not data.get('categories'):
        xbmcgui.Dialog().notification('i24NEWS', 'No shows found', xbmcgui.NOTIFICATION_WARNING, 3000)
        return
    
    # Display shows
    iconimage = common.GetIconFullPath('i24news.png')
    for show in data['categories']:
        show_name = show.get('name', 'Unknown')
        show_desc = show.get('description', '')
        contents_url = show.get('contentsLocation', '')
        
        if not contents_url:
            continue
        
        # Get thumbnail
        thumb = iconimage
        images = show.get('images', [])
        if images:
            thumb = images[0].get('url', iconimage)
        
        url = 'action=episodes&show_name={0}&contents_url={1}'.format(
            common.quote_plus(show_name),
            common.quote_plus(contents_url)
        )
        
        common.addDir(
            name=common.GetLabelColor(show_name, keyColor="prColor", bold=True),
            url=url,
            mode=-1,
            iconimage=thumb,
            infos={'Title': show_name, 'Plot': show_desc},
            module=module,
            isFolder=True
        )


def ShowEpisodes(show_name, contents_url, start=0):
    """Display episodes for a TV show"""
    xbmc.log("i24news: Loading episodes for '{0}'".format(show_name), xbmc.LOGINFO)
    
    # Parse contents URL to get search parameters
    try:
        parsed = common.url_parse(contents_url)
        params = common.parse_qs(parsed.query)
        
        # Build request params
        api_params = {
            'type': params.get('type', ['DYNAMIC'])[0],
            'value': params.get('value', [''])[0],
            'provider': params.get('provider', ['brightcove'])[0],
            'key': params.get('key', ['search_en'])[0],
            'value2': params.get('value2', ['-published_at'])[0],
            'start': start,
            'number': 50
        }
        
        # Fetch episodes
        episodes = GetAPIData('contents', api_params)
        
        if not episodes:
            xbmcgui.Dialog().notification('i24NEWS', 'No episodes found', xbmcgui.NOTIFICATION_WARNING, 3000)
            return
        
        # Display episodes
        iconimage = common.GetIconFullPath('i24news.png')
        for video in episodes:
            video_id = video.get('id', '')
            video_name = video.get('name', 'Unknown')
            video_desc = video.get('description', '')
            duration = video.get('duration', 0)
            
            if not video_id:
                continue
            
            # Get thumbnail
            thumb = iconimage
            images = video.get('images', [])
            if images:
                thumb = images[0].get('url', iconimage)
            
            url = 'action=play&video_id={0}&video_name={1}'.format(
                video_id,
                common.quote_plus(video_name)
            )
            
            common.addDir(
                name= common.GetLabelColor(video_name, keyColor="chColor"),
                url=url,
                mode=-1,
                iconimage=thumb,
                infos={'Title': video_name, 'Plot': video_desc, 'Duration': duration},
                module=module,
                isFolder=False,
                isPlayable=True
            )
        
        # Add "More" button if there might be more episodes
        if len(episodes) == 50:
            url = 'action=episodes&show_name={0}&contents_url={1}&start={2}'.format(
                common.quote_plus(show_name),
                common.quote_plus(contents_url),
                start + 50
            )
            common.addDir(
                name='[COLOR yellow]▶ Load More[/COLOR]',
                url=url,
                mode=-1,
                iconimage=iconimage,
                infos={'Title': 'Load More Episodes'},
                module=module,
                isFolder=True
            )
        
    except Exception as e:
        xbmc.log("i24news: Error showing episodes: {0}".format(str(e)), xbmc.LOGERROR)


# ============================================================================
# VIDEO PLAYBACK
# ============================================================================

def GetStreamURL(video_id):
    """
    Get HLS stream URL from Wiztivi API
    Returns m3u8 URL with fresh Fastly token
    """
    try:
        # Wiztivi media endpoint - returns stream URL with fresh token
        media_url = '{0}/contents/brightcove/{1}/medias/{1}_hls'.format(API_BASE, video_id)
        
        headers = GetHeaders(with_auth=True)
        xbmc.log("i24news: Fetching stream URL for video {0}".format(video_id), xbmc.LOGINFO)
        
        session = common.GetSession()
        response = session.get(media_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            xbmc.log("i24news: Media API error {0}".format(response.status_code), xbmc.LOGERROR)
            return None
        
        data = response.json()
        stream_url = data.get('url')
        
        if stream_url:
            xbmc.log("i24news: Stream URL obtained successfully", xbmc.LOGINFO)
            return stream_url
        else:
            xbmc.log("i24news: No URL in response", xbmc.LOGERROR)
            return None
            
    except Exception as ex:
        xbmc.log("i24news: GetStreamURL error: {0}".format(str(ex)), xbmc.LOGERROR)
        return None


def PlayVideo(video_id, video_name):
    """Play video using Wiztivi stream URL"""
    xbmc.log("i24news: Playing {0}".format(video_id), xbmc.LOGINFO)
    
    # Get stream URL with fresh Fastly token from Wiztivi
    stream_url = GetStreamURL(video_id)
    
    if not stream_url:
        xbmcgui.Dialog().notification('i24NEWS', 'Failed to get video stream', xbmcgui.NOTIFICATION_ERROR, 3000)
        xbmc.log("i24news: Failed to get stream URL for video {0}".format(video_id), xbmc.LOGERROR)
        return
    
    xbmc.log("i24news: Playing stream: {0}".format(stream_url[:100]), xbmc.LOGINFO)
    common.PlayStream(stream_url, 'best', video_name, common.GetIconFullPath('i24news.png'))


# ============================================================================
# MAIN ROUTER
# ============================================================================

def Run(name='', url='', mode=-1, iconimage='', moreData=''):
    """
    Main router - handles all actions
    Called by addon with: Run(name, url, mode, iconimage, moreData)
    
    Mode values:
    -1 = Show language menu (entry point)
    Other modes parsed from url params
    """
    xbmc.log("i24news: Run() called - mode={0}, url={1}".format(mode, url), xbmc.LOGINFO)
    
    # Parse params from URL if present
    params = {}
    if url:
        try:
            # URL is already just the query string (no domain/path)
            # e.g., "action=catalog&language=he"
            query = url
            if query:
                params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                         for k, v in common.parse_qs(query).items()}
        except Exception as e:
            xbmc.log("i24news: Error parsing URL: {0}".format(str(e)), xbmc.LOGERROR)
    
    # Get action from params or default based on mode
    action = params.get('action', 'main' if mode == -1 else '')
    
    xbmc.log("i24news: Action='{0}', params={1}".format(action, str(params)), xbmc.LOGINFO)
    
    if action == 'catalog':
        ShowCatalog(params.get('language', 'en'))
    elif action == 'episodes':
        ShowEpisodes(
            params.get('show_name', ''),
            params.get('contents_url', ''),
            int(params.get('start', 0))
        )
    elif action == 'play':
        PlayVideo(params.get('video_id', ''), params.get('video_name', ''))
    else:
        # Default to language menu (main entry point)
        ShowLanguages()
