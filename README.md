# Various Ad-Hoc Scripts 

**(Facebook API, Twitter API, Strava API, S3 Bucket)**

##### A local Postgres Database (9.5 or higher) is required.

*fb_posts.py*

Script which uses the Facebook GraphAPI to extract all the wall posts you have posted,
along with the location it was posted from (latitude, longitude), amount of 'likes' (if any) it has recieved and the datetime you posted it.
It then inserts the data into a Postgres database table called 'fb_posts'.

*Tableau Dashboard*
https://public.tableau.com/profile/aaronolszewski#!/vizhome/Facebook_33/Facebook

# Running the Script

Clone the project to a local directory and create an virtualenv e.g. facebook-data:

```
$ mkvirtualenv facebook-data
```

Once created, run the make file from the root folder (api-scripts)

```
(facebook-data) $ make
```

*twitter_posts.py*

Similar to the Facebook script but using the TwitterAPI this time via the twitter library, gets the 200 most recent tweets 
on your timeline along with the datetime it was created and the amount of favourite checks it received.
It then inserts the data into a MySQL database

*strava.py*

Extracts all historic cycling data using the StravaAPI. Apply a load of transforms so that we can then insert the data into a MySQL database.

Metrics used are:
-date of activity
-distance cycled in miles
-average power for activity (only where a powermeter is present)
-activity moving time in seconds
-activity elapsed time in seconds
-amount of likes / kudos
-elevation climbed in feet
-amount of Kilojoules burned for the ride
