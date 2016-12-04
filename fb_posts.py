"""
Little script which pulls down all your wall posts and likes from your facebook wall and inserts them into a MySQL database
"""
import facebook
from datetime import datetime
import requests
import sys
import os
import psycopg2
from ConfigParser import SafeConfigParser

TABLE_NAME = 'fb_posts'


CREATE_TABLE_SQL = \
"""
create table if not exists {table_name}
(created_date date,
object_id text unique,
story text,
message text,
likes int,
poster text,
post_type text,
status_type text,
latitude float,
longitude float,
place text)
""".format(table_name=TABLE_NAME)


INSERT_TEMPLATE = "insert into {table_name} ({columns}) values ({placement_holders}) on conflict do nothing"


class FacebookException(Exception):
    pass


class DatabaseException(Exception):
    pass


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

    def get_config_details(self):
        """
        Method which reads our config file
        :return: dictionary containing our connection details {user, passwd, host, db etc...}
        """
        config = SafeConfigParser()
        config.read(os.path.join(os.path.dirname(os.path.realpath(__file__)), self.config))
        details = dict(config.items(self.section))
        return details

    def get_db_connection(self):
        """
        method for getting an open connection to our database
        :return: db connection
        """
        conn = psycopg2.connect(**self.get_config_details())
        return conn

    def fetch_all_rows(self, sql):
        """
        Method which executes an SQL statement and returns the result as a tuple of tuples
        :param sql: SQL query to be executed
        :return: result-set as a tuple of tuples
        E.g. (('foo'), ('bar'), ('baz'), )
        """
        cursor = self.get_db_connection().cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        return results

    def execute_sql(self, sql, data=None, executemany=False):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        if data:
            cursor.executemany(sql, data) if executemany else cursor.execute(sql, data)
            conn.commit()
            rows = cursor.rowcount
            return rows
        cursor.execute(sql)
        conn.commit()
        rows = cursor.rowcount
        return rows

    @staticmethod
    def build_placement_holders(column_count):
        return ",".join('%s' for _ in xrange(column_count))

    def build_insert_sql(self):
        get_columns_sql = "select column_name from information_schema.columns where table_name = '{table_name}'"
        columns = self.fetch_all_rows(sql=get_columns_sql.format(table_name=TABLE_NAME))
        formatted_columns = ", ".join(x[0] for x in columns)
        return INSERT_TEMPLATE.format(table_name=TABLE_NAME,
                                      columns=formatted_columns,
                                      placement_holders=self.build_placement_holders(len(columns)))


class FacebookConnect(object):
    def __init__(self):
        """
        Instantiate the class
        :param access_token: token used to connect to the GraphAPI
        """
        self.token = raw_input("Please enter your Facebook Access Token:")
        try:
            self.connection = DBConnection('config.conf', 'local')
        except Exception as _error:
            raise DatabaseException("Failed to connect to Postgres Database: {error}".format(error=_error))

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
        :return: dictionary consisting of {post_data, url}
        """
        try:
            posts = self.connect().get_connections("me", "posts")
        except Exception as _error:
            raise FacebookException("Failed to connect to Facebook API: {error}".format(error=_error))
        post_data = posts['data']
        url = posts['paging']['next']
        return {'post_data': post_data, 'url': url}

    @staticmethod
    def get_previous_posts(url):
        """
        method which gets a json response object (posts) from which we get our data and our URL for the subsequent iterations
        :return: list consisting of [post_data, URL]
        """
        posts = requests.get(url).json()
        data = posts['data']
        if not data:
            sys.exit("No more data to process. Exiting Script")
        url_string = posts['paging']['next']
        return {'post_data': data, 'url': url_string}

    def get_insert_info(self, post_data):
        """
        now we loop through our post data to extract the bits we are after to insert into our database...
        :return: get a list of [created_time, facebook_post, likes]
        """
        insert_list = []
        latitude = None
        longitude = None
        place = None
        for posts in post_data['post_data']:
            try:
                date = datetime.strptime(str(posts['created_time'][0:10]), '%Y-%m-%d')
                object_id = posts['id']
                story = posts['story'] if 'story' in posts else None
                message = posts['message'] if 'message' in posts else None
                likes = len(posts['likes']['data']) if 'likes' in posts else None
                poster = posts['from']['name'] if 'from' in posts else None
                post_type = posts['type'] if 'type' in posts else None
                status_type = posts['status_type'] if 'status_type' in posts else None
                latitude = posts['place']['location']['latitude'] if 'place' in posts else None
                longitude = posts['place']['location']['longitude'] if 'place' in posts else None
                place = posts['place']['name'] if 'place' in posts else None
            except Exception as e:
                print "Error getting info for {error}".format(error=e)
            finally:
                insert_list.append((date,
                                    object_id,
                                    story,
                                    message,
                                    likes,
                                    poster,
                                    post_type,
                                    status_type,
                                    latitude,
                                    longitude,
                                    place))
        self.connection.execute_sql(sql=self.connection.build_insert_sql(),
                                    data=insert_list,
                                    executemany=True)
        self.get_insert_info(self.get_previous_posts(post_data['url']))

    def execute(self):
        """
        main entry point to execute the script
        """
        self.connection.execute_sql(sql=CREATE_TABLE_SQL)
        self.get_insert_info(self.get_posts())


if __name__ == '__main__':
    FacebookConnect().execute()
