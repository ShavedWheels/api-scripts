from stravalib import Client
from bishared.job_utils import WarehouseConnectionManager, LoggingUtils


class Strava(object):
    """
    Class which holds all of our Strava API attributes along with conversion / helper methods
    """

    def __init__(self):
        """
        Instantiate the class
        :param token: access token to use to gain access
        """
        self.token = 'insert_token_here'

    def get_connection(self):
        """
        Method to connect to the Strava API
        :returns: connection
        """
        conn = Client(access_token=self.token)
        return conn

    def get_details(self):
        """
        Method which confirms the athlete is actually you.
        :returns: Message with your first name, surname and how many followers you have on Strava
        """
        conn = self.get_connection()
        athlete = conn.get_athlete()
        return "Hey! My name is {first_name} {last_name}. I have {followers} followers on Strava".format(
            first_name=athlete.firstname,
            last_name=athlete.lastname,
            followers=athlete.follower_count)

    @staticmethod
    def distance_converter(qnty_obj):
        """
        Method which converts from metres to miles seeing as we live in the UK. We DON'T TALK IN KM's!!!
        :param qnty_obj: Quantity Class
        :returns: distance cycled in miles
        """
        metres = qnty_obj.get_num()
        miles = metres * 0.000621371
        return miles

    @staticmethod
    def real_watts(flag, watts):
        """
        Method which checks whether the watts which are shown are "estimated" or from a actual powermeter.
        If the watts are from a powermeter, show the average power, otherwise get rid of it as it's garbage data
        :param flag: boolean flag
        :param watts: average power
        """
        if flag is True:
            return watts

    @staticmethod
    def time_in_seconds(timedelta):
        """
        method which takes in a timedelta object and converts it to seconds
        :param timedelta: timedelta object
        :returns: time of ride in seconds
        """
        sec = timedelta.total_seconds()
        return sec

    @staticmethod
    def metres_to_feet(qnty_obj):
        """
        Method which converts from metres into feet.
        :param qnty_obj: Quantity class
        :returns: elevation climbed in feet
        """
        metres = qnty_obj.get_num()
        feet = metres * 3.28084
        return feet

    def get_activities(self):
        """
        Main method which gets all historic ride data and transforms it accordingly so that we can insert the data
        into our a table to easily query
        """
        ride_info = []

        conn = self.get_connection()
        activities = conn.get_activities()
        for active in activities:
            ride_info.append((active.id,
                              active.name,
                              active.start_date.strftime('%Y-%m-%d'),
                              self.distance_converter(active.distance),
                              self.real_watts(active.device_watts, active.average_watts),
                              self.time_in_seconds(active.moving_time),
                              self.time_in_seconds(active.elapsed_time),
                              active.kudos_count,
                              self.metres_to_feet(active.total_elevation_gain),
                              active.kilojoules))
        return ride_info


class Connection(Strava):
    """
    Class for getting DB Connections
    """

    def __init__(self, config, section):
        """
        Initialise the class by reading a config file and config section
        :param config: config file to read from
        :param section: section of config file
        """
        self.config = config
        self.section = section

        super(Connection, self).__init__()

    def connect(self):
        """
        Method for getting a connection
        :returns: DB Connection
        """
        conn = WarehouseConnectionManager(self.config, self.section)
        return conn

    def create_table(self):
        """
        Method for creating our table which we will insert our data into
        """
        sql = \
        """create table if not exists strava_data (
            id int not null auto_increment unique key,
            activity_id int primary key,
            _date date,
            distance_miles decimal (10,4),
            avg_power decimal (10, 4),
            moving_time_seconds decimal(18, 4),
            elapsed_time_seconds decimal (18, 4),
            kudos_count int,
            elevation_feet decimal(18, 4),
            kilojoules decimal (12, 2))"""
        self.connect().execute(sql)

    def insert_data(self):
        """
        Method which inserts our data
        """
        self.create_table()
        self.connect().execute_many("""insert ignore into strava_data
        (activity_id,
        name,
        _date,
        distance_miles,
        avg_power,
        moving_time_seconds,
        elapsed_time_seconds,
        kudos_count,
        elevation_feet,
        kilojoules) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""", self.get_activities())


if __name__ == '__main__':
    logger = LoggingUtils.setup_logging('strava_data', 'log')
    Connection('app.conf', 'bireporting').insert_data()
