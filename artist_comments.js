#!/usr/bin/env node
/**
 * Northern Dial — Artist Comment Bot
 * Monitors recently featured artists for new posts,
 * leaves a genuine comment linking back to Northern Dial.
 * 
 * NOTE: Instagram Graph API only allows commenting on your OWN posts
 * or on posts where you're @mentioned. This script uses the Business
 * Discovery API to detect new posts from featured artists, then flags
 * them to you via Telegram so you can comment manually (or from a
 * secondary account not limited by the API).
 * 
 * For fully automated commenting, a third-party tool like ManyChat
 * or a browser automation approach would be needed.
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

const SCRIPT_DIR = path.dirname(__filename);
const cfg = JSON.parse(fs.readFileSync(path.join(SCRIPT_DIR, "config.json")));
const LOG = path.join(SCRIPT_DIR, "comments.log");
const STATE_FILE = path.join(SCRIPT_DIR, "comments_state.json");

const { instagram_token: IG_TOKEN, instagram_account_id: IG_ID } = cfg;
const TELEGRAM_CHAT_ID = cfg.notify_telegram_chat_id;
const TELEGRAM_TOKEN = cfg.telegram_bot_token || null;

// High-value artists to monitor (handles without @)
// Add to this list as you feature more artists
const WATCH_HANDLES = [
  "katietupper", "shantelmay", "pumajune", "_2ndson_", "unotopicmusica",
  "apollobrown", "eterniamc", "maestrofreshwes", "88glam", "melaniefiona",
  "livingthingmusic", "harveystripes", "buck65", "serenaryder", "hedleyband",
  "haileyblakeofficial", "lovxofficial"
];

// Comment templates — rotated to avoid spam detection
const COMMENT_TEMPLATES = [
  "Just spun this on Northern Dial 🍁 CanCon radio done right — northerndial.ca",
  "We play this on Northern Dial! 🎙️ All Canadian, all the time — northerndial.ca",
  "Northern Dial approved 🍁 Catch this on our CanCon stream — northerndial.ca",
  "This one's in rotation on Northern Dial 📻 northerndial.ca",
  "Love this! Been spinning it on Northern Dial 🍁 — northerndial.ca",
];

function log(msg) {
  const ts = new Date().toISOString().replace("T", " ").slice(0, 19);
  const line = `[${ts}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG, line + "\n");
}

function loadState() {
  if (fs.existsSync(STATE_FILE)) return JSON.parse(fs.readFileSync(STATE_FILE));
  return { seenPosts: {}, lastChecked: {} };
}
function saveState(s) { fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2)); }

function fetchJson(url, headers = {}) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "northern-dial-bot", ...headers } }, res => {
      let d = ""; res.on("data", c => d += c);
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    }).on("error", reject);
  });
}

function sendTelegram(message) {
  if (!TELEGRAM_TOKEN || !TELEGRAM_CHAT_ID) {
    log(`[Telegram] ${message}`);
    return Promise.resolve();
  }
  return fetchJson(
    `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage?chat_id=${TELEGRAM_CHAT_ID}&text=${encodeURIComponent(message)}&parse_mode=Markdown`
  );
}

function getCommentTemplate(index) {
  return COMMENT_TEMPLATES[index % COMMENT_TEMPLATES.length];
}

async function checkArtist(handle, state, commentIndex) {
  try {
    // Use Business Discovery API to get recent posts
    const url = `https://graph.facebook.com/v19.0/${IG_ID}?fields=business_discovery.as(${handle}){recent_media{id,timestamp,permalink,caption}}&access_token=${IG_TOKEN}`;
    const data = await fetchJson(url);
    const media = data?.business_discovery?.recent_media?.data;

    if (!Array.isArray(media) || media.length === 0) return commentIndex;

    const latestPost = media[0];
    const seenBefore = state.seenPosts[handle];

    if (!seenBefore) {
      // First time checking — just record, don't alert
      state.seenPosts[handle] = latestPost.id;
      log(`  ${handle}: recorded latest post ${latestPost.id} (first check)`);
      return commentIndex;
    }

    if (latestPost.id !== seenBefore) {
      // New post!
      log(`  ${handle}: NEW POST detected! ${latestPost.permalink}`);
      const comment = getCommentTemplate(commentIndex);

      const alert = `🎯 *Northern Dial Comment Opportunity!*\n\n` +
        `Artist: @${handle}\n` +
        `New post: ${latestPost.permalink}\n\n` +
        `Suggested comment:\n"${comment}"\n\n` +
        `_(Tap to comment and drive traffic to northerndial.ca)_`;

      await sendTelegram(alert);
      state.seenPosts[handle] = latestPost.id;
      return commentIndex + 1;
    } else {
      log(`  ${handle}: no new posts`);
    }
  } catch (err) {
    log(`  ${handle}: error — ${err.message}`);
  }
  return commentIndex;
}

async function main() {
  log("=== Northern Dial: Artist Comment Monitor ===");
  const state = loadState();
  let commentIndex = state.commentIndex || 0;

  log(`Checking ${WATCH_HANDLES.length} artists...`);
  for (const handle of WATCH_HANDLES) {
    commentIndex = await checkArtist(handle, state, commentIndex);
    await new Promise(r => setTimeout(r, 500)); // be gentle with API
  }

  state.commentIndex = commentIndex;
  state.lastRun = new Date().toISOString();
  saveState(state);
  log("=== Done ===");
}

main().catch(err => { log(`Fatal: ${err.message}`); process.exit(1); });
