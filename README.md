# Bangalore Pulse - Data Scraper & Analysis Agent

## 1. Project Overview

This is the primary data ingestion and pre-processing engine for the "Managing City Data Overload" project. Its core responsibility is to act as the central nervous system for the application, gathering raw data from across the internet, enriching it with initial analysis, and storing it in a structured format for consumption by other services, particularly the Gemini AI agent.

### Key Features
- **Multi-Source Ingestion:** Scrapes data from both verified news RSS feeds and real-time citizen reports from the `r/bangalore` subreddit.
- **Intelligent Pre-processing:** Goes beyond simple collection by performing first-pass analysis on all incoming data.
- **Automated Categorization:** Reads event text to automatically tag it with relevant categories like `traffic`, `civic_issue`, `power_cut`, or `cultural_event`.
- **Location Extraction:** Identifies mentions of key Bangalore localities (e.g., "Koramangala", "HSR Layout") to provide geographical context.
- **Robust & Resilient:** Built with duplicate prevention to ensure data integrity and error handling for reliable operation.
- **Standardized Output:** All data is transformed into a unified JSON schema, making it incredibly easy for other services to consume.

### System Architecture
The scraper fits into the overall project as the first crucial step:

`Sources (RSS, Reddit)  ->  [ Python Scraper ]  ->  Enriched Data (MongoDB)  ->  Downstream Services (Gemini, Firebase)`

---

## 2. Prerequisites

Before you begin, you must have the following software installed on your development machine:

1.  **Python** (version 3.8 or newer)
2.  **Docker Desktop** (the latest version)

---

## 3. Step-by-Step Setup Guide

Follow these instructions in order to configure and run the scraper.

### Step 3.1: Get the Code & Prepare Environment

First, create a local project folder and set up a Python virtual environment to keep dependencies clean and isolated.

```bash
# 1. Navigate to your project folder
cd /path/to/project_folder

# 2. Create a Python virtual environment named 'myenv'
python -m venv myenv

# 3. Activate the virtual environment. This command depends on your OS.
#    On Windows (using Command Prompt):
myenv\Scripts\activate.bat

#    On macOS and Linux (using bash/zsh):
source myenv/bin/activate

# Your terminal prompt should now start with (myenv)
```

### Step 3.2: Install Required Libraries

With your virtual environment active, install all the necessary Python packages using the provided `requirements.txt` file.

```bash
# This command reads the requirements.txt file and installs everything
pip install -r requirements.txt
```

### Step 3.3: Launch the MongoDB Database with Docker

The scraper stores its data in a MongoDB database. We will run this database inside a Docker container.

**A. First-Time Setup (Do this only once):**
This command downloads the official MongoDB image and creates a persistent container named `my-mongo-db`.
```bash
docker run --name my-mongo-db -p 27017:27017 -d mongo
```

**B. Subsequent Starts (Do this every time you restart your PC):**
If the container already exists but is stopped, simply start it again.
```bash
docker start my-mongo-db
```

**C. Verify it's Running:**
You can check that the container is running with the `docker ps` command. You should see `my-mongo-db` in the list with a status of "Up".

### Step 3.4: Configure Reddit API Credentials

The script requires API keys to access Reddit. These must be stored as secure environment variables, not in the code.

**A. Get Your Credentials:**
Go to your [Reddit Apps](https://www.reddit.com/prefs/apps) page and get your:
- `Client ID`
- `Client Secret`
- Your Reddit `Username`

**B. Set the Environment Variables:**
The method depends on your Operating System.

**On Windows (using Command Prompt `cmd.exe`):**
Run these three commands, replacing the placeholder text with your actual credentials.
```cmd
setx REDDIT_CLIENT_ID "your_real_client_id_here"
setx REDDIT_CLIENT_SECRET "your_real_client_secret_here"
setx REDDIT_USER_AGENT "BglrPulseApp/1.0 by u/YourUsername"
```
**CRITICAL:** You **must close and reopen** your Command Prompt window after running these commands for them to take effect.

**On macOS and Linux:**
Add the following lines to your shell's configuration file (e.g., `~/.zshrc`, `~/.bashrc`, or `~/.profile`).
```bash
export REDDIT_CLIENT_ID="your_real_client_id_here"
export REDDIT_CLIENT_SECRET="your_real_client_secret_here"
export REDDIT_USER_AGENT="BglrPulseApp/1.0 by u/YourUsername"
```
After saving the file, apply the changes by running `source ~/.zshrc` (or your relevant file) or simply restart your terminal.

---

## 4. Running the Scraper

With all setup complete, running the script is a single command. Ensure your virtual environment is active and your Docker container is running.

```bash
python master_scraper.py
```

The script will print its progress to the console, indicating successful connections and how many new documents were added to the database.

---

## 5. Verifying the Data

The best way to see your data is with **MongoDB Compass**, a free graphical tool for MongoDB.

1.  **Download and Install:** Get MongoDB Compass from the official website.
2.  **Connect:** Open Compass and use the default connection string: `mongodb://localhost:27017`. Click "Connect".
3.  **Navigate:** On the left, click on the **`bangalore_pulse`** database, then click on the **`events`** collection.
4.  **Inspect:** You will see all the scraped documents. Click on any document to see its details. To see the smart tags, find the `analysis` field and **click the small triangle `▸` next to it** to expand the object.

### Data Schema
Every document in the `events` collection follows this enriched schema. The `analysis` object is the key value-add from this script.
```json
{
  "_id": "...",
  "event_id": "reddit_...",
  "source_type": "Reddit",
  "source_name": "r/bangalore",
  "content_raw": "Massive traffic jam at Silk Board...",
  "content_summary": "Massive traffic jam at Silk Board",
  "link_original": "https://www.reddit.com/...",
  "timestamp_published": "...",
  "timestamp_scraped": "...",
  "media_urls": [],
  "analysis": {
    "categories": [
      "traffic"
    ],
    "mentioned_locations": [
      "Silk Board"
    ]
  }
}
```

---

## 6. Project Files

This package contains:
- `master_scraper.py`: The main Python script.
- `README.md`: This instruction file.
- `requirements.txt`: The list of Python dependencies.
```
