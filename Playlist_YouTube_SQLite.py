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
    print(response.status_code)
    print(response.json())


def main():
    
    conn = sqlite3.connect('PlaylistYouTube.sqlite')
    cur = conn.cursor()

    # Make some fresh tables using executescript()
    cur.executescript('''
    DROP TABLE IF EXISTS Artist;
    DROP TABLE IF EXISTS Song;

    CREATE TABLE Artist (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        name    TEXT UNIQUE
    );
    
    CREATE TABLE Song (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        title   TEXT UNIQUE,
        artist_id  INTEGER,
        link    TEXT UNIQUE
    )
    ''')
    
    
    youtube = authorization()
    
    
    playlist_id = input("INSERT YOUR PLAYLIST Address HERE: ")
    '''
    You can find addresses such a the example below:
    https://www.youtube.com/playlist?list=PLfzRniKpg9XQ_HExJ_ceAhnOdi5rqlY9m
    => PLfzRniKpg9XQ_HExJ_ceAhnOdi5rqlY9m
    '''
    
    max_results = int(input("Please Insert the total number of items in your playlist: "))

    playlist_items = get_playlist_items(youtube, playlist_id, max_results)

    for i, item in enumerate(playlist_items):
        print(f'Number of Music {i + 1}')

        title_Track = (item["snippet"]["title"]).split('-')
        artist = title_Track[0]
        print('Artist is: ',artist)
        if artist == 'Deleted video':
            continue
        else:
            try:
                song = title_Track[1]
                print('Song is: ',song)
            except:
                song = "THIS IS A CONCERT LIVE OR SOMETHING LIKE THIS"
                
            link = f'https://youtu.be/{item["snippet"]["resourceId"]["videoId"]}'
            
            cur.execute('''INSERT OR IGNORE INTO Artist (name) 
                        VALUES ( ? )''', ( artist, ) )
            cur.execute('SELECT id FROM Artist WHERE name = ? ', (artist, ))
            artist_id = cur.fetchone()[0]
            
            cur.execute('''INSERT OR REPLACE INTO Song (title, artist_id, link)
                        VALUES ( ?, ?, ? )''', (song, artist_id, link, ) )
            conn.commit() # Commit the changes to the database
            
            message = song, artist, link
            
            send_telegram_message(token, chat_id, message)

if __name__ == "__main__":
    
    #TELEGRAM SEND ARTIST, SONG and LINK
    token = input("Insert Your TELEGRAM Bot Token: ")
    
    #For finding the Chat ID in Telegram You can Use this Bot: https://t.me/getmyid_bot
    chat_id = input("Insert Your Chat ID: ")

    main()

'''Prompt this command to the Tap on Execute SQL in SQlite Broswer app:
SELECT Song.title,Artist.name,Song.link FROM Song JOIN Artist ON Song.artist_id = Artist.id'''