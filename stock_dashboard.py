import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import pytz
import os
from dateutil import parser
from gnews import GNews
from streamlit_gsheets import GSheetsConnection

# Constants
WATCHLIST_FILE = 'watchlist.csv'
TZ_SHANGHAI = pytz.timezone('Asia/Shanghai')

# --- Helper Functions ---

def load_watchlist():
    """Loads the watchlist from a CSV file. Returns a list of tickers."""
    if not os.path.exists(WATCHLIST_FILE):
        return []
    try:
        df = pd.read_csv(WATCHLIST_FILE, header=None)
        if df.empty:
            return []
        # Assume first column contains tickers
        tickers = df[0].dropna().astype(str).unique().tolist()
        return sorted(tickers)
    except Exception as e:
        st.error(f"Error loading watchlist: {e}")
        return []

def save_watchlist(tickers):
    """Saves the list of tickers to the CSV file."""
    try:
        df = pd.DataFrame(tickers)
        df.to_csv(WATCHLIST_FILE, index=False, header=False)
    except Exception as e:
        st.error(f"Error saving watchlist: {e}")

def get_stock_price_data(ticker):
    """Fetches just the price data using yfinance."""
    stock = yf.Ticker(ticker)
    try:
        hist = stock.history(period="5d")
        if hist.empty:
            return None
        current_price = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        price_change = current_price - previous_close
        percent_change = (price_change / previous_close) * 100
        return {
            "current_price": current_price,
            "change": price_change,
            "pct_change": percent_change
        }
    except Exception:
        return None

def load_bookmarks():
    """Loads bookmarks from Google Sheets."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="stock_bookmarks", ttl=0)
        if df.empty:
            return []
        return df.to_dict('records')
    except Exception as e:
        # If credentials are missing locally, this might fail.
        # Check if secrets file exists first or handle gracefully.
        print(f"Error loading bookmarks from GSheets: {e}")
        return []

def save_bookmark(article, ticker, category):
    """Saves a news article to bookmarks in Google Sheets."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="stock_bookmarks", ttl=0)
        
        # Deduplication check by URL
        # GSheets read returns a DF, if empty or first time, might be issue if no columns.
        # But assuming sheet exists with columns or we handle it.
        
        if not df.empty and 'URL' in df.columns:
            if article['link'] in df['URL'].values:
                st.toast(f"Already saved: {article['title'][:30]}...")
                return

        new_bookmark = {
            'Timestamp': datetime.datetime.now().isoformat(),
            'Ticker': ticker,
            'Category': category,
            'Title': article['title'],
            'URL': article['link'],
            'Source': article['source']
        }
        
        # Append logic
        if df.empty:
            # Create new DF
            updated_df = pd.DataFrame([new_bookmark])
        else:
            new_row = pd.DataFrame([new_bookmark])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            
        conn.update(worksheet="stock_bookmarks", data=updated_df)
        st.cache_data.clear() # Clear cache to refresh read
        st.toast(f"Saved: {article['title'][:30]}...")
        
    except Exception as e:
        st.error(f"Error saving bookmark to GSheets: {e}")

def remove_bookmark(url):
    """Removes a bookmark by URL from Google Sheets."""
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="stock_bookmarks", ttl=0)
        
        if df.empty or 'URL' not in df.columns:
            return

        # Filter out the URL
        updated_df = df[df['URL'] != url]
        
        conn.update(worksheet="stock_bookmarks", data=updated_df)
        st.cache_data.clear()
        st.toast("Article removed.")
    except Exception as e:
        st.error(f"Error removing bookmark from GSheets: {e}")


# --- News Fetching Functions ---

def normalize_title(title):
    """Simple normalization for deduplication."""
    if not title:
        return ""
    return str(title).lower().strip()

def fetch_yfinance_news(ticker):
    """Fetches news from Yahoo Finance."""
    articles = []
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        for item in news:
            # yfinance dates are unix timestamps
            pub_time = item.get('providerPublishTime', 0)
            if isinstance(pub_time, int):
                dt = datetime.datetime.fromtimestamp(pub_time, tz=datetime.timezone.utc)
            else:
                dt = datetime.datetime.now(datetime.timezone.utc)
            
            articles.append({
                'title': item.get('title'),
                'link': item.get('link'),
                'publisher': item.get('publisher'),
                'published_at': dt,
                'source': 'Yahoo'
            })
    except Exception as e:
        print(f"YFinance news error for {ticker}: {e}")
    return articles

def fetch_gnews(ticker):
    """Fetches news from Google News."""
    articles = []
    try:
        google_news = GNews(max_results=3)
        g_news = google_news.get_news(f"{ticker} stock news")
        for item in g_news:
            # GNews dates are strings, need parsing
            try:
                dt = parser.parse(item.get('published date'))
                # Ensure timezone aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc)
            except:
                dt = datetime.datetime.now(datetime.timezone.utc)
            
            articles.append({
                'title': item.get('title'),
                'link': item.get('url'),
                'publisher': item.get('publisher', {}).get('title', 'Google News'),
                'published_at': dt,
                'source': 'Google '
            })
    except Exception as e:
         print(f"GNews error for {ticker}: {e}")
    return articles

