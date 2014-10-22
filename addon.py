import os
import sys
import urllib2
import json
import xml.etree.ElementTree as ET
import xbmc
import xbmcaddon
import xbmcgui

__addon__ = xbmcaddon.Addon("script.tvdbrating")
__addonpath__ = __addon__.getAddonInfo('path').decode('utf-8')
sys.path.append(os.path.join(__addonpath__, "resources/lib/tvdb_api"))
sys.path.append(os.path.join(__addonpath__, "resources/lib/tvdb_login"))
import tvdb_api
import tvdbauthenticate

accountName = ""
accountID = ""
try:
    path = __addonpath__ + '/resources/tvdb_account_settings.xml'
    tree = ET.parse(path)
    root = tree.getroot()
    itemList = root.findall('accountName')
    if len(itemList) != 0:
        accountName = itemList[0].text
    itemList = root.findall('accountID')
    if len(itemList) != 0:
        accountID = itemList[0].text
except IOError:
    # Create new xml file
    root = ET.Element("data")
    acname = ET.SubElement(root, "accountName")
    acname.text = "temp"
    accID = ET.SubElement(root, "accountID")
    accID.text = "temp"
    tree = ET.ElementTree(root)
    path = __addonpath__ + '/resources/tvdb_account_settings.xml'
    tree.write(path)


class myPlayer(xbmc.Player):

    def __init__(self, *args):
        self.loadAddonSettings()
        self.rating_url = "http://thetvdb.com/api/User_Rating.php?accountid="
        self.tvdb = tvdb_api.Tvdb(apikey='0F7BE09C80105D50')

    def loadAddonSettings(self):
        self.shouldOperate = True
        self.percentage_limit = int(__addon__.getSetting("percentage_limit"))
        self.display_past_rating = str(__addon__.getSetting("get_previous"))
        self.allow_past_rating = __addon__.getSetting("rate_if_previous")
        tvdb_username = __addon__.getSetting("tvdb_username")
        tvdb_password = __addon__.getSetting("tvdb_password")
        self.tvdb_authenticate = tvdbauthenticate.TVDB(tvdb_username, tvdb_password)
        icon = __addonpath__ + "/icon.png"
        if (tvdb_username == ""):
            xbmc.executebuiltin('Notification(TVDB Rating,No username given!,5000, %s)' % icon)
            self.shouldOperate = False
        elif (tvdb_password == ""):
            xbmc.executebuiltin('Notification(TVDB Rating,No password given!,5000, %s)' % icon)
            self.shouldOperate = False

        if (accountName != tvdb_username or accountID != ""):
            try:
                self.account_id = self.tvdb_authenticate.get_user_id()
            except:
                xbmc.executebuiltin('Notification(TVDB Rating,Unable to get user account id check account details,8000, %s)' % icon)
                self.shouldOperate = False
        else:
            self.account_id = accountID

        itemList = root.findall('accountName')
        if len(itemList) != 0:
            itemList[0].text = tvdb_username
        itemList = root.findall('accountID')
        if len(itemList) != 0:
            itemList[0].text = self.account_id
        tree = ET.ElementTree(root)
        path = __addonpath__ + '/resources/tvdb_account_settings.xml'
        tree.write(path)



    def onPlayBackStarted(self):
        self.isTvShow = False
        if xbmc.Player().isPlayingVideo():
            self.total_time = xbmc.Player().getTotalTime()
            result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "season", "episode", "showtitle"], "playerid": 1 }, "id": "VideoGetItem"}')
            data = json.loads(result)
            video_type = data['result']['item']['type']
            if (video_type == 'episode'):
                self.show_name = data['result']['item']['showtitle']
                self.episode_title = data['result']['item']['title']
                self.episode = data['result']['item']['episode']
                self.season = data['result']['item']['season']
                self.isTvShow = True
                self.getItemInfo()

    def onPlayBackStopped(self):
        if not self.shouldOperate:
            return
        if (((current_time / self.total_time) * 100 > self.percentage_limit) and self.isTvShow):
            self.rateItem()

    def onPlayBackEnded(self):
        if not self.shouldOperate:
            return
        if (self.isTvShow):
            self.rateItem()

    def getItemInfo(self):
        episode_data = self.tvdb[self.show_name][self.season][self.episode]
        self.item_id = episode_data['id']
        if (self.display_past_rating == "true"):
            episode_url = "http://thetvdb.com/?tab=episode&seriesid=" + episode_data['seriesid'] + "&seasonid=" + episode_data['seasonid'] + "&id=" + episode_data['id']
            self.previous_rating = self.tvdb_authenticate.get_user_rating(episode_url)
            self.was_rated = True
            if (self.previous_rating == -1):
                self.was_rated = False

    def rateItem(self):
        if (self.was_rated and self.allow_past_rating == "false"):
            return
        dialog = xbmcgui.Dialog()
        season = self.season
        episode = self.episode
        if (season < 10):
            season = "0" + str(season)
        if (episode < 10):
            episode = "0" + str(episode)
        item_name = self.show_name + " - " + "S" + str(season) + "E" + str(episode) + " - " + "'" + self.episode_title +"'"
        if (self.display_past_rating == "true" and self.was_rated):
            rating = dialog.select('%s\n Previous rating: %s' % (item_name, self.previous_rating), ['No rating (clears previous)', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        else:
            rating = dialog.select('Select a rating for:\n%s' % item_name, ['No rating', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
            url = str(self.rating_url + self.account_id + "&itemtype=episode&itemid=" + self.item_id + "&rating=" + str(rating))
            req = urllib2.Request(url)
            urllib2.urlopen(req)


class myMonitor(xbmc.Monitor):

    def __init__(self, *args):
        pass

    def onSettingsChanged(self):
        player.loadAddonSettings()


player = myPlayer()
monitor = myMonitor()

while (not xbmc.abortRequested):
    if xbmc.Player().isPlayingVideo():
        global current_time
        current_time = xbmc.Player().getTime()
    xbmc.sleep(100)
