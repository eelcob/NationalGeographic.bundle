import re

####################################################################################################

PHOTOS_PREFIX = "/photos/nationalgeographic"
VIDEO_PREFIX = "/video/nationalgeographic"

NAMESPACES = {'media':'http://search.yahoo.com/mrss/', 'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd', "itunesB":"http://www.itunes.com/DTDs/Podcast-1.0.dtd"}
POD_FEED = "http://feeds.nationalgeographic.com/ng/photography/photo-of-the-day/"

# Video urls
CHANNEL_ROOT = "http://channel.nationalgeographic.com/channel/videos/feeds/cv/us/"
CHANNEL_CAT_URL = "player_0000059.xml"
CHANNEL_VIDEO_URL = "http://channel.nationalgeographic.com/channel/videos/player.html?channel=%s&category=%s&title=%s"
VIDEO_SECTIONS = "http://video.nationalgeographic.com/video/player/data/xml/sectionlist.xml"
SECTION_URL = "http://video.nationalgeographic.com/video/player/data/xml/section_%s.xml"
VIDEO_CATEGORY_URL = "http://video.nationalgeographic.com/video/player/data/xml/category_%s.xml"
VIDEO_ASSETS_URL = "http://video.nationalgeographic.com/video/player/data/xml/category_assets_%s.xml"
CATEGORY_THUMBNAIL = "http://video.nationalgeographic.com/video/player/media/featured_categories/%s_102x68.jpg"
CATEGORYASSET_THUMBNAIL = "http://video.nationalgeographic.com/video/player/media/%s/%s_150x100.jpg"
VIDEO_URL = "http://video.nationalgeographic.com/video/cgi-bin/cdn-auth/cdn_tokenized_url.pl?slug=%s&siteid=popupmain"
VIDEO_THUMBNAIL = "http://video.nationalgeographic.com/video/player/media/%s/%s_480x360.jpg"

NAME = L('Title')

# Default artwork and icon(s)
ART           = 'art-default.jpg'
ICON          = 'icon-default.png'
NEXT          = 'icon-more.png'

####################################################################################################
def Start():
    Plugin.AddPrefixHandler(PHOTOS_PREFIX, PhotosMainMenu, L('PhotosTitle'), ICON, ART)
    Plugin.AddPrefixHandler(VIDEO_PREFIX, VideosMainMenu, L('VideoTitle'), ICON, ART)

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    # Set the default MediaContainer attributes
    MediaContainer.art = R(ART)
    MediaContainer.title1 = NAME
    MediaContainer.viewGroup = "InfoList"

    # Default icons for DirectoryItem and WebVideoItem
    DirectoryItem.thumb = R(ICON)
    WebVideoItem.thumb = R(ICON)

    # Set the default cache time
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10"

####################################################################################################
def VideosMainMenu():
    Log(CHANNEL_ROOT + CHANNEL_CAT_URL)
    # Videos main menu
    #
    # This is a port of the NG plugin for XBMC by stacked.xbmc
    # http://code.google.com/u/stacked.xbmc/ and http://code.google.com/p/plugin/downloads/list

    dir = MediaContainer(viewGroup="List")

    for category in XML.ElementFromURL(CHANNEL_ROOT+CHANNEL_CAT_URL, errors='ignore').xpath('//category'):
        name = category.xpath('./name')[0].text
        name = clean(name)
        url = category.xpath('./datafile')[0].text
        thumbnail = category.xpath('./thumbnail')[0].text
        id = category.xpath('./id')[0].text
        dir.Append(Function(DirectoryItem(ChannelVideoCategory, title=name, thumb=Function(GetThumb, url=thumbnail)), url=url, channel=id))

    return dir

####################################################################################################
def PhotosMainMenu():
    # Photo's main menu currently just listing Photo's of the Day.
    # This section heavily inspired by FeedMe plugin

    dir = MediaContainer()

    for item in XML.ElementFromURL(POD_FEED, errors='ignore').xpath('//item'):
        title = item.xpath('./title')[0].text

        subtitle = None
        if len(item.xpath('./pubDate')) > 0:
            subtitle = Datetime.ParseDate(item.xpath('./pubDate')[0].text).strftime('%a %b %d, %Y')

        description = ItemDescription(item)

        # Finds the url and switches to higher resolution image
        media = None
        content = item.xpath('.//media:content', namespaces=NAMESPACES)
        if len(content) > 0:
            media = content[0].get('url')
            media = media.replace('360x270','990x742')

        if media == None:
            enclosures = item.xpath('./enclosure')
            if len(enclosures) > 0:
                media = enclosures[0].get('url')
                media = media.replace('360x270','990x742')

        if media != None:
            dir.Append(PhotoItem(media, title=title, subtitle=subtitle, summary=description, thumb=Function(GetThumb, url=media)))

    return dir