def fetch_finviz_news(ticker):
    """Fetches news from FinViz."""
    articles = []
    try:
        fv = finvizfinance(ticker)
        news_df = fv.ticker_news()
        # Returns a dataframe with 'Date', 'Title', 'Link'
        # Date is string like 'Dec-10-24 09:30AM'
        
        # Limit to top 5 recent
        for index, row in news_df.head(5).iterrows():
            date_str = row['Date']
            try:
                # FinViz date format handling
                dt = parser.parse(date_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.timezone.utc) # Approx, strict TZ parsing might fail
            except:
                dt = datetime.datetime.now(datetime.timezone.utc)

            articles.append({
                'title': row['Title'],
                'link': row['Link'],
                'publisher': 'FinViz',
                'published_at': dt,
                'source': 'FinViz'
            })
    except Exception as e:
        print(f"FinViz error for {ticker}: {e}")
    return articles

def get_aggregated_news(ticker):
    """Fetches news from all sources, dedupes, and filters by 24h."""
    all_news = []
    
    # Fetch in parallel could be better but keeping it simple/sequential for reliability
    all_news.extend(fetch_yfinance_news(ticker))
    all_news.extend(fetch_gnews(ticker))
    all_news.extend(fetch_finviz_news(ticker))
    
    # Deduplication
    seen_titles = set()
    unique_news = []
    
    # Sort by date first to keep the newest version of a duplicate? 
    # Or just keep the first one found?
    # Let's sort all by date descending
    all_news.sort(key=lambda x: x['published_at'], reverse=True)
    
    for article in all_news:
        norm_title = normalize_title(article['title'])
        # Simple fuzzy match or startswith could be better, but exact match of normalized title is safe
        if norm_title not in seen_titles:
            seen_titles.add(norm_title)
            unique_news.append(article)
            
    # Filter last 24h
    recent_news = []
    now = datetime.datetime.now(datetime.timezone.utc)
    for article in unique_news:
        if (now - article['published_at']) < datetime.timedelta(hours=24):
            recent_news.append(article)
            
    return recent_news, unique_news

def classify_news(article):
    """
    Classifies news into 'Announcements' or 'Media News'.
    Rules for Announcements:
    1. Publisher in {PR Newswire, Business Wire, GlobeNewswire, Accesswire, SEC.gov}
    2. Title contains {8-K, 10-Q, 10-K, Form 4, Schedule 13G}
    """
    announcement_publishers = {
        "PR Newswire", "Business Wire", "GlobeNewswire", "Accesswire", "SEC.gov"
    }
    announcement_keywords = {
        "8-K", "10-Q", "10-K", "Form 4", "Schedule 13G"
    }

    publisher = str(article.get('publisher', '')).strip()
    title = str(article.get('title', '')).strip()

    # Rule 1: Publisher check
    # Check if any part of the publisher string matches our set (sometimes "PR Newswire via Yahoo")
    if any(pub.lower() in publisher.lower() for pub in announcement_publishers):
        return "Announcements"
        
    # Rule 2: Title check
    if any(kw.lower() in title.lower() for kw in announcement_keywords):
        return "Announcements"
        
    return "Media News"


# --- Main App ---

