from datetime import datetime

TITLE       = 'USTVnow'
PREFIX      = '/video/ustvnow'
ART         = 'art-default.jpeg'
ICON        = 'icon-default.png'
ICON_PREFS  = 'icon-prefs.png'
XPATHS      = {'Live'       : "//div[contains(@class, 'livetv-content-pages')]",
               'Favorites'  : "//div[contains(@class, 'livetv-content-pages')]",
               'Recordings' : "//div[contains(@class, 'reccontentpage')]"}

BASE_URL         = 'http://m.ustvnow.com'
GUIDE            = 'http://www.ustvnow.com?a=do_login&force_redirect=1&manage_proper=1&input_username=%s&input_password=%s'
RECORD_PROGRAM   = 'http://www.ustvnow.com/recordprogram.php?id=%s&token=%s'
DELETE_RECORDING = 'http://www.ustvnow.com/recordprogram.php?delete=%s&token=%s'
LOGIN_URL        = BASE_URL + '/iphone/1/live/login?username=%s&password=%s'
LIVETV           = BASE_URL + '/iphone/1/live/playingnow?pgonly=true&token=%s'
RECORDINGS       = BASE_URL + '/iphone/1/dvr/viewdvrlist?pgonly=true&token=%s'
FAVORITES        = BASE_URL + '/iphone/1/live/showfavs?pgonly=true&token=%s'
ADD_FAVORITE     = BASE_URL + '/iphone/1/live/updatefavs?prgsvcid=%s&token=%s&action=add'

####################################################################################################
def FormatDate(date):
    times = date.split('-')
    start = datetime.strptime(times[0], "%H:%M%p").strftime("%I:%M%p")
    end = datetime.strptime(times[1], "%H:%M%p").strftime("%I:%M%p")
    return start + '-' + end

def GetURL(network):
    page = HTML.ElementFromURL(LIVETV % (Dict['token']), cacheTime=0)
    node = page.xpath("//h1[contains(., '" + network + "')]/../..")
    href = node[0].xpath(".//a[contains(@class, 'viewlink')]")
    if len(href) > 0:
        return href[0].get('href')
    else:
        return None

def URLEncode(title, summary, network):
    if title is None:
        title = ''
    if summary is None:
        summary = ''
    if network is None:
        network = ''
    return '#' + String.Encode(summary.strip() + '::' + title + '::' + network)

####################################################################################################
def Start():
    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)

####################################################################################################
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu(view_group='InfoList'):
    Login()
    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(GetItems, title='All Channels', url=LIVETV, xp=XPATHS['Live']), title = 'All Channels'))
    oc.add(DirectoryObject(key = Callback(GetItems, title='My Favorites', url=FAVORITES, xp=XPATHS['Favorites']), title = 'My Favorites'))
    oc.add(DirectoryObject(key = Callback(GetItems, title='My Recordings', url=RECORDINGS, xp=XPATHS['Recordings']), title = 'My Recordings'))
    oc.add(DirectoryObject(key = Callback(GetGuide), title='Channel Guide'))
    oc.add(PrefsObject(title = 'Preferences', thumb = R(ICON_PREFS)))
    return oc

####################################################################################################
@route(PREFIX + '/getitems')
def GetItems(title, url, xp):
    oc = ObjectContainer(title2=title)
    page = HTML.ElementFromURL(url % (Dict['token']), cacheTime=0)
    items = page.xpath(xp)
    for item in items:
        url = item.xpath('.//a[@class="viewlink"]')
        if len(url) > 0:
            name = item.xpath('.//h1')[0].text
            url = BASE_URL + url[0].get("href")
            title = item.xpath('.//td[@class="nowplaying_item"]')[0].text
            summary = item.xpath("//a[contains(@href, '#" + item.get('id') + "')]/..//td[@class='nowplaying_desc']")
            if len(summary) > 0 and len(summary[0].text_content()) > 0:
                summary = summary[0].text_content()
            else:
                summary = 'No description available'
            encoded_data = URLEncode(title, summary, name)
            oc.add(VideoClipObject(
                url = url + encoded_data,
                title = name + " - " + String.DecodeHTMLEntities(title),
                summary = String.DecodeHTMLEntities(summary.strip()),
                thumb = R(name + '.jpg')
            ))
    if len(oc) == 0:
        return ObjectContainer(title2=title, header=title, message='None Found')
    else:
        return oc

