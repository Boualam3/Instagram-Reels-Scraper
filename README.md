# 📸 Instagram Reels Scraper

A Python tool to **login, scrape, and extract data** from Instagram Reels — using your own browser session.

✅ No browser extension  
✅ No fake requests  
✅ Works with **Playwright** and saved session

---

## 🚀 What This Tool Does

1. **Login** to Instagram once and save session (no need to login every time).
2. **Scrape Reels** from a given link, scroll multiple times, and save response data.
3. **Extract data** (likes, views, engagement rate) from saved files into a `.csv`.
4. **Sort data** by plays, likes, or engagement rate.

---

## 📦 Setup

### 1. Clone this repo

```bash
git clone git@github.com:Boualam3/Instagram-Reels-Scraper.git
cd Instagram-Reels-Scraper
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
You also need to install Playwright:

```bash
playwright install
```

3. Create .env
Create a .env file with your Instagram credentials

```bash
USERNAME=your_instagram_username
PASSWORD=your_instagram_password
```

## 🚀 Usage 
# GUI
Run the command and check the browser http://localhost:8080 

```bash
python gui.py
``` 

# CLI 

### 1. Configure

Interactive setup for scraping:

```bash
python main.py config
``` 

You'll be asked for:

-   Instagram Reels link
    
-   Output folder
    
-   Scroll count
    
-   Delay between scrolls
    
-   Headless mode (y/n)
    

----------

### 2. Login

Login using your `.env` credentials. The session is saved in `insta_session.json`.

```bash
python main.py login
```

----------

### 3. Scrape Reels

Use saved session and configuration to collect reels data:

```bash
python main.py scrape
```

----------

### 4. Extract to CSV

Convert saved JSON responses into a clean CSV file:

```bash
python main.py extract
```

Optional flags:

-   `-o`, `--output`: Output CSV file (default: `reels_summary.csv`)
    
-   `-sbp`, `--sort-by-plays`: Sort by plays
    
-   `-sbl`, `--sort-by-likes`: Sort by likes
    
-   `-sbe`, `--sort-by-engagement`: Sort by engagement rate
    

Example:

```bash
python main.py extract -o top_reels.csv -sbp
```

----------

## 📁 Output Example
```csv
url,plays,likes,engagement_rate
instagram.com/reel/DAlBtOfyTip/,17.1M,592K,3.46%
instagram.com/reel/DC689zIdsXq/,15.3M,1.1M,7.32%
instagram.com/reel/DEVDHShsffF/,14.3M,328K,2.29%
``` 

----------

## 🔐 Notes

-   Session is saved in `insta_session.json`, so you don't need to login every time.
    
-   Configuration is saved in `.scraper_config.json`.
    
-   Make sure you're using a valid Instagram account for login.
    

----------

## ✅ To-Do / Improvements

-   Save scroll position to continue later
-   Improve Scraping and its Logs in GUI 