import requests
import cookielib
from bs4 import BeautifulSoup
import re
import logging
from requests.exceptions import ConnectionError



# TODO: Allow setting for number of retries on operations e.g number of times to retry getting account id
class TVDB(object):
    jar = None


    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.session()
        logging.basicConfig(filename='tvdbauthenticate.log', level=logging.DEBUG)


    def authenticate(self):
        auth_url = "http://thetvdb.com/index.php?tab=login"

        header = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        form_data = {
            'username': self.username,
            'password': self.password,
            'function': 'Log In',
            'submit': 'Log In',
            'setcookie': 'on'
        }

        # Create CookieJar
        self.jar = cookielib.CookieJar()

        # Authenticate
        try:
            response = self.session.post(auth_url, data=form_data, headers=header, cookies=self.jar)
        except ConnectionError:
            # Couldn't reach tvdb
            raise FailedAuthenticationError()
        if (response.status_code != 200):
            # Something went wrong
            logging.error("Failed to authenticate")
            raise FailedAuthenticationError()

        successful = False
        for cookie in response.cookies:
            if (cookie.name == "cookieid" or cookie.name == "cookiepass"):
                # Authentication was successful
                successful = True
                logging.debug("Successfully authenticated")
                break

        if (not(successful)):
            logging.error("Failed to authenticate")
            # Throw exception
            raise FailedAuthenticationError()


    # TODO: must handle invalid urls (catch exceptions ?)
    def get_user_rating(self, url):
        logging.debug("Attempting to get rating with URL: " + url)
        # Check if we have authenticated
        if (self.jar is None):
            # Haven't authenticated, should do it
            self.authenticate()

        rating = None

        # Attempt to parse TVDB page for user's rating
        try:
            response = self.session.get(url, cookies=self.jar)
        except ConnectionError:
            # Couldn't reach tvdb, return -1
            return -1
        soup = BeautifulSoup(response.text)
        
        link = soup.find('a', onmouseout=True)
        pattern = re.compile('([A-Za-z]*\()([0-9])(\))')
        
        try:
            match = pattern.match(str(link['onmouseout']))
            rating = match.group(2)
        except:
            pass

        # Return result
        if (rating is None):
            logging.error("Unable to get rating")
            return -1
        else:
            logging.debug("Got rating: " + rating)
            return int(rating)


    def get_user_id(self):
        account_url = "http://thetvdb.com/?tab=userinfo"
        logging.debug("Attempting to get user account id")
        # Check if we have authenticated
        if (self.jar is None):
            # Haven't authenticated, should do it
            self.authenticate()

        account_id = None

        # Attempt to parse user's account page to get their id
        try:
            response = self.session.get(account_url, cookies=self.jar)
        except ConnectionError:
            raise GetAccountIDFailedError()
        soup = BeautifulSoup(response.text)
        pattern = re.compile('(<input name="form_uniqueid" readonly="" type="text" value=")(\w+)(".*)')

        for link in soup.find_all('input'):
            try:
                match = pattern.match(str(link))
                account_id = match.group(2)
                break
            except:
                pass

        if (account_id == None):
            # Couldn't get id
            logging.error("Couldn't get user account id")
            return -1
        else:
            logging.debug("Successfully got id: " + account_id)
            return account_id
        
        
    def rate_item(self, account_id, item_id, rating):
        id_length = len(account_id)
        if (not(account_id.isalnum()) or id_length < 16 or id_length > 32):
            raise FailedRatingError()
        elif ((rating < 0) or (rating > 10)):
            raise FailedRatingError()
        
        url = "http://thetvdb.com/api/User_Rating.php?accountid=%s&itemtype=episode&itemid=%s&rating=%s" % (account_id, item_id, rating)
        try:
            response = self.session.post(url)
        except ConnectionError:
            raise FailedRatingError()
        if "failed" in response.text:
            raise FailedRatingError()
    
    

class FailedAuthenticationError(Exception):

    def __init__(self):
        super(FailedAuthenticationError, self).__init__()
        
        
        
class FailedRatingError(Exception):
    def __init__(self):
        super(FailedRatingError, self).__init__()
        
        
        
class GetAccountIDFailedError(Exception):
    def __init__(self):
        super(FailedRatingError, self).__init__()
        