####################################################################################################
def ChannelVideoCategory(sender, url, channel):
    # Channel Video Category

    dir = MediaContainer(viewGroup="List", title2=sender.itemTitle)

    myurl = CHANNEL_ROOT+url
    for playlist in XML.ElementFromURL(myurl, errors='ignore').xpath('//playlist'):
        name = playlist.xpath('./name')[0].text
        url  = playlist.xpath('./datafile')[0].text
        id   = playlist.xpath('./id')[0].text
        dir.Append(Function(DirectoryItem(ChannelVideoPlaylist, title=name), title=name, url=url, channel=channel, category=id, page=1))

    return dir

####################################################################################################
def ChannelVideoPlaylist(sender, title, url, channel, category, page):
    # Channel Video Category

    dir = MediaContainer(title2=sender.itemTitle)

    myurl = CHANNEL_ROOT+url
    videos = XML.ElementFromURL(myurl, errors='ignore').xpath('//videos')[0]
    videoCount = int(videos.xpath('./videoCount')[0].text)
    pageCount  = int(videos.xpath('./pageCount')[0].text)
    prefix = videos.xpath('./prefixSortByDate')[0].text

    if (videoCount == 0):
        return MessageContainer(title, "No videos available")
    else:
        myurl = CHANNEL_ROOT+prefix+str(page)+'.xml'
        for video in XML.ElementFromURL(myurl, errors='ignore', cacheTime=CACHE_1WEEK).xpath('//video'):
            name    = clean(video.xpath('./shortTitle')[0].text)
            thisurl = video.xpath('./datafile')[0].text

            thisVideo = XML.ElementFromURL(thisurl, errors='ignore')
            video_title    = thisVideo.xpath('./shortTitle')[0].text
            subtitle = thisVideo.xpath('./longTitle')[0].text
            video    = thisVideo.xpath('./video')[0].text
            titleid  = thisVideo.xpath('./id')[0].text

            try:
                summary = thisVideo.xpath('./longDescription')[0].text
            except:
                try:
                    summary = thisVideo.xpath('./shortDescription')[0].text
                except:
                    summary = ''

            try:
                episode = thisVideo.xpath('./episodeTitle')[0].text
            except:
                episode = None

            try:
                rating = thisVideo.xpath('./rating')[0].text
            except:
                rating = None

            try:
                thumb = thisVideo.xpath('./still')[0].text
            except:
                try:
                    thumb = thisVideo.xpath('./thumbnail')[0].text
                except:
                    thumb = None

            longsummary = ''
            if episode != None:
                longsummary = longsummary+episode+"\n"
            if rating != None:
                longsummary = longsummary+"Rating: "+rating
            if (len(longsummary) > 0):
                longsummary = longsummary+"\n\n"
            longsummary = longsummary + summary

            dir.Append(Function(WebVideoItem(PlayVideo, title=video_title, subtitle=subtitle, summary=longsummary, thumb=Function(GetThumb, url=thumb)), url=video))

            #videourl = CHANNEL_VIDEO_URL % (channel, category, titleid)
            #Log(videourl,debugOnly=False)
            #dir.Append(WebVideoItem(videourl, title=title, subtitle=subtitle, summary=longsummary, thumb=Function(GetThumb, url=thumb)))

        if (page < pageCount):
            page = page+1
            nextpage = "Next page ("+str(page)+" of "+str(pageCount)+")"
            dir.Append(Function(DirectoryItem(ChannelVideoPlaylist, title=nextpage, thumb=R(NEXT)), title=title, url=url, channel=channel, category=category, page=page))

    return dir

####################################################################################################
def VideoSection(sender,url):
    # Video Section

    dir = MediaContainer(viewGroup="List", title2=sender.itemTitle)

    # Added by sander1 to prevent errors encountered with at least 1 XML file that contained an unencoded ampersand
    content = HTTP.Request(url).content
    content = re.sub('&(?!#)(?!amp;)', '&amp;', content)

    for category in XML.ElementFromString(content).xpath('//children/category'):
        name = clean(category.xpath('./name')[0].text)
        categoryid = category.get('id')
        thumb = CATEGORY_THUMBNAIL % categoryid
        if(category.xpath('./hasVideo')[0].text == 'true'):
            url2 = VIDEO_ASSETS_URL % categoryid
            dir.Append(Function(DirectoryItem(VideoAssets, title=name, thumb=Function(GetThumb, url=thumb)), url=url2))
        else:
            url2 = VIDEO_CATEGORY_URL % categoryid
            dir.Append(Function(DirectoryItem(VideoCategory, title=name, thumb=Function(GetThumb, url=thumb)), url=url2))

    return dir

