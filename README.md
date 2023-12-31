# YouTube Playlist to SQLite and send to your Telegram

Automate the extraction of information from a YouTube playlist, organize it in an SQLite database, and receive updates on your Telegram. This Python script simplifies the process, making it easy to manage your favorite YouTube content.

## Prerequisites

- Python 3.x
- SQLite Browser or a similar tool

## Installation

1. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

2. Obtain your YouTube API credentials and save them to a file.

3. Run the script:

    ```bash
    python main.py
    ```

    Follow the prompts to provide the path to your credentials file and the playlist ID.

4. Obtain a Telegram Bot Token and Chat ID. If you don't have them, you can [create a Telegram Bot](https://core.telegram.org/bots#botfather) and get your [Chat ID](https://t.me/getmyid_bot).

5. Insert your Telegram Bot Token and Chat ID when prompted.

## Usage

- The script will extract information from the provided YouTube playlist and store it in an SQLite database.
- Top songs with their artists, links, and view counts will be sent to your Telegram.
- The songs are sorted by view count, showcasing the most popular ones first.

## Database Query

Run the following SQL query in an SQLite browser to view the stored data:

```sql
SELECT Song.Artist, Song.title, Song.link, Song.view_count
FROM Song
ORDER BY Song.view_count DESC;
```


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
