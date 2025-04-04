import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from ttkthemes import ThemedTk
import threading
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from textblob import TextBlob
import json
import os
from datetime import datetime
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_scraper.log'),
        logging.StreamHandler()
    ]
)

class TwitterScraper:
    def __init__(self):
        self.driver = None
        self.is_running = False
        self.config = self.load_config()
        self.setup_database()

    def setup_database(self):
        self.conn = sqlite3.connect('scraper.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_data (
                id INTEGER PRIMARY KEY,
                username TEXT,
                tweet_text TEXT,
                sentiment REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def load_config(self):
        if os.path.exists('scraper_config.json'):
            with open('scraper_config.json', 'r') as f:
                return json.load(f)
        return {
            'delay_min': 2,
            'delay_max': 5,
            'max_retries': 3,
            'proxy_enabled': False,
            'proxies': [],
            'max_tweets': 100,
            'save_images': False,
            'save_videos': False
        }

    def save_config(self):
        with open('scraper_config.json', 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_driver(self):
        if self.driver is not None:
            return
            
        try:
            options = Options()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_experimental_option("excludeSwitches", ["enable-logging"])
            
            if self.config['proxy_enabled'] and self.config['proxies']:
                proxy = random.choice(self.config['proxies'])
                options.add_argument(f'--proxy-server={proxy}')
            
            # Try multiple methods to initialize ChromeDriver
            try:
                # Method 1: Using ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                logging.info("ChromeDriver initialized successfully using ChromeDriverManager")
            except Exception as e:
                logging.warning(f"ChromeDriverManager failed: {str(e)}")
                try:
                    # Method 2: Using local chromedriver.exe
                    driver_path = os.path.join(os.getcwd(), "chromedriver.exe")
                    if os.path.exists(driver_path):
                        service = Service(executable_path=driver_path)
                        self.driver = webdriver.Chrome(service=service, options=options)
                        logging.info("ChromeDriver initialized successfully using local driver")
                    else:
                        # Method 3: Basic initialization
                        self.driver = webdriver.Chrome(options=options)
                        logging.info("ChromeDriver initialized successfully using basic method")
                except Exception as e:
                    logging.error(f"All ChromeDriver initialization methods failed: {str(e)}")
                    raise
        except Exception as e:
            logging.error(f"Error setting up ChromeDriver: {str(e)}")
            raise

    def login(self, username, password):
        try:
            if self.driver is None:
                self.setup_driver()
                
            self.driver.get("https://twitter.com/i/flow/login")
            wait = WebDriverWait(self.driver, 30)

            # Handle username
            username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
            username_field.send_keys(username)
            time.sleep(random.uniform(1, 2))
            
            next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[role="button"].r-13qz1uu')))
            next_button.click()
            time.sleep(random.uniform(1, 2))

            # Handle password
            password_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
            password_field.send_keys(password)
            time.sleep(random.uniform(1, 2))
            
            login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="LoginForm_Login_Button"]')))
            login_button.click()

            # Verify login
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="AppTabBar_Home_Link"]')))
            logging.info(f"Successfully logged in as {username}")
            return True
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def scrape_tweets(self, username, num_tweets, callback=None):
        try:
            self.driver.get(f"https://twitter.com/{username}")
            wait = WebDriverWait(self.driver, 10)

            tweet_texts = []
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while len(tweet_texts) < num_tweets and self.is_running:
                tweets = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//article[@data-testid="tweet"]//div[@lang]')))
                for tweet in tweets:
                    if not self.is_running:
                        break
                    tweet_text = tweet.text
                    if tweet_text not in tweet_texts:
                        tweet_texts.append(tweet_text)
                        sentiment = TextBlob(tweet_text).sentiment.polarity
                        self.save_to_database(username, tweet_text, sentiment)
                        if callback:
                            callback(f"Found tweet: {tweet_text[:50]}...")
                        if len(tweet_texts) >= num_tweets:
                            break

                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 4))
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            return tweet_texts[:num_tweets]
        except Exception as e:
            logging.error(f"Error scraping tweets: {str(e)}")
            return []

    def save_to_database(self, username, tweet_text, sentiment):
        self.cursor.execute(
            "INSERT INTO scraped_data (username, tweet_text, sentiment) VALUES (?, ?, ?)",
            (username, tweet_text, sentiment)
        )
        self.conn.commit()

    def get_scraping_stats(self):
        self.cursor.execute("SELECT COUNT(*) FROM scraped_data")
        total_tweets = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT AVG(sentiment) FROM scraped_data")
        avg_sentiment = self.cursor.fetchone()[0]
        return total_tweets, avg_sentiment

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
        if self.conn:
            self.conn.close()

