#!/usr/bin/env python3

Northern Dial Instagram Post Generator
Monitors AzuraCast API and generates Instagram carousel posts every 5 songs


import os
import json
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Configuration

AZURACAST_API = “https://a10.asurahosting.com/api/nowplaying/northern_dial”
STATE_FILE = “instagram_state.json”
OUTPUT_DIR = “instagram-posts”
SONGS_PER_POST = 5

# Instagram optimal size

IMG_SIZE = 1080

def load_state():
“”“Load the current state (songs tracked, last song ID, etc.)”””
if os.path.exists(STATE_FILE):
with open(STATE_FILE, ‘r’) as f:
return json.load(f)
return {
“tracked_songs”: [],
“last_song_id”: None,
“post_count”: 0
}

def save_state(state):
“”“Save the current state”””
with open(STATE_FILE, ‘w’) as f:
json.dump(state, f, indent=2)

def fetch_current_song():
“”“Fetch currently playing song from AzuraCast”””
try:
response = requests.get(AZURACAST_API, timeout=10)
response.raise_for_status()
data = response.json()

    if 'now_playing' in data and 'song' in data['now_playing']:
        song = data['now_playing']['song']
        return {
            'id': song.get('id'),
            'title': song.get('title', 'Unknown Title'),
            'artist': song.get('artist', 'Unknown Artist'),
            'art': song.get('art', ''),
            'timestamp': datetime.now().isoformat()
        }
except Exception as e:
    print(f"Error fetching current song: {e}")
return None

def download_album_art(url, song_index):
“”“Download and resize album art to Instagram size”””
try:
if not url or url.startswith(‘data:’):
# No art or data URL - create placeholder
return create_placeholder_art(song_index)

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    img = Image.open(BytesIO(response.content))
    img = img.convert('RGB')
    img = img.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.LANCZOS)
    
    return img
except Exception as e:
    print(f"Error downloading art from {url}: {e}")
    return create_placeholder_art(song_index)

def create_placeholder_art(song_index):
“”“Create a placeholder image with Northern Dial branding”””
img = Image.new(‘RGB’, (IMG_SIZE, IMG_SIZE), color=’#1a1a1a’)
draw = ImageDraw.Draw(img)

# Add gradient effect (simple vertical gradient)
for y in range(IMG_SIZE):
    shade = int(26 + (y / IMG_SIZE) * 20)  # 26 to 46
    color = (shade, shade, shade)
    draw.line([(0, y), (IMG_SIZE, y)], fill=color)

# Draw red circle for music note
circle_size = 300
circle_pos = (IMG_SIZE//2 - circle_size//2, IMG_SIZE//2 - circle_size//2)
draw.ellipse([circle_pos, (circle_pos[0] + circle_size, circle_pos[1] + circle_size)],
             fill='#C33', outline='#ff6666', width=5)

# Add "Northern Dial" text
try:
    # Try to use a nice font, fallback to default
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
except:
    font = ImageFont.load_default()

text = "Northern Dial"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]

draw.text(((IMG_SIZE - text_width) // 2, IMG_SIZE // 2 - text_height // 2),
          text, fill='white', font=font)

return img

def generate_caption(songs):
“”“Generate Instagram caption”””
caption = “🎵 RECENTLY PLAYED ON NORTHERN DIAL\n\n”

for i, song in enumerate(songs, 1):
    caption += f"{i}. {song['artist']} - \"{song['title']}\"\n"

caption += "\nAll Killer, All CanCon 🍁\n"
caption += "Tune in: northerndial.ca\n\n"
caption += "#CanadianMusic #IndieRadio #CanCon #NorthernDial #DiscoverMusic"

return caption

def create_instagram_post(songs, post_count):
“”“Create Instagram post (images + caption)”””
os.makedirs(OUTPUT_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
post_dir = os.path.join(OUTPUT_DIR, f"post_{post_count:03d}_{timestamp}")
os.makedirs(post_dir, exist_ok=True)

# Download and save album art for each song
print(f"\nGenerating Instagram post #{post_count}...")
for i, song in enumerate(songs, 1):
    print(f"  Processing {i}/5: {song['artist']} - {song['title']}")
    img = download_album_art(song['art'], i)
    img_path = os.path.join(post_dir, f"image_{i}.jpg")
    img.save(img_path, "JPEG", quality=95)

# Generate and save caption
caption = generate_caption(songs)
caption_path = os.path.join(post_dir, "caption.txt")
with open(caption_path, 'w', encoding='utf-8') as f:
    f.write(caption)

# Create a summary JSON
summary = {
    "post_number": post_count,
    "created_at": datetime.now().isoformat(),
    "songs": songs,
    "caption": caption,
    "images": [f"image_{i}.jpg" for i in range(1, 6)]
}

summary_path = os.path.join(post_dir, "post_info.json")
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2)

print(f"✅ Post created: {post_dir}")
print(f"   Images: 5 album covers")
print(f"   Caption: {caption_path}")

return post_dir

def main():
“”“Main execution”””
print(”=” * 60)
print(“Northern Dial Instagram Post Generator”)
print(”=” * 60)

# Load current state
state = load_state()
print(f"\nCurrent state:")
print(f"  Tracked songs: {len(state['tracked_songs'])}/5")
print(f"  Posts generated: {state['post_count']}")

# Fetch current song
current_song = fetch_current_song()
if not current_song:
    print("\n⚠️  Could not fetch current song. Exiting.")
    return

print(f"\nNow playing:")
print(f"  {current_song['artist']} - {current_song['title']}")

# Check if this is a new song
if current_song['id'] == state['last_song_id']:
    print("  (Same as last check - no update needed)")
    return

# New song! Add to tracked songs
state['tracked_songs'].append(current_song)
state['last_song_id'] = current_song['id']

print(f"\n✅ New song tracked! ({len(state['tracked_songs'])}/5)")

# Check if we have 5 songs
if len(state['tracked_songs']) >= SONGS_PER_POST:
    # Generate post
    songs_for_post = state['tracked_songs'][:SONGS_PER_POST]
    state['post_count'] += 1
    
    post_dir = create_instagram_post(songs_for_post, state['post_count'])
    
    # Reset tracked songs (keep overflow if any)
    state['tracked_songs'] = state['tracked_songs'][SONGS_PER_POST:]
    
    print(f"\n🎉 POST READY FOR INSTAGRAM!")
    print(f"   Location: {post_dir}")
    print(f"   Upload the 5 images as a carousel")
    print(f"   Copy caption from caption.txt")

# Save state
save_state(state)
print("\n" + "=" * 60)

if **name** == “**main**”:
main()