####################################################################################################
@route(PREFIX + '/getguide')
def GetGuide():
    n = 0
    name = ""
    oc = ObjectContainer(title2='Guide')
    page = HTML.ElementFromURL(GUIDE % (Prefs["username"], Prefs["password"]), cacheTime=0)
    channels = page.xpath('//td[contains(@class, "chnl")]')
    for channel in channels:
        show_info = []
        
        shows = channel.xpath('following-sibling::td//td[@title]')
        for show in shows:
            content = show.xpath('.//div[contains(@class, "cntnt")]')[0]
            href = content.xpath('.//a')[0]
            desc = content.xpath('.//div')[0].text
            if desc is None:
                desc = 'No description available'

            rec_id = content.xpath('.//a[contains(@title, "Record Program")]')
            if len(rec_id) > 0:
                rec_id = rec_id[0].get('onclick').split("javascript:recordProgram('")[1].split('\'')[0]
            else:
                rec_id = ''

            del_id = content.xpath('.//a[contains(@title, "Delete Marked Recording")]')
            if len(del_id) > 0:
                del_id = del_id[0].get('onclick').split("javascript:deleteProgram('")[1].split('\'')[0]
            else:
                del_id = ''

            fav_id = content.xpath('.//a[contains(@class, "play")]')
            if len(fav_id) > 0:                
                playVideo = fav_id[0].get('onclick').split('playVideo("')
                if len(playVideo) > 1:                    
                    fav_id = playVideo[1].split('_')[0]
                else:
                    fav_id = ''
           

            show_info.append({
                'channel': href.get('title').split('Watch ')[1],
                'time': FormatDate(show.get('title')),
                'title': href.text,
                'desc': desc,
                'rec_id': rec_id,
                'del_id': del_id,
                'fav_id': fav_id
                }
            )
        show_info = JSON.StringFromObject(show_info)
        name = page.xpath(".//a[@class='play']/strong")[n].text
        oc.add(DirectoryObject(key = Callback(GuideSubMenu, title=name, data=String.Encode(show_info)), title=name, thumb=R(name + '.jpg')))
        if name != "...": n = n + 1
      	else: n = n + 2
      	if n == 28: n = 27  
    return oc

####################################################################################################
@route(PREFIX + '/guidesubmenu')
def GuideSubMenu(title, data):
    oc = ObjectContainer(title2=title)
    shows = JSON.ObjectFromString(String.Decode(data))
    for show in shows:
        title = show['time'] + ' - ' + show['title']
        ids = show['rec_id'] + '||' + show['del_id'] + '||' + show['fav_id']
        oc.add(DirectoryObject(key = Callback(ChannelOptions, title=show['title'], summary=show['desc'], network=show['channel'], ids=ids), title=title, summary=show['desc']))
    return oc

####################################################################################################
@route(PREFIX + '/channeloptions')
def ChannelOptions(title, summary, network, ids):
    oc = ObjectContainer(title2='Options for ' + title)
    url = GetURL(network)
    rec_id, del_id, fav_id = ids.split('||')
    encoded_data = URLEncode(title, summary, network)
    if url is not None:
        oc.add(VideoClipObject(
            url = BASE_URL + url + encoded_data,
            title = 'Watch ' + title,
            summary = summary,
            thumb = R(network + ".jpg")
        ))
        if rec_id is not '':
            oc.add(DirectoryObject(key = Callback(RecordMenu, type='Record', id=rec_id), title='Record'))
        if del_id is not '':
            oc.add(DirectoryObject(key = Callback(RecordMenu, type='Delete', id=del_id), title='Delete'))
        if fav_id is not '':
            oc.add(DirectoryObject(key = Callback(FavoriteMenu, id=fav_id), title='Add to Favorites'))
    else:
        return ObjectContainer(header=network, message='You must be a paid subscriber to view these options')
    return oc

####################################################################################################
@route(PREFIX + '/recordmenu')
def RecordMenu(type, id):
    if type == 'Record':
        data = HTTP.Request(RECORD_PROGRAM % (id, Dict['token']), cacheTime=0)
    else:
        data = HTTP.Request(DELETE_RECORDING % (id, Dict['token']), cacheTime=0)
    return ObjectContainer(title2=type, header=type, message=data.content)

####################################################################################################
@route(PREFIX + '/favoritemenu')
def FavoriteMenu(id):
    data = XML.ElementFromURL(ADD_FAVORITE % (id, Dict['token']), cacheTime=0)
    return ObjectContainer(title2='Add to Favorites', header='Favorites', message='Favorite added successfully')

####################################################################################################
def Login():
    Dict['token'] = ""
    username = Prefs["username"]
    password = Prefs["password"]
    if (username != None) and (password != None):
        x = HTTP.Request(LOGIN_URL % (username, password), cacheTime=0).content
        for cookie in HTTP.CookiesForURL(BASE_URL).split(';'):
            if 'token' in cookie:
                Dict['token'] = cookie.split("=")[1]
                return True
    return False
