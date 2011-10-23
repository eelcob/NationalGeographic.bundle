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
SECTION_URL = "http://video.nationalgeographic.com/video/player/data/xml/section_%s.xml"
VIDEO_CATEGORY_URL = "http://video.nationalgeographic.com/video/player/data/xml/category_%s.xml"
VIDEO_ASSETS_URL = "http://video.nationalgeographic.com/video/player/data/xml/category_assets_%s.xml"
CATEGORY_THUMBNAIL = "http://video.nationalgeographic.com/video/player/media/featured_categories/%s_102x68.jpg"
CATEGORYASSET_THUMBNAIL = "http://video.nationalgeographic.com/video/player/media/%s/%s_150x100.jpg"
VIDEO_URL = "http://video.nationalgeographic.com/video/cgi-bin/cdn-auth/cdn_tokenized_url.pl?slug=%s&siteid=popupmain"
VIDEO_THUMBNAIL = "http://video.nationalgeographic.com/video/player/media/%s/%s_480x360.jpg"

BASE_URL = "http://video.nationalgeographic.com"
JSON_CAT_URL = "http://video.nationalgeographic.com/video/player/data/mp4/json/main_sections.json"
JSON_CHANNEL_CAT_URL = "http://video.nationalgeographic.com/video/player/data/mp4/json/category_%s.json"
JSON_PLAYLIST_URL = "http://video.nationalgeographic.com/video/player/data/mp4/json/lineup_%s_%s.json"
JSON_VIDEO_URL = "http://video.nationalgeographic.com/video/player/data/mp4/json/video_%s.json"

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

    # Set the default ObjectContainer attributes
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = NAME
    ObjectContainer.view_group = "List"

    # Default icons for DirectoryObject and WebVideoItem
    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    # Set the default cache time
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16"

####################################################################################################
def VideosMainMenu():
    oc = ObjectContainer()

    # Iterate over all of the available categories and display them to the user.
    categories = JSON.ObjectFromURL(JSON_CAT_URL)
    for category in categories['sectionlist']['section']:
        name = category['label']
        oc.add(DirectoryObject(key = Callback(ChannelVideoCategory, id = category['id'], name = name), title = name))

    return oc

####################################################################################################
def ChannelVideoCategory(id, name):
    oc = ObjectContainer()

    # Iterate over all the subcategories. It's possible that we actually find another sub-sub-category
    # In this case, we will simply recursively call this function again until we find actual playlists.
    sub_categories = JSON.ObjectFromURL(JSON_CHANNEL_CAT_URL % id)
    for sub_category in sub_categories['section']['children']:
        name = sub_category['label']

        has_child = sub_category['hasChild']
        if has_child == "true":
            oc.add(DirectoryObject(key = Callback(ChannelVideoCategory, id = sub_category['id'], name = name), title = name))
        else:
            oc.add(DirectoryObject(key = Callback(ChannelVideoPlaylist, id = sub_category['id'], name = name), title = name))

    return oc

####################################################################################################
def ChannelVideoPlaylist(id, name, page = 0):
    oc = ObjectContainer(view_group="InfoList")

    # Iterate over all the available playlist and extract the available information.
    playlist = JSON.ObjectFromURL(JSON_PLAYLIST_URL % (id, str(page)))
    for video in playlist['lineup']['video']:
        name = video['title']
        summary = video['caption']

        duration_text = video['time']
        duration_dict = re.match("(?P<mins>[0-9]+):(?P<secs>[0-9]+)", duration_text).groupdict()
        mins = int(duration_dict['mins'])
        secs = int(duration_dict['secs'])
        duration = ((mins * 60) + secs) * 1000

        # In order to obtain the actual url, we need to call the specific JSON page. This will also
        # include the 
        video_details = JSON.ObjectFromURL(JSON_VIDEO_URL % video['id'])
        url = BASE_URL + video_details['video']['url']
        thumb = video_details['video']['still']
        
        oc.add(VideoClipObject(
            url = url, 
            title = name, 
            summary = String.StripTags(summary.strip()), 
            thumb = thumb,
            duration = duration))

    return oc

####################################################################################################
def PhotosMainMenu():
    # Photo's main menu currently just listing Photo's of the Day.
    # This section heavily inspired by FeedMe plugin

    oc = ObjectContainer()
    return oc
