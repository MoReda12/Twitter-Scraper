# Twitter Scraper Pro

A powerful and user-friendly Twitter scraping application with a modern GUI interface. This tool allows you to scrape tweets, analyze sentiment, and manage multiple Twitter accounts efficiently.

## Features

- **Modern GUI Interface**: User-friendly interface with multiple tabs for different functionalities
- **Multiple Scraping Options**:
  - User tweets
  - Hashtag tweets
  - Following list
  - Media content
- **Advanced Features**:
  - Sentiment analysis
  - Analytics dashboard
  - Export capabilities
- **Security**:
  - Secure credential storage
  - Rate limiting protection

## Requirements

- Python 3.7+
- Chrome browser installed
- Required Python packages (install using `pip install -r requirements.txt`):
  - selenium
  - webdriver_manager
  - ttkthemes
  - textblob
  - tkinter

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd twitter-scraper-pro
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python scraper.py
```

## Usage

### Main Tab
- Enter your Twitter credentials
- Select scraping type (tweets, hashtags, following, or media)
- Enter target username/hashtag
- Set number of items to scrape
- Click "Start Scraping" to begin

### Settings Tab
- Configure delay settings (minimum and maximum delay between actions)
- Enable/disable proxy support
- Add proxy configurations
- Save settings for future use

### Analytics Tab
- View scraping statistics
- Monitor sentiment analysis results
- Export scraped data
- View historical scraping data

### Accounts Tab
- Manage multiple Twitter accounts
- Add/remove accounts
- View account status and history

## Configuration

The application uses a configuration file (`scraper_config.json`) to store settings. You can modify these settings through the GUI or directly in the file:

```json
{
    "delay_min": 2,
    "delay_max": 5,
    "max_retries": 3,
    "proxy_enabled": false,
    "proxies": [],
    "max_tweets": 100,
    "save_images": false,
    "save_videos": false
}
```

## Proxy Configuration

To use proxies, enable them in the settings tab and add your proxy configurations in the format:
```
ip:port:username:password
```

## Database

The application uses SQLite to store scraped data and account information. The database file (`scraper.db`) is automatically created in the application directory.

## Troubleshooting

1. **ChromeDriver Issues**:
   - Make sure you have the latest version of Chrome installed
   - The application will automatically download the correct ChromeDriver version
   - If automatic download fails, you can manually place a compatible chromedriver.exe in the application directory

2. **Login Issues**:
   - Verify your credentials are correct
   - Check if your account has 2FA enabled
   - Ensure your account is not locked or suspended

3. **Scraping Issues**:
   - Adjust delay settings if you're getting rate limited
   - Try using a proxy if your IP is blocked
   - Check if the target account is private

## Security Notes

- Never share your configuration file containing credentials
- Use proxies for anonymity
- Respect Twitter's terms of service and rate limits
- Do not use this tool for malicious purposes

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use it responsibly and in accordance with Twitter's terms of service. The developers are not responsible for any misuse or violations of Twitter's policies. 


contact:
- Email: instamoreda13@gmail.com
- telegram: justmo69
