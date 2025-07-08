import feedparser
import praw
import pymongo
import os
# Import 'timezone' to handle the new datetime format
from datetime import datetime, timezone
from time import mktime

# --- CONFIGURATION ---
RSS_FEEDS = {
    'TimesOfIndia': 'https://timesofindia.indiatimes.com/rssfeeds/-2128833038.cms',
    'TheHindu': 'https://www.thehindu.com/news/cities/bangalore/feeder/default.xml',
    'DeccanHerald': 'https://www.deccanherald.com/rss/city/bengaluru.xml',
    'BangaloreMirror': 'https://bangaloremirror.indiatimes.com/rssfeeds/-2128830345.cms'
}
SUBREDDIT_NAME = "bangalore"
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "bangalore_pulse"
MONGO_COLLECTION_NAME = "events"


# --- SETUP FUNCTIONS ---

def setup_database():
    """Connects to MongoDB, creates the collection, and sets up a unique index."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ismaster')
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        collection.create_index("link_original", unique=True)
        print("✅ MongoDB connection successful.")
        return collection
    except pymongo.errors.ConnectionFailure as e:
        print(f"❌ Could not connect to MongoDB: {e}")
        return None

def setup_reddit_client():
    """
    Sets up and returns a PRAW Reddit instance using credentials
    read securely from environment variables.
    """
    try:
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT")

        if not all([client_id, client_secret, user_agent]):
            print("❌ Error: Reddit credentials not found in environment variables.")
            return None

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            request_timeout=15
        )
        reddit.user.me()
        print("✅ Reddit client setup successful.")
        return reddit
    except Exception as e:
        print(f"❌ Error connecting to Reddit: {e}")
        return None


# --- DATA FETCHING FUNCTIONS ---

def fetch_rss_data():
    """Fetches data from all RSS feeds and formats it into the Unified Schema."""
    all_events = []
    print("\n--- 📰 Fetching RSS News Feeds ---")
    for source, url in RSS_FEEDS.items():
        print(f"  -> Scraping {source}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                published_dt = datetime.now(timezone.utc)
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                # UPDATED: Replaced datetime.utcnow()
                event = {"event_id": f"rss_{entry.get('id', entry.get('link'))}", "source_type": "RSS", "source_name": source, "content_raw": entry.get("title", "No Title"), "content_summary": entry.get("summary", "No Summary"), "link_original": entry.get("link"), "timestamp_published": published_dt, "timestamp_scraped": datetime.now(timezone.utc), "location": {"text_raw": None, "geo_coordinates": None}, "media_urls": [], "categories": [tag.term for tag in entry.get('tags', [])]}
                if event["link_original"]: all_events.append(event)
        except Exception as e:
            print(f"    ! Could not process feed from {source}. Reason: {e}")
    return all_events

def fetch_reddit_data(reddit_client):
    """Fetches new posts from a subreddit and formats them into the Unified Schema."""
    if reddit_client is None: return []
    all_events = []
    subreddit = reddit_client.subreddit(SUBREDDIT_NAME)
    print(f"\n--- 🤖 Fetching Reddit Posts from r/{subreddit.display_name} ---")
    try:
        for submission in subreddit.new(limit=50):
            # UPDATED: Replaced utcfromtimestamp() and utcnow()
            event = {"event_id": f"reddit_{submission.id}", "source_type": "Reddit", "source_name": f"r/{subreddit.display_name}", "content_raw": f"{submission.title} :: {submission.selftext}", "content_summary": submission.title, "link_original": f"https://www.reddit.com{submission.permalink}", "timestamp_published": datetime.fromtimestamp(submission.created_utc, timezone.utc), "timestamp_scraped": datetime.now(timezone.utc), "location": {"text_raw": submission.title, "geo_coordinates": None}, "media_urls": [submission.url] if not submission.is_self and "reddit.com" not in submission.url else [], "categories": [submission.link_flair_text] if submission.link_flair_text else []}
            all_events.append(event)
    except Exception as e:
        print(f"  ! Error fetching from Reddit: {e}")
    return all_events


# --- DATABASE STORAGE ---

def store_events_in_db(collection, events):
    """Stores a list of event dictionaries in MongoDB, avoiding duplicates."""
    if not events: return 0
    events_added = 0
    for event in events:
        try:
            result = collection.update_one({'link_original': event['link_original']}, {'$setOnInsert': event}, upsert=True)
            if result.upserted_id: events_added += 1
        except Exception as e:
            print(f"    ! Error storing event '{event.get('link_original')}': {e}")
    return events_added


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    try:
        print("🚀 Starting Bangalore Pulse Scraper...")
        db_collection = setup_database()
        reddit_client = setup_reddit_client()
        if db_collection is None or reddit_client is None:
            print("\n❌ Halting execution due to setup failure. Please check error messages above.")
        else:
            rss_events = fetch_rss_data()
            rss_added = store_events_in_db(db_collection, rss_events)
            print(f"-> RSS: Fetched {len(rss_events)} articles, added {rss_added} new ones to the database.")
            reddit_posts = fetch_reddit_data(reddit_client)
            reddit_added = store_events_in_db(db_collection, reddit_posts)
            print(f"-> Reddit: Fetched {len(reddit_posts)} posts, added {reddit_added} new ones to the database.")
            print("\n✅ Scraping cycle complete.")
    except Exception as e:
        print("\n" + "="*60 + "\n‼️  AN UNEXPECTED ERROR OCCURRED! ‼️\n" + f"    ERROR DETAILS: {e}\n" + "="*60)