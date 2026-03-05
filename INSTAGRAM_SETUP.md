# Northern Dial Instagram Post Generator

Automatically creates Instagram carousel posts every 5 songs played on Northern Dial Radio.

## 🎵 What It Does

- **Monitors** your AzuraCast API every hour
- **Tracks** songs as they play
- **Generates** Instagram carousel posts (5 album covers + caption) automatically
- **Saves** posts to `instagram-posts/` folder for you to review and upload

## 📦 Setup Instructions

### 1. Add Files to Your Repository

Copy these files to your Northern Dial GitHub repository:

```
your-repo/
├── instagram_generator.py          # Main script
├── .github/
│   └── workflows/
│       └── instagram-generator.yml # GitHub Actions workflow
└── instagram_state.json            # Will be auto-created (tracks progress)
```

**File locations:**
- `instagram_generator.py` → Root of your repo
- `instagram-generator.yml` → `.github/workflows/instagram-generator.yml`

### 2. Commit and Push

```bash
git add instagram_generator.py .github/workflows/instagram-generator.yml
git commit -m "Add Instagram post generator"
git push
```

That's it! GitHub Actions will now run automatically every hour.

## 🚀 How It Works

### Automatic Schedule
- Runs **every hour** (on the hour: 12:00, 1:00, 2:00, etc.)
- Checks if a new song is playing
- Tracks up to 5 songs
- When 5 songs are reached, generates a post

### Manual Trigger
You can also run it manually:
1. Go to your GitHub repo
2. Click **Actions** tab
3. Click **Instagram Post Generator**
4. Click **Run workflow** button

## 📁 Generated Posts

Posts are saved in `instagram-posts/` with this structure:

```
instagram-posts/
└── post_001_20260304_143022/
    ├── image_1.jpg          # Album cover for song 1
    ├── image_2.jpg          # Album cover for song 2
    ├── image_3.jpg          # Album cover for song 3
    ├── image_4.jpg          # Album cover for song 4
    ├── image_5.jpg          # Album cover for song 5
    ├── caption.txt          # Pre-written caption
    └── post_info.json       # Full post metadata
```

## 📸 How to Post to Instagram

### Option 1: Manual Upload (Easiest)
1. Check your repo's `instagram-posts/` folder for new posts
2. Download the 5 images
3. Open Instagram app → Create → Carousel
4. Upload the 5 images in order
5. Copy/paste the caption from `caption.txt`
6. Post!

### Option 2: Desktop Upload
1. Use Instagram web (requires Chrome + browser extension)
2. Same process as above

### Option 3: Scheduling Tool (Recommended)
Use Buffer, Later, or Hootsuite:
1. Import the 5 images
2. Paste the caption
3. Schedule for optimal posting time
4. Let it auto-post

## 🎨 Customization

### Change Posting Frequency

Edit `instagram_generator.py`:
```python
SONGS_PER_POST = 5  # Change to 10 for every 10 songs
```

### Change Schedule

Edit `.github/workflows/instagram-generator.yml`:
```yaml
schedule:
  - cron: '0 * * * *'  # Every hour
  # - cron: '0 */2 * * *'  # Every 2 hours
  # - cron: '0 9,15,21 * * *'  # 9am, 3pm, 9pm only
```

### Change Caption Format

Edit the `generate_caption()` function in `instagram_generator.py`:
```python
def generate_caption(songs):
    caption = "🎵 YOUR CUSTOM TEXT HERE\n\n"
    # ... customize as needed
```

### Change Hashtags

Edit the hashtags at the end of `generate_caption()` function.

## 🔔 Add Notifications (Optional)

### Email Notification

Add to `.github/workflows/instagram-generator.yml` after the "Create notification" step:

```yaml
- name: Send Email Notification
  if: success()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{secrets.MAIL_USERNAME}}
    password: ${{secrets.MAIL_PASSWORD}}
    subject: New Instagram Post Ready!
    to: your-email@example.com
    from: Northern Dial Bot
    body: A new Instagram post is ready in the instagram-posts folder!
```

### Discord Webhook

```yaml
- name: Discord Notification
  if: success()
  uses: tsickert/discord-webhook@v5.3.0
  with:
    webhook-url: ${{ secrets.DISCORD_WEBHOOK }}
    content: "🎵 New Instagram post ready! Check the repo."
```

## 📊 Monitoring

### Check Action Status
1. Go to **Actions** tab in your GitHub repo
2. See all workflow runs
3. Click on any run to see detailed logs

### View Generated Posts
- Browse `instagram-posts/` folder in your repo
- Each post gets a timestamped folder

## ⚙️ Configuration

### State File (`instagram_state.json`)

Automatically created and updated. Contains:
```json
{
  "tracked_songs": [...],  // Current songs being tracked
  "last_song_id": "...",   // Last song seen
  "post_count": 5          // Total posts generated
}
```

Don't delete this file - it tracks progress between runs!

## 🐛 Troubleshooting

### "No changes to commit"
- Normal! Means no new song played since last check
- Script only generates posts when 5 NEW songs have played

### Action failing?
- Check the Actions tab for error logs
- Make sure the files are in the correct locations
- Verify AzuraCast API is accessible

### Missing album art?
- Script creates Northern Dial branded placeholders automatically
- No action needed from you

## 🎯 Future Enhancements

Want to add auto-posting? You can integrate:
- Instagram Graph API (requires Facebook Business account)
- Buffer API
- Later API
- Hootsuite API

Let me know if you want help setting this up!

## 📝 Notes

- GitHub Actions has 2,000 free minutes/month (this uses ~1 min/hour = ~720 min/month)
- Plenty of headroom for a radio station!
- All posts are saved in your repo forever (unless you delete them)

---

**Questions?** Open an issue or reach out!

🎵 All Killer, All CanCon 🍁
