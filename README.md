# Various Ad-Hoc Scripts 

**(Facebook API, Twitter API, S3 Bucket)**

*fb_posts.py*

Cool little script which uses the Facebook GraphAPI to extract all the wall posts you have posted,
along with the amount of 'likes' (if any) it has recieved and the datetime you posted it.
It then inserts the data into a MySQL database table.


*twitter_posts.py*

Similar to the Facebook script but using the TwitterAPI this time via the twitter library, gets the 200 most recent tweets 
on your timeline along with the datetime it was created and the amount of favourite checks it received.
It then inserts the data into a MySQL database