class TwitterScraperGUI(ThemedTk):
    def __init__(self):
        super().__init__()
        self.title("Twitter Scraper Pro")
        self.geometry("1000x800")
        self.set_theme("arc")
        
        self.scraper = TwitterScraper()
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.main_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.analytics_tab = ttk.Frame(self.notebook)
        self.accounts_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.main_tab, text="Main")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.analytics_tab, text="Analytics")
        self.notebook.add(self.accounts_tab, text="Accounts")

        # Create tab contents
        self.create_main_tab()
        self.create_settings_tab()
        self.create_analytics_tab()
        self.create_accounts_tab()

    def create_main_tab(self):
        # Login section
        ttk.Label(self.main_tab, text="Twitter Login", font=("Arial", 12, "bold")).pack(pady=5)
        
        login_frame = ttk.Frame(self.main_tab)
        login_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Username:").pack(side=tk.LEFT)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(login_frame, text="Password:").pack(side=tk.LEFT)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.pack(side=tk.LEFT, padx=5)

        # Scraping options
        ttk.Label(self.main_tab, text="\nScraping Options", font=("Arial", 12, "bold")).pack()
        
        options_frame = ttk.Frame(self.main_tab)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.scrape_type = tk.StringVar(value="tweets")
        ttk.Radiobutton(options_frame, text="User Tweets", variable=self.scrape_type, value="tweets").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(options_frame, text="Hashtag Tweets", variable=self.scrape_type, value="hashtag").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(options_frame, text="Following", variable=self.scrape_type, value="following").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(options_frame, text="Media", variable=self.scrape_type, value="media").pack(side=tk.LEFT, padx=5)

        # Target and number of items
        target_frame = ttk.Frame(self.main_tab)
        target_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(target_frame, text="Target:").pack(side=tk.LEFT)
        self.target_entry = ttk.Entry(target_frame)
        self.target_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(target_frame, text="Number of items:").pack(side=tk.LEFT)
        self.num_items_entry = ttk.Entry(target_frame)
        self.num_items_entry.pack(side=tk.LEFT, padx=5)

        # Control buttons
        control_frame = ttk.Frame(self.main_tab)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(control_frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop Scraping", command=self.stop_scraping, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(self.main_tab, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        # Status and output
        self.status_label = ttk.Label(self.main_tab, text="Status: Ready")
        self.status_label.pack()

        self.output_text = scrolledtext.ScrolledText(self.main_tab, height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_settings_tab(self):
        # Delay settings
        ttk.Label(self.settings_tab, text="Delay Settings", font=("Arial", 12, "bold")).pack(pady=5)
        
        delay_frame = ttk.Frame(self.settings_tab)
        delay_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(delay_frame, text="Minimum Delay (seconds):").pack(side=tk.LEFT)
        self.min_delay_entry = ttk.Entry(delay_frame)
        self.min_delay_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(delay_frame, text="Maximum Delay (seconds):").pack(side=tk.LEFT)
        self.max_delay_entry = ttk.Entry(delay_frame)
        self.max_delay_entry.pack(side=tk.LEFT, padx=5)

        # Proxy settings
        ttk.Label(self.settings_tab, text="\nProxy Settings", font=("Arial", 12, "bold")).pack()
        
        self.proxy_var = tk.BooleanVar(value=self.scraper.config['proxy_enabled'])
        ttk.Checkbutton(self.settings_tab, text="Enable Proxies", variable=self.proxy_var).pack(pady=5)

        proxy_frame = ttk.Frame(self.settings_tab)
        proxy_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(proxy_frame, text="Proxies (ip:port:username:password):").pack()
        self.proxies_text = tk.Text(proxy_frame, height=5)
        self.proxies_text.pack(fill=tk.X, padx=5)
        for proxy in self.scraper.config['proxies']:
            self.proxies_text.insert(tk.END, proxy + "\n")

        # Save settings button
        ttk.Button(self.settings_tab, text="Save Settings", command=self.save_settings).pack(pady=10)

    def create_analytics_tab(self):
        # Statistics
        ttk.Label(self.analytics_tab, text="Scraping Statistics", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.total_tweets_label = ttk.Label(self.analytics_tab, text="Total Tweets Scraped: 0")
        self.total_tweets_label.pack()
        
        self.avg_sentiment_label = ttk.Label(self.analytics_tab, text="Average Sentiment: 0.00")
        self.avg_sentiment_label.pack()

        # Export buttons
        ttk.Button(self.analytics_tab, text="Export Tweets", command=self.export_tweets).pack(pady=5)
        ttk.Button(self.analytics_tab, text="Export Sentiments", command=self.export_sentiments).pack(pady=5)

    def create_accounts_tab(self):
        # Account management
        ttk.Label(self.accounts_tab, text="Account Management", font=("Arial", 12, "bold")).pack(pady=5)
        
        self.accounts_text = tk.Text(self.accounts_tab, height=10)
        self.accounts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(self.accounts_tab, text="Add Account", command=self.add_account).pack(pady=5)
        ttk.Button(self.accounts_tab, text="Remove Account", command=self.remove_account).pack(pady=5)

    def load_config(self):
        self.min_delay_entry.delete(0, tk.END)
        self.min_delay_entry.insert(0, str(self.scraper.config['delay_min']))
        self.max_delay_entry.delete(0, tk.END)
        self.max_delay_entry.insert(0, str(self.scraper.config['delay_max']))
        self.proxy_var.set(self.scraper.config['proxy_enabled'])
        self.proxies_text.delete(1.0, tk.END)
        for proxy in self.scraper.config['proxies']:
            self.proxies_text.insert(tk.END, proxy + "\n")

    def save_settings(self):
        try:
            self.scraper.config['delay_min'] = float(self.min_delay_entry.get())
            self.scraper.config['delay_max'] = float(self.max_delay_entry.get())
            self.scraper.config['proxy_enabled'] = self.proxy_var.get()
            self.scraper.config['proxies'] = [line.strip() for line in self.proxies_text.get(1.0, tk.END).split('\n') if line.strip()]
            self.scraper.save_config()
            messagebox.showinfo("Success", "Settings saved successfully")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for delays")

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)

    def start_scraping(self):
        if self.scraper.is_running:
            messagebox.showwarning("Warning", "Scraper is already running")
            return

        username = self.username_entry.get()
        password = self.password_entry.get()
        target = self.target_entry.get()
        num_items = int(self.num_items_entry.get() or 10)
        scrape_type = self.scrape_type.get()

        if not username or not password or not target:
            messagebox.showerror("Error", "Please fill all required fields")
            return

        self.scraper.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress["value"] = 0
        
        threading.Thread(target=self.run_scraping, args=(username, password, target, num_items, scrape_type)).start()

    def stop_scraping(self):
        self.scraper.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Scraping stopped by user")
        if self.scraper.driver:
            self.scraper.driver.quit()
            self.scraper.driver = None

    def run_scraping(self, username, password, target, num_items, scrape_type):
        try:
            if self.scraper.login(username, password):
                self.update_status("Logged in successfully")
                
                if scrape_type == "tweets":
                    tweets = self.scraper.scrape_tweets(target, num_items, self.update_status)
                    if tweets:
                        self.update_status(f"Scraped {len(tweets)} tweets")
                        self.update_analytics()
                
                elif scrape_type == "hashtag":
                    # Implement hashtag scraping
                    pass
                
                elif scrape_type == "following":
                    # Implement following scraping
                    pass
                
                elif scrape_type == "media":
                    # Implement media scraping
                    pass
            else:
                self.update_status("Login failed")
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        finally:
            self.scraper.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_status("Scraping completed")
            if self.scraper.driver:
                self.scraper.driver.quit()
                self.scraper.driver = None

    def update_analytics(self):
        total_tweets, avg_sentiment = self.scraper.get_scraping_stats()
        self.total_tweets_label.config(text=f"Total Tweets Scraped: {total_tweets}")
        self.avg_sentiment_label.config(text=f"Average Sentiment: {avg_sentiment:.2f}")

    def export_tweets(self):
        self.cursor.execute("SELECT tweet_text FROM scraped_data")
        tweets = self.cursor.fetchall()
        with open("exported_tweets.txt", "w", encoding="utf-8") as f:
            for tweet in tweets:
                f.write(f"{tweet[0]}\n")
        messagebox.showinfo("Success", "Tweets exported successfully")

    def export_sentiments(self):
        self.cursor.execute("SELECT sentiment FROM scraped_data")
        sentiments = self.cursor.fetchall()
        with open("exported_sentiments.txt", "w") as f:
            for sentiment in sentiments:
                f.write(f"{sentiment[0]}\n")
        messagebox.showinfo("Success", "Sentiments exported successfully")

    def add_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username and password:
            self.accounts_text.insert(tk.END, f"{username}:{password}\n")
            self.update_status(f"Added account: {username}")

    def remove_account(self):
        selection = self.accounts_text.tag_ranges(tk.SEL)
        if selection:
            self.accounts_text.delete(selection[0], selection[1])
            self.update_status("Removed selected account")

if __name__ == "__main__":
    app = TwitterScraperGUI()
    app.mainloop() 