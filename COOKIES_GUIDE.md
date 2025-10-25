# TikTok Cookies Authentication Guide

## Why Use Cookies?

TikTok implements anti-scraping measures that may block unauthenticated requests. Using cookies from an authenticated browser session can help:

- ✅ Bypass rate limiting
- ✅ Access age-restricted content
- ✅ Reduce HTTP 403 errors
- ✅ Access private/restricted accounts (if you have permission)

## How to Export Cookies

### Method 1: Browser Extension (Recommended)

#### Chrome/Edge
1. Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Log into TikTok (https://www.tiktok.com)
3. Click the extension icon
4. Save as `cookies.txt`

#### Firefox
1. Install [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
2. Log into TikTok (https://www.tiktok.com)
3. Click the extension icon
4. Export and save as `cookies.txt`

### Method 2: Manual Export (Advanced)

#### Chrome DevTools
1. Open TikTok (https://www.tiktok.com)
2. Press F12 to open DevTools
3. Go to Application tab → Cookies → https://www.tiktok.com
4. Right-click → Copy all cookies
5. Convert to Netscape format manually (not recommended)

## Using Cookies with the Transcriber

### Single Account
```bash
python scripts/ingest_account.py --user kwrt_ --cookies cookies.txt
```

### Batch Ingestion
```bash
python scripts/batch_ingest.py --users kwrt_ matrix.v5 --cookies cookies.txt
```

### Environment Variable
You can also set it in `.env`:
```
COOKIES_FILE=cookies.txt
```

## Cookies.txt Format

The file should be in Netscape HTTP Cookie File format:

```
# Netscape HTTP Cookie File
.tiktok.com	TRUE	/	FALSE	1234567890	cookie_name	cookie_value
```

## Security Best Practices

⚠️ **IMPORTANT**: Cookies are sensitive credentials!

- ✅ **Never commit cookies.txt to git** (already in .gitignore)
- ✅ Store cookies.txt outside the project directory
- ✅ Use environment-specific cookie files
- ✅ Regenerate cookies periodically (they expire)
- ✅ Don't share your cookies.txt file

## Troubleshooting

### Cookies Not Working
- ✅ Make sure you're logged into TikTok before exporting
- ✅ Check the cookies.txt format is correct (Netscape format)
- ✅ Try re-exporting fresh cookies
- ✅ Clear browser cache and log in again

### Still Getting 403 Errors
- ✅ Cookies may have expired - export new ones
- ✅ TikTok may have rate-limited your IP
- ✅ Try using a VPN or different network
- ✅ Wait a few hours before retrying

### Permission Errors
- ✅ Ensure cookies.txt has read permissions: `chmod 600 cookies.txt`
- ✅ Check the file path is correct

## Alternative: Session Tokens

Some users prefer using session tokens directly:

```bash
# Export specific cookie values
export TIKTOK_SESSION="your_session_token_here"
```

However, the cookies.txt file approach is more reliable as it includes all necessary cookies.

## Cookie Lifespan

- TikTok cookies typically last **30 days**
- You'll need to re-export when they expire
- Signs of expired cookies:
  - HTTP 401/403 errors
  - "Authentication required" messages
  - Reduced video access

## Legal & Ethical Considerations

⚠️ **Disclaimer**: 

- Only scrape public TikTok content
- Respect robots.txt and TikTok's Terms of Service
- Don't scrape private accounts without permission
- Use reasonable rate limits to avoid overloading servers
- This tool is for educational/research purposes

## Need Help?

If you're still having issues:

1. Check the error logs: `tiktok_transcriber.log`
2. Try running with `--verbose` flag
3. Test with a small number of videos first: `--max-videos 3`
4. Verify cookies.txt is in Netscape format

## Quick Start Example

```bash
# 1. Export cookies from browser (use extension)
# 2. Save as cookies.txt in project root
# 3. Run with cookies
python scripts/ingest_account.py --user kwrt_ --cookies cookies.txt --max-videos 5

# Success! You should see fewer 403 errors
```


