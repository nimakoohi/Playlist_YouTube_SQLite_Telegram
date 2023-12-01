import sqlite3
#This imports the SQLite database module

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery #It is used for discovering and building APIs
import googleapiclient.errors
from google.auth.transport.requests import Request

import pickle

import requests
#This import Telegram Bot

import re

import time


scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

def get_playlist_items(youtube, playlist_id, max_results=50):
    playlist_items = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=min(50, max_results),
            playlistId=playlist_id,
            pageToken=next_page_token
        )
        response = request.execute()

        playlist_items.extend(response.get('items', []))
        next_page_token = response.get('nextPageToken')

        if not next_page_token or len(playlist_items) >= max_results:
            break

    return playlist_items

def get_view_count(youtube, video_id):
    request = youtube.videos().list(
        part="id,statistics",
        id=video_id
    )
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        if 'statistics' in response['items'][0] and 'viewCount' in response['items'][0]['statistics']:
            return int(response['items'][0]['statistics']['viewCount'])

    return None  # Return None if view count could not be fetched

def format_view_count(view_count):
    if view_count is not None:
        if view_count >= 1_000_000_000:
            return f'{view_count / 1_000_000_000:.2f}B'
        elif view_count >= 1_000_000:
            return f'{view_count / 1_000_000:.2f}M'
        elif view_count >= 1_000:
            return f'{view_count / 1_000:.2f}k'
        else:
            return str(view_count)
    else:
        return 'N/A'


def authorization():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = input(r"INSERT YOUR SECRETS YouTube FILE: ")
    #e.g. (r"path/to/dir/here")

    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    credentials = None  # Initialize credentials to None

    if os.path.exists('token.pickle'):
        # Load existing credentials from the file
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if credentials is None or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            # Refresh the credentials if they are expired
            credentials.refresh(Request())
        else:
            # Run the authorization flow if no valid credentials are available
            # Get credentials and create an API client
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes)
            credentials = flow.run_local_server(port=0)

        # Save the credentials to the file
        with open('token.pickle', 'wb') as f:
            pickle.dump(credentials, f)
            
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)
        
    return youtube


def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    response = requests.get(url)


def main():
    
    
    conn = sqlite3.connect('PlaylistYouTube.sqlite')
    cur = conn.cursor()

    # Make some fresh tables using executescript()
    cur.executescript(''' 
    DROP TABLE IF EXISTS Artist;
    DROP TABLE IF EXISTS Song;
    
    
    CREATE TABLE IF NOT EXISTS Song (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        Artist TEXT,
        title   TEXT,
        link    TEXT UNIQUE,
        view_count INTEGER
    );
    ''')
    
    
    
    youtube = authorization()
    
    
    playlist_id = input("INSERT YOUR PLAYLIST Address Link HERE: ")
    playlist_id = playlist_id.strip()
    playlist_id = re.split(r'playlist\?list=(.+)', playlist_id)
    playlist_id = playlist_id[1].strip()
    
    max_results = int(input("Please Insert the total number of items in your playlist: "))
    

    playlist_items = get_playlist_items(youtube, playlist_id, max_results)

    for i,item in enumerate(playlist_items):

        title_Track = re.split(r'([-|–].*)', item["snippet"]["title"])
        
        artist = title_Track[0].strip()
        
        if artist == 'Deleted video':
            continue
        else:
            try:
                song = title_Track[1].strip()
            except:
                song = "  THIS IS A CONCERT LIVE OR SOMETHING LIKE THIS"
                
            link = f'https://youtu.be/{item["snippet"]["resourceId"]["videoId"]}'
            
            # Check if the link already exists in the database
            cur.execute('SELECT id FROM Song WHERE link = ?', (link,))
            existing_link = cur.fetchone()

            if existing_link:
                print(f'Song with link {link} already exists. Skipping...')
                time.sleep(2)
                continue
            
            # Fetch view count for this video
            view_count = get_view_count(youtube, item["snippet"]["resourceId"]["videoId"])
            
            
            cur.execute('''INSERT INTO Song (Artist, title, link, view_count)
                    VALUES ( ?, ?, ?, ? )''', (artist, song, link, view_count, ) )
            
            conn.commit()  # Commit the changes to the database
            
            print(f'Music {i + 1} has been uploaded to the Database!!')
                
                
    cur.execute('SELECT Song.Artist, Song.title, Song.link, Song.view_count FROM Song ORDER BY Song.view_count DESC')
    sorted_songs = cur.fetchall()
    

    for i, song in enumerate(sorted_songs):
        title, artist, link, view_count = song
        
        # Send the message to Telegram
        message = f'Top {i + 1}'
        send_telegram_message(token, chat_id, message)
        message = f"{artist}{title}"
        send_telegram_message(token, chat_id, message)
        message = f"Link: {link}\nView Count: {format_view_count(view_count)}"
        send_telegram_message(token, chat_id, message)

        print(f"Music Number {i + 1} has been sent on Telegram!!")

         

if __name__ == "__main__":
    
    token = input("Insert Your TELEGRAM Bot Token: ")
    
    #For finding the Chat ID in Telegram You can Use this Bot: https://t.me/getmyid_bot
    chat_id = input("Insert Your Chat ID: ")

    main()