####################################################################################################
def VideoCategory(sender, url):
    # Video child category

    dir = MediaContainer(viewGroup="List", title2=sender.itemTitle)

    # Added by sander1 to prevent errors encountered with at least 1 XML file that contained an unencoded ampersand
    content = HTTP.Request(url).content
    content = re.sub('&(?!#)(?!amp;)', '&amp;', content)

    for category in XML.ElementFromString(content).xpath('//children/category'):
        name = clean(category.xpath('./name')[0].text)
        categoryid = category.get('id')
        url2 = VIDEO_ASSETS_URL % categoryid
        thumb = CATEGORYASSET_THUMBNAIL % (categoryid, categoryid)
        dir.Append(Function(DirectoryItem(VideoAssets, title=name, thumb=Function(GetThumb, url=thumb)), url=url2))

    return dir

####################################################################################################
def VideoAssets(sender, url, page=0):
    # Video child category

    dir = MediaContainer(viewGroup="List", title2=sender.itemTitle)

    myurl = url
    if (page != 0):
        myurl = url.replace('.xml','_'+str(int(page))+'.xml')

    assets = XML.ElementFromURL(myurl, errors='ignore').xpath('//assetlist')
    totalpages = int(assets[0].get('totalpages'))
    pagesize = int(assets[0].get('pagesize'))

    i = 1
    for video in XML.ElementFromURL(myurl, errors='ignore').xpath('//videoasset'):
        refid = video.get('refid')
        title = clean(video.xpath('./title')[0].text)
        title = str(pagesize*page+i)+'.  '+title
        videoXmlUrl = VIDEO_URL % refid
        try:
            thumbnail = VIDEO_THUMBNAIL % (refid, refid)
        except:
            thumbnail = None
        dir.Append(Function(VideoItem(PlayProgressiveVideo, title=title, thumb=Function(GetThumb, url=thumbnail)), url=videoXmlUrl))
        i = i+1

    if ((page+1) < totalpages):
        page = page+1
        nextpage = "Next page ("+str(page+1)+" of "+str(totalpages)+")"
        dir.Append(Function(DirectoryItem(VideoAssets, title=nextpage, thumb=R(NEXT)), url=url, page=page))

    return dir

####################################################################################################
def clean(name):
    # Function cleans up HTML ascii stuff

    remove = [('&amp;','&'),('&quot;','"'),('&#233;','e'),('&#8212;',' - '),('&#39;','\''),('&#46;','.'),('&#58;',':')]
    for trash, crap in remove:
        name = name.replace(trash,crap)

    return name.strip()

####################################################################################################
def ItemDescription(item):
    # Function to pull item's description
    # From FeedMe plugin
    description = ""
    if len(item.xpath('./description')) > 0:
        description = item.xpath('./description')[0].text
    if description == None:
        description = ""
    description = String.StripTags(description.strip())
    
    return description

####################################################################################################
def PlayVideo(sender, url):
    flvconfig  = XML.ElementFromURL(url, errors='ignore', cacheTime=0) # cacheTime=0 to get a fresh (and working) authorization string for the Akamai streams every time
    serverName = flvconfig.xpath('./serverName')[0].text
    appName    = String.Quote(flvconfig.xpath('./appName')[0].text, usePlus=False)
    playPath   = String.Quote(flvconfig.xpath('./streamName')[0].text, usePlus=False)

    if (flvconfig.xpath('./isLive')[0].text == "true"):
        isLive = True
    else:
        isLive = False

    videourl = 'rtmp://'+serverName+'/'+appName
    Log(videourl)
    return Redirect( RTMPVideoItem( url=videourl, clip=playPath, live=bool(isLive) ) )

####################################################################################################
def PlayProgressiveVideo(sender, url):
    videourl = XML.ElementFromURL(url, errors='ignore', cacheTime=0).xpath('//tokenizedURL')[0].text
    videourl = clean(videourl)
    return Redirect(videourl)

####################################################################################################
def GetThumb(url):
    if url != None:
        try:
            data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
            return DataObject(data, 'image/jpeg')
        except:
            pass
    return Redirect( R(ICON) )
