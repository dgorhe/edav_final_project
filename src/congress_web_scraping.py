#!/usr/bin/env python
# coding: utf-8

import requests
import tweepy
import pandas as pd
import math
import json
from os.path import exists
from datetime import datetime as dt
from datetime import timezone as tz
from alive_progress import alive_bar

dgorhe_cred = {
    "bearer_token": "AAAAAAAAAAAAAAAAAAAAACC0VQEAAAAAVMb%2BsKdjGQF%2Bk2P0SxmpbqLPFeg%3DGQiBNYXWePAyShoZdbYpUGhLeysplsdxZ8eKMWPfhDUfWpLilo",
    "consumer_key": "BoxdMYUEnBcdl0Rf3dXKCRrKN",
    "consumer_secret": "BosBJ90fJ81EMnznNkgRcncbA6KtrSARwuUkqkdh9EUvgDvvqT",
    "access_token": "1084676618554028034-Me3iM6GE8fkZ0HFtvDnYU7X2kwkxEA",
    "access_token_secret": "JcNVR8vA4guM6T2gQTvQkRNcuJ8nIaPUQxNhaEG9c8ctI",
}
client = tweepy.Client(**dgorhe_cred)
print("Initiated Client")

df = pd.read_csv("https://theunitedstates.io/congress-legislators/legislators-current.csv")
congress_twitter_handles = [x for x in list(df["twitter"]) if type(x) == str]
print("Read handles")

# Static parameters for tweet search
# fields = ['created_at', 'geo', 'lang', 'context_annotations', 'entities']
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
        with alive_bar(len(dictionary.keys())) as bar:
            for key, value in dictionary.items():
                for val in value:
                    # items = [key, val.text, str(val.id), str(val.geo), str(val.lang), json.dumps(val.context_annotations), json.dumps(val.entities)]
                    items = [key, "\"" + val.text + "\"", str(val.id), str(val.geo), str(val.lang)]
                    line = ",".join(items) + "\n"
                    f.write(line)
            bar()


# TODO: Add typing
def get_tweets(client, handles, kwargs, dictionary={}, cache="../data/checked_handles.txt"):
    checked = open(cache, "r+")
    checked_handles = [line for line in checked.read().split("\n") if line != ""]

    # Looping through all twitter handles to get tweets
    with alive_bar(len(handles)) as bar:        
        for handle in handles:
            # If we don't have tweets for handle, get them
            if (handle not in dictionary.keys() and handle not in checked_handles):
                congress_person = client.get_user(username=handle)
                kwargs["id"] = congress_person.data.id
                paginator = tweepy.Paginator(client.get_users_tweets, **kwargs)
                dictionary[handle] = []
                
                # Iterate through pages of 100 tweets and append each tweet
                for response in paginator:
                    if (response.data) and (len(response.data) > 0):
                        for tweet in response.data:
                            dictionary[handle].append(tweet)
            bar()

            write_to_csv("../data/congress_tweets.csv", dictionary)
            checked.write(handle + "\n") 
            checked_handles.append(handle)
            dictionary = {}
                
    return checked_handles



congress_tweets = {}
checked_handles = []

if exists("../data/checked_handles.txt"):
    with open("../data/checked_handles.txt", "r") as h:
        line = h.readline().strip("\n")
        while line != "":
            checked_handles.append(line)
            line = h.readline().strip("\n")
else:
    file = open("../data/checked_handles.txt", "x")
    file.close()

get_tweets(client, congress_twitter_handles, users_tweets_kwargs, congress_tweets)
