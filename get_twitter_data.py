import os, codecs, json, argparse
import twitter
from time import sleep

#Get api keys and access keys from local files
with open(".tkeys") as f: 
    api_key, api_secret_key = f.read().strip().split("\t")
with open(".taccess") as f:
    access_key, access_secret_key = f.read().strip().split("\t")
    
api = twitter.Api(consumer_key=api_key, consumer_secret=api_secret_key,
                  access_token_key=access_key, access_token_secret=access_secret_key)

def get_user_friends_timelines(api, username, num_tweets=300):
    friends = api.GetFriendIDs(screen_name=username) #get user friends (i.e. people who username follows in Twitter)
    user_filename = "%s__friends_timelines.json" % username
    timelines = {} #dictionary with keys corresponding to Twitter user_id (numerical ids) and values corresponding to a list of tweets for that user
    if os.path.exists(user_filename):
        timelines = json.load(codecs.open(user_filename, "r", "utf-8"))
    for i in range(len(friends)):
        try:
            statuses = api.GetUserTimeline(user_id=friends[i], count=num_tweets)
            for status in statuses: #Iterate over each friend's tweets
                timelines.setdefault(friends[i], []).append(status.GetText()) #store it in a dictionary
            if (i+1) % 10 == 0:
                print i, 'friends processed'
            sleep(1.2) #be nice
        except twitter.error.TwitterError:
            break
    json.dump(timelines, codecs.open(user_filename, "w", "utf-8"))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Twitter timelines of a certain user\'s friends.')
    parser.add_argument('username', help='Twitter user name')
    parser.add_argument('-n', '--num-tweets', nargs='?', type=int, default=300, help='Number of tweets per timeline to retrieve (default=300)')
    args = parser.parse_args()
    timelines = get_user_friends_timelines(api, args.username, args.num_tweets)
    