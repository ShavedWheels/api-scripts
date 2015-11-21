"""
Little script which pulls down your time-line tweets along with how many people have marked it as a favourite and 
the datetime it was posted
"""
import time
import twitter
from bishared import job_utils
from ConfigParser import SafeConfigParser
import os


class Twitter(object):
    """
    class which uses the Twitter API to get previous twitter posts
    """
    def __init__(self, config_file, config_section):
        """
        Insantiate the class
        :param config_file: config file to use
        :param config_section: section of config file
        """
        self.config_file = config_file
        self.config_section = config_section

    @classmethod
    def raw_config_input(cls):
        """
        method which creates a config file (if one is not present) and requires raw input from the user to fill in
        """
        config_file = 'twitter.conf'
        with open(config_file, 'w') as conf:
            conf.write("[twitter]\n"
                       "consumer_key={consumer_key}\n"
                       "consumer_secret={consumer_secret}\n"
                       "access_token={access_token}\n"
                       "token_secret={token_secret}".format(consumer_key=raw_input("Enter consumer key: "),
                                                            consumer_secret=raw_input("Enter consumer secret: "),
                                                            access_token=raw_input("Enter access token: "),
                                                            token_secret=raw_input("Enter token secreet: ")))
            conf.close()

    def get_details(self):
        """
        method which retrieves our details from the config file.
        :return: config details as dict
        """

        config_file = '\\twitter.conf'
        config_file = os.getcwd() + config_file
        if not os.path.isfile(config_file):
            self.raw_config_input()
            config = SafeConfigParser()
            config.read(self.config_file)
            details = dict(config.items(self.config_section))
            return details
        else:
            config = SafeConfigParser()
            config.read(self.config_file)
            details = dict(config.items(self.config_section))
            return details

    def connect(self):
        """
        Instantiates the Twitter API object
        :return: Twitter connection
        """
        conn = twitter.Api(consumer_key=self.get_details()['consumer_key'],
                           consumer_secret=self.get_details()['consumer_secret'],
                           access_token_key=self.get_details()['access_token'],
                           access_token_secret=self.get_details()['token_secret'])

        return conn

    @classmethod
    def format_dates(cls, data):
        """
        method which re-formats the date given by twitter
        :return: data to insert into our table
        """
        data = list(data)
        data[0] = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(data[0], '%a %b %d %H:%M:%S +0000 %Y'))
        return data

    def get_tweets(self):
        """
        method which pulls down the most recent 200 tweets from your time-line along
        with the datetime it was posted and the amount of favourites it received
        """
        insert = []
        tweets = self.connect().GetUserTimeline(count=200)
        for tweet in tweets:
            insert.append((tweet.created_at, tweet.text, tweet.favorite_count))
        mapped = map(self.format_dates, insert)
        return mapped


class DBConnection(object):
    """
    class which connects to a MySQL database
    """
    def __init__(self, config_file, config_section):
        """
        Instantiate the class
        :param config_file: config file to use
        :param config_section: section of config file
        """
        self.config_file = config_file
        self.section = config_section

    def get_connection(self):
        """
        method which gets an open connection connection to the database
        :return: connection
        """
        conn = job_utils.WarehouseConnectionManager(self.config_file, self.section)
        return conn


    def create_table(self):
        """
        creates a table(if it doesn't exist already) for us to insert our twitter data
        """
        sql = \
            """create table if not exists twitter_posts
            (created_datetime datetime,
            tweet varchar(255),
            favourties int)"""
        self.get_connection().execute(sql)
        return None

    def insert_data(self, data):
        """
        inserts our twitter data into our table
        :param; twitter data for us to insert
        """
        self.create_table()
        sql = """insert into twitter_posts values(%s, %s, %s)"""
        self.get_connection().execute_many(sql, data)

if __name__ == '__main__':
    tweet_data = Twitter('twitter.conf', 'twitter').get_tweets()
    DBConnection('netl.conf', 'test').insert_data(tweet_data)
