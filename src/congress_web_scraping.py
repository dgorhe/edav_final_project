#!/usr/bin/env python
# coding: utf-8

import requests
import tweepy
import pandas as pd
import math
import json
import sys
from os.path import exists
from datetime import datetime as dt
from datetime import timezone as tz
from alive_progress import alive_bar

CREDENTIALS_PATH = ""
if (len(sys.argv) > 1):
    CREDENTIALS_PATH = sys.argv[1]
elif (len(sys.argv) == 1):
    if exists("./credentials.json"):
        CREDENTIALS_PATH = "./credentials.json"
        print("Using default credentials path ./credentials.json")
else:
    print("Usage: python3 congress_web_scraping.py <TWITTER CREDENTIALS FILEPATH>")
    sys.exit()

if exists("../data/checked_handles.txt"):
    print("Found cached Twitter handles in ../data/checked_handles.txt")
    cached_handles = []

    # Grabbing all the cached handles
    with open("../data/checked_handles.txt", "r") as h:
        line = h.readline().strip("\n")
        while line != "":
            cached_handles.append(line)
            line = h.readline().strip("\n")

    # Displaying cache 
    print("There are:", len(cached_handles), "in the cache")
    if (len(cached_handles) >= 5):
        print("Here are the first 5 values")
        [print(h) for idx, h in enumerate(cached_handles) if idx < 5]
        
    # Getting user input for what to do with cache
    resp = input("Would you like to use the handles in the cache [y/n]: ")
    if (resp.lower() == "y"):
        pass
    elif (resp.lower() == "n"):
        should_delete = input("Would you like to delete the cache? [y/n]: ")
        if (should_delete.lower() == "y"):
            open("..data/checked_handles.txt", "w").close()
        elif (should_delete.lower() == "n"):
            print("Will use the values in cache")
        else:
            print("Invalid input")
            sys.exit()
    else:
        print("Invalid input")
        sys.exit()
else:
    print("Creating checked_handles.txt because it doesn't exist")
    file = open("../data/checked_handles.txt", "x")
    file.close()


credentials = ""
with open(CREDENTIALS_PATH, "r") as cred:
    credentials = json.load(cred)

client = tweepy.Client(**credentials)
print("Initiated Client")

df = pd.read_csv("https://theunitedstates.io/congress-legislators/legislators-current.csv")
congress_twitter_handles = [x for x in list(df["twitter"]) if type(x) == str]
print("Read handles")

# Static parameters for tweet search
fields = ['created_at', 'geo', 'lang']
start_utc = dt.strptime("01/01/2020 00:00:00", "%m/%d/%Y %H:%M:%S")
end_utc = dt.strptime("12/31/2020 11:59:59", "%m/%d/%Y %H:%M:%S")
start_utc_iso8601 = start_utc.astimezone(tz.utc).isoformat('T', timespec='milliseconds').replace("+00:00", "Z")
end_utc_iso8601 = end_utc.astimezone(tz.utc).isoformat('T', timespec='milliseconds').replace("+00:00", "Z")

# Formatted dictionary to 
users_tweets_kwargs = {
    "max_results": 100,
    "start_time": start_utc_iso8601,
    "end_time": end_utc_iso8601,    
    "tweet_fields": fields
}

def write_to_csv(filename, dictionary):
    with open(filename, "w") as f:
        for key, value in dictionary.items():
            for val in value:
                items = [key, "\"" + val.text + "\"", str(val.id), str(val.geo), str(val.lang)]
                line = ",".join(items) + "\n"
                f.write(line)


def get_tweets(client, handles, tweet_details, dictionary={}, cache="../data/checked_handles.txt"):
    checked = open(cache, "r+")
    checked_handles = [line for line in checked.read().split("\n") if line != ""]

    # Looping through all twitter handles to get tweets
    with alive_bar(len(handles)) as bar:        
        for handle in handles:
            # If we don't have tweets for handle, get them
            if (handle not in checked_handles):
                congress_person = client.get_user(username=handle)
                tweet_details["id"] = congress_person.data.id
                paginator = tweepy.Paginator(client.get_users_tweets, **tweet_details)
                dictionary[handle] = []
                
                # Iterate through pages of 100 tweets and append each tweet
                for response in paginator:
                    if (response.data) and (len(response.data) > 0):
                        for tweet in response.data:
                            dictionary[handle].append(tweet)
            
                # Writing to csv, one handle at a time
                write_to_csv("../data/congress_tweets.csv", dictionary)
                checked.write(handle + "\n") 
                checked_handles.append(handle)
                dictionary = {}
        
        bar()
                
    return checked_handles


get_tweets(client, congress_twitter_handles, users_tweets_kwargs)