def main():
    st.set_page_config(page_title="US Stock Briefing", layout="wide")

    # --- Sidebar: Configure Watchlist ---
    st.sidebar.header("Manage Watchlist")
    
    new_ticker = st.sidebar.text_input("Add Ticker (e.g., NVDA)").upper().strip()
    if st.sidebar.button("Add"):
        if new_ticker:
            tickers = load_watchlist()
            if new_ticker not in tickers:
                tickers.append(new_ticker)
                save_watchlist(tickers)
                st.sidebar.success(f"Added {new_ticker}")
                st.rerun()
            else:
                st.sidebar.warning("Ticker already in watchlist")

    uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file, header=None)
            new_tickers = df_upload[0].dropna().astype(str).str.upper().tolist()
            existing_tickers = load_watchlist()
            combined = sorted(list(set(existing_tickers + new_tickers)))
            save_watchlist(combined)
            st.sidebar.success(f"Imported {len(new_tickers)} tickers")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")

    st.sidebar.subheader("Current Watchlist")
    watchlist = load_watchlist()
    
    if watchlist:
        ticker_to_delete = st.sidebar.selectbox("Select to Delete", ["Select..."] + watchlist)
        if ticker_to_delete != "Select...":
            if st.sidebar.button("Delete"):
                watchlist.remove(ticker_to_delete)
                save_watchlist(watchlist)
                st.sidebar.success(f"Deleted {ticker_to_delete}")
                st.rerun()
    else:
        st.sidebar.info("Watchlist is empty.")

    # --- Sidebar: Saved Articles ---
    st.sidebar.divider()
    st.sidebar.subheader("📂 Saved Articles")
    
    bookmarks = load_bookmarks()
    if bookmarks:
        # Group by Ticker for better display
        bookmarks_by_ticker = {}
        for b in bookmarks:
            t = b['Ticker']
            if t not in bookmarks_by_ticker:
                bookmarks_by_ticker[t] = []
            bookmarks_by_ticker[t].append(b)
        
        for ticker, items in bookmarks_by_ticker.items():
            with st.sidebar.expander(f"{ticker} ({len(items)})"):
                for i, item in enumerate(items):
                    st.sidebar.markdown(f"[{item['Title']}]({item['URL']})")
                    if st.sidebar.button("🗑️ Remove", key=f"del_{i}_{item['URL']}"):
                        remove_bookmark(item['URL'])
                        st.rerun()
    else:
        st.sidebar.caption("No saved articles yet.")


    # --- Main Page ---
    
    now_shanghai = datetime.datetime.now(TZ_SHANGHAI)
    st.title(f"🇺🇸 US Stock Daily Briefing")
    st.markdown(f"**Current Time (GMT+8):** {now_shanghai.strftime('%Y-%m-%d %H:%M:%S')}")
    st.divider()

    if not watchlist:
        st.info("Add stocks to sidebar to see the dashboard.")
        return

    # Check for new dependencies
    try:
        import gnews
        import finvizfinance
    except ImportError:
        st.error("Missing libraries: `gnews` or `finvizfinance`. Please install them.")
        return

    st.header("📰 Daily Briefing (Last 24h)")
    
    # Combined Data Loading
    with st.spinner('Fetching aggregated news from Yahoo, Google, and FinViz...'):
        dashboard_data = [] # List of (ticker, price_data, recent_news, all_news)
        
        for ticker in watchlist:
            price_data = get_stock_price_data(ticker)
            recent_news, all_news_items = get_aggregated_news(ticker)
            
            # Classify news
            announcements = []
            media_news = []
            for news in recent_news:
                category = classify_news(news)
                if category == "Announcements":
                    announcements.append(news)
                else:
                    media_news.append(news)
            
            dashboard_data.append({
                'ticker': ticker,
                'price': price_data,
                'announcements': announcements,
                'media_news': media_news,
                'all': all_news_items
            })

    # Briefing Section
    recent_found = False
    
    # We will show tabs for each stock? Or tabs for the whole section? 
    # User requirement: "Display a prominent 'Daily Briefing' section."
    # Let's break it down by Stock, then inside each stock, tabs for Announcements vs Media.
    
    for item in dashboard_data:
        has_news = item['announcements'] or item['media_news']
        if has_news:
            recent_found = True
            with st.expander(f"**{item['ticker']}**: {len(item['announcements']) + len(item['media_news'])} New Articles", expanded=True):
                
                tab1, tab2 = st.tabs(["📢 Official Announcements", "🗞️ Media News"])
                
                with tab1:
                    if item['announcements']:
                        for news in item['announcements']:
                            # Color code source
                            source_color = "blue"
                            if news['source'] == 'Yahoo': source_color = "violet"
                            elif news['source'] == 'FinViz': source_color = "orange"
                            
                            col1, col2 = st.columns([0.85, 0.15])
                            with col1:
                                st.markdown(f":{source_color}[[{news['source']}]] [{news['title']}]({news['link']}) - *{news['publisher']}*")
                            with col2:
                                if st.button("⭐ Save", key=f"save_ann_{item['ticker']}_{news['link']}"):
                                    save_bookmark(news, item['ticker'], "Announcement")
                                    st.rerun()
                    else:
                        st.caption("No official announcements in the last 24h.")
                
                with tab2:
                    if item['media_news']:
                        for news in item['media_news']:
                            # Color code source
                            source_color = "blue"
                            if news['source'] == 'Yahoo': source_color = "violet"
                            elif news['source'] == 'FinViz': source_color = "orange"
                            
                            col1, col2 = st.columns([0.85, 0.15])
                            with col1:
                                st.markdown(f":{source_color}[[{news['source']}]] [{news['title']}]({news['link']}) - *{news['publisher']}*")
                            with col2:
                                if st.button("⭐ Save", key=f"save_med_{item['ticker']}_{news['link']}"):
                                    save_bookmark(news, item['ticker'], "Media News")
                                    st.rerun()
                    else:
                        st.caption("No media news in the last 24h.")

    if not recent_found:
        st.info("No significant news found in the last 24 hours.")

    st.divider()

    # Stock Cards
    st.header("📈 Market Overview")
    cols = st.columns(3)
    
    for idx, item in enumerate(dashboard_data):
        col = cols[idx % 3]
        price = item['price']
        ticker = item['ticker']
        
        with col:
            if price:
                delta_str = f"{price['change']:.2f} ({price['pct_change']:.2f}%)"
                st.metric(label=ticker, value=f"${price['current_price']:.2f}", delta=delta_str)
            else:
                st.metric(label=ticker, value="N/A", delta="Error")
            
            with st.expander("All Latest News"):
                for news in item['all'][:5]:
                    st.markdown(f"**[{news['source']}]** [{news['title']}]({news['link']})")

if __name__ == "__main__":
    main()
