import os
import sys
import json
import logging
import xbmc
import xbmcaddon
import xbmcgui


addon = xbmcaddon.Addon("script.tvdbrating")
addonpath = addon.getAddonInfo('path').decode('utf-8')
icon = addonpath + "/icon.png"
sys.path.append(os.path.join(addonpath, "resources/lib/tvdb_api"))
sys.path.append(os.path.join(addonpath, "resources/lib/tvdb_authenticate"))
import tvdb_api
from tvdb_authenticate import TVDB

logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s.%(msecs)d %(levelname)s %(module)s - %(funcName)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
logging.disable(logging.CRITICAL)# Comment this to enable logging


class myPlayer(xbmc.Player):

    def __init__(self, *args):
        logging.debug("Creating instance of xbmc.Player subclass")
        self.tvdb_username = ""
        self.tvdb_password = ""
        self.account_id = ""
        self.loadAddonSettings(True)
        self.rating_url = "http://thetvdb.com/api/User_Rating.php?accountid="
        self.tvdb = tvdb_api.Tvdb(apikey='0F7BE09C80105D50')


    def loadAddonSettings(self, isFirstRun):
        logging.debug("Loading settings of addon")
        self.shouldOperate = True
        self.percentage_limit = int(addon.getSetting("percentage_limit"))
        self.display_past_rating = str(addon.getSetting("get_previous"))
        self.allow_past_rating = addon.getSetting("rate_if_previous")
        username_from_settings = addon.getSetting("tvdb_username")
        password_from_settings = addon.getSetting("tvdb_password")

        accountDetailsChanged = False
        if (self.tvdb_username != username_from_settings):
            self.tvdb_username = username_from_settings
            accountDetailsChanged = True
        if (self.tvdb_password != password_from_settings):
            self.tvdb_password = password_from_settings
            accountDetailsChanged = True
        if (isFirstRun):
            accountDetailsChanged = False

        if (self.tvdb_username == ""):
            xbmc.executebuiltin('Notification(TVDB Rating,No username given!,5000, %s)' % icon)
            logging.debug("No username given in settings")
            self.shouldOperate = False
            return
        elif (self.tvdb_password == ""):
            xbmc.executebuiltin('Notification(TVDB Rating,No password given!,5000, %s)' % icon)
            logging.debug("No password given in settings")
            self.shouldOperate = False
            return

        self.tvdb_authenticate = TVDB(self.tvdb_username, self.tvdb_password)
        logging.debug("accountDetailsChanged = " + str(accountDetailsChanged))
        self.getAccountID(accountDetailsChanged)

        logging.debug("shouldOperate = " + str(self.shouldOperate))
        logging.debug("percentage_limit = " + str(self.percentage_limit))
        logging.debug("display_past_rating = " + self.display_past_rating)
        logging.debug("display_past_rating = " + self.display_past_rating)
        logging.debug("allow_past_rating = " + self.allow_past_rating)
        logging.debug("username_from_settings = " + username_from_settings)
        logging.debug("tvdb_username = " + self.tvdb_username)
        logging.debug("password_from_settings = " + password_from_settings)
        logging.debug("tvdb_password = " + self.tvdb_password)
        logging.debug("account_id = " + self.account_id )



    def getAccountID(self, shouldReGet):
        logging.debug("Getting account id")
        accountID = addon.getSetting('accountID')
        if (accountID == "" or shouldReGet):
            logging.debug("Connecting to tvdb to get account id")
            try:
                self.account_id = self.tvdb_authenticate.get_user_id()
                addon.setSetting(id='accountID', value=self.account_id)
                logging.debug("Got account id from tvdb successfully")
            except:
                logging.debug("Unable to get account id from tvdb")
                xbmc.executebuiltin('Notification(TVDB Rating,Unable to get user account id check account details,8000, %s)' % icon)
                self.shouldOperate = False
        else:
            logging.debug("Using account id from settings")
            self.account_id = accountID


    def onPlayBackStarted(self):
        logging.debug("Playback started")
        self.isTvShow = False
        if self.isPlayingVideo():
            logging.debug("Player is playing a video file")
            self.total_time = self.getTotalTime()
            logging.debug("Total time of item = " + str(self.total_time))
            result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetItem", "params": { "properties": ["title", "season", "episode", "showtitle"], "playerid": 1 }, "id": "VideoGetItem"}')
            data = json.loads(result)
            video_type = data['result']['item']['type']
            if (video_type == 'episode'):
                logging.debug("Item in player is a TV episode")
                self.show_name = data['result']['item']['showtitle']
                self.episode_title = data['result']['item']['title']
                self.episode = data['result']['item']['episode']
                self.season = data['result']['item']['season']
                self.isTvShow = True
                self.getItemInfo()
                logging.debug("show_name = " + str(self.show_name))
                logging.debug("episode_title = " + str(self.episode_title))
                logging.debug("episode number = " + str(self.episode))
                logging.debug("season number = " + str(self.season))


    def onPlayBackStopped(self):
        logging.debug("Playback stopped")
        logging.debug("Time position of mediaplayer = " + str(current_time))
        logging.debug("Total time of item that was playing = " + str(self.total_time))
        logging.debug("Percentage_limit from settings = " + str(self.percentage_limit))
        if not self.shouldOperate:
            return
        if (((current_time / self.total_time) * 100 > self.percentage_limit) and self.isTvShow):
            global current_time
            current_time = 0
            self.rateItem()


    def onPlayBackEnded(self):
        logging.debug("Playback ended")
        logging.debug("Time position of mediaplayer = " + str(current_time))
        logging.debug("Total time of item that was playing = " + str(self.total_time))
        logging.debug("Percentage_limit from settings = " + str(self.percentage_limit))
        if (self.isTvShow and self.shouldOperate):
            global current_time
            current_time = 0
            self.rateItem()


    def getItemInfo(self):
        logging.debug("Getting information of item in player")
        episode_data = self.tvdb[self.show_name][self.season][self.episode]
        self.item_id = episode_data['id']
        if (self.display_past_rating == "true"):
            episode_url = "http://thetvdb.com/?tab=episode&seriesid=" + episode_data['seriesid'] + "&seasonid=" + episode_data['seasonid'] + "&id=" + episode_data['id']
            self.previous_rating = self.tvdb_authenticate.get_user_rating(episode_url)
            self.was_rated = True
            if (self.previous_rating == -1):
                self.was_rated = False


    def rateItem(self):
        logging.debug("Rating item")
        if (self.was_rated and self.allow_past_rating == "false"):
            logging.debug("Item has been rated before by user, but 'allow_past_rating' is false")
            return
        dialog = xbmcgui.Dialog()
        season = self.season
        episode = self.episode
        if (season < 10):
            season = "0" + str(season)
        if (episode < 10):
            episode = "0" + str(episode)
        item_name = self.show_name + " - " + "S" + str(season) + "E" + str(episode) + " - " + "'" + self.episode_title +"'"
        logging.debug("Formatted name of item being rated = " + item_name)
        if (self.display_past_rating == "true" and self.was_rated):
            logging.debug("'display_past_rating' is true and item being rated has been rated by user before")
            rating = dialog.select('%s\n Previous rating: %s' % (item_name, self.previous_rating), ['No rating (clears previous)', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        else:
            logging.debug("'display_past_rating' is false, or user has not rated this item before")
            rating = dialog.select('Select a rating for:\n%s' % item_name, ['No rating', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
        
        logging.debug("Rating value selected = " + str(rating))
        if (rating >= 0 and rating <= 10):
            self.tvdb_authenticate.rate_item(self.account_id, self.item_id, rating)



class myMonitor(xbmc.Monitor):

    def __init__(self, *args):
        pass

    def onSettingsChanged(self):
        logging.debug("Settings changed")
        player.loadAddonSettings(False)


player = myPlayer()
monitor = myMonitor()

while (not xbmc.abortRequested):
    if xbmc.Player().isPlayingVideo():
        global current_time
        current_time = xbmc.Player().getTime()
    xbmc.sleep(100)

logging.debug("Abort requested, exiting...")
logging.debug("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")