"""
Little script which pulls down all your wall posts and likes from your facebook wall and inserts them into a MySQL database
"""
import facebook
from bishared import job_utils
from datetime import datetime
import requests
import sys


class DBConnection(object):
    """
    DB class for connecting to a MySQL database
    """

    def __init__(self, config, section):
        """
        Instantiate the class
        :param config: config file to read our connection details from
        :param section: section of config file
        """
        self.config = config
        self.section = section

    def get_connection(self):
        """
        method for getting an open connection to the DB
        :return: db connection
        """
        conn = job_utils.WarehouseConnectionManager(self.config, self.section)
        return conn

    def create_table(self):
        """
        method which creates our table for us to insert into
        """
        sql = \
        """
        create table if not exists fb_posts
        (created_datetime datetime,
        post varchar(100),
        likes int)
        """
        self.get_connection().execute(sql)
        return None


class FacebookConnect(DBConnection):

    token = 'CAACEdEose0cBALeKVKZCypaadNx18ePBiaM6ZCM77y0ArPqoX8NsLr7HsPBwDwCQQeqzmO8YHfCMZCFZAhd4CjYQr8qp0ySyT1Iqg25ZAC0uzrqlLxGvu4crOAHSLeNUbPnFP2Y64W4vbHYGJjrqcXzUYs2fMwR7mxHXZAQTZCOSnSutiyE9IeMaZCGtrvRyG8GG6ovlqR2np7g6W7KKqySLOaWmyE49PZCgZD'

    def __init__(self, access_token):
        """
        Instantiate the class
        :param access_token: token used to connect to the GraphAPI
        """
        self.token = access_token

        super(FacebookConnect, self).__init__('facebook.conf', 'test')

    def connect(self):
        """
        connects to facebook via the GraphAPI
        :return: facebook connection
        """
        conn = facebook.GraphAPI(access_token=self.token)
        return conn

    def get_posts(self):
        """
        gets all the recent facebook wall posts which the user has posted as well as the URL for the next set of posts
        :return: list consisting of [post_data, URL]
        """
        posts = self.connect().get_connections("me", "posts")
        post_data = posts['data']
        url = posts['paging']['next']
        return post_data, url

    @classmethod
    def get_previous_posts(cls, url):
        """
        method which gets a json response object (posts) from which we get our data and our URL for the subsequent iterations
        :return: list consisting of [post_data, URL]
        """
        posts = requests.get(url).json()
        global url_string, data
        try:
            data = posts['data']
        except KeyError, e:
            print e
        try:
            url_string = posts['paging']['next']

        except KeyError, e:
            print "Key Error {}".format(e)
            sys.exit("Failed to find relevant key. Exiting Script...")
        return data, url_string

    def get_insert_info(self, post_data):
        """
        now we loop through our post data to extract the bits we are after to insert into our database...
        :return: get a list of [created_time, facebook_post, likes]
        """
        insert_list = []
        for posts in post_data[0]:
            date = datetime.strptime(str(posts['created_time'][0:10]), '%Y-%m-%d')
            try:
                ## check if an actual message was posted rather than a check-in / story
                message = posts['message']
            except KeyError, e:
                message = 'None'
            try:
                ## check if anyone actually "liked" my post
                likes = len(posts['likes']['data'])
            except KeyError, e:
                likes = 0
            finally:
                insert_list.append((date, message, likes))
        self.get_connection().execute_many("""insert ignore into fb_posts values (%s, %s, %s)""", insert_list)
        self.get_insert_info(self.get_previous_posts(post_data[1]))

    def execute(self):
        """
        main entry point to execute the script
        """
        self.create_table()
        self.get_insert_info(self.get_posts())

if __name__ == '__main__':
    FacebookConnect(access_token=FacebookConnect.token).execute()