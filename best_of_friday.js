#!/usr/bin/env node
/**
 * Northern Dial — Weekly Best Of (Fridays)
 * Pulls the most-played track from AzuraCast history,
 * posts a featured carousel to Instagram
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

const SCRIPT_DIR = path.dirname(__filename);
const cfg = JSON.parse(fs.readFileSync(path.join(SCRIPT_DIR, "config.json")));
const LOG = path.join(SCRIPT_DIR, "bestof.log");

const { instagram_token: IG_TOKEN, instagram_account_id: IG_ID, github_token: GH_TOKEN, github_repo: GH_REPO } = cfg;
const AZURACAST_BASE = "https://a10.asurahosting.com/api";

const KNOWN_HANDLES = {
  "katie tupper": "@katietupper", "vbnd": "@vbnd", "shantel may": "@shantelmay",
  "puma june": "@pumajune", "2nd son": "@_2ndson_", "unotopic": "@unotopicmusica",
  "apollo brown": "@apollobrown", "eternia": "@eterniamc", "maestro": "@maestrofreshwes",
  "88glam": "@88glam", "melanie fiona": "@melaniefiona", "livingthing": "@livingthingmusic",
  "harvey stripes": "@harveystripes", "buck 65": "@buck65", "snow": "@snow",
  "la sécurité": "@lasecurite", "serena ryder": "@serenaryder", "hedley": "@hedleyband",
  "hailey blake": "@haileyblakeofficial", "löv": "@lovxofficial", "lov": "@lovxofficial",
};

function log(msg) {
  const ts = new Date().toISOString().replace("T", " ").slice(0, 19);
  const line = `[${ts}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG, line + "\n");
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function fetchJson(url, headers = {}) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { "User-Agent": "northern-dial-bot", ...headers } }, res => {
      let d = ""; res.on("data", c => d += c);
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    }).on("error", reject);
  });
}

function postForm(url, params) {
  const body = Object.entries(params).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = https.request({
      hostname: u.hostname, path: u.pathname, method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "Content-Length": Buffer.byteLength(body), "User-Agent": "northern-dial-bot" },
    }, res => {
      let d = ""; res.on("data", c => d += c);
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on("error", reject);
    req.write(body); req.end();
  });
}

function resolveHandle(artist) {
  const key = artist.toLowerCase().trim();
  for (const [k, v] of Object.entries(KNOWN_HANDLES)) {
    if (key.includes(k) || k.includes(key)) return v;
  }
  return null;
}

async function getTopSongsThisWeek() {
  // AzuraCast song history endpoint
  try {
    const data = await fetchJson(`${AZURACAST_BASE}/station/northern_dial/history?rows=500`);
    if (!Array.isArray(data)) throw new Error("Unexpected history format");

    // Count plays per song
    const counts = {};
    for (const entry of data) {
      const id = entry.song?.id;
      if (!id) continue;
      if (!counts[id]) counts[id] = { ...entry.song, plays: 0 };
      counts[id].plays++;
    }

    return Object.values(counts).sort((a, b) => b.plays - a.plays).slice(0, 5);
  } catch (err) {
    log(`History fetch failed: ${err.message} — falling back to now playing`);
    // Fallback: use now playing
    const np = await fetchJson(`${AZURACAST_BASE}/nowplaying/northern_dial`);
    return [{ ...np.now_playing?.song, plays: 1 }];
  }
}

async function uploadImage(imgUrl) {
  const result = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media`, {
    image_url: imgUrl, is_carousel_item: "true", access_token: IG_TOKEN,
  });
  if (!result.id) throw new Error(`Upload failed: ${JSON.stringify(result)}`);
  return result.id;
}

async function postCarousel(songs) {
  const now = new Date();
  const weekStr = `${now.toLocaleDateString("en-CA", { month: "long", day: "numeric" })}`;

  // Build caption
  const lines = [`🏆 NORTHERN DIAL — BEST OF THE WEEK`, `Week of ${weekStr}`, ``];
  for (let i = 0; i < songs.length; i++) {
    const { artist, title, plays } = songs[i];
    const parts = artist.split(/[,/]|\s+(?:feat\.?|ft\.?|&)\s+/i).map(p => p.trim()).filter(Boolean);
    const tagged = parts.map(p => resolveHandle(p) || p).join(" & ");
    lines.push(`${i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}.`} ${tagged} - "${title}" (${plays} plays)`);
  }
  lines.push(``, `All CanCon, All Week 🍁`, `Tune in: northerndial.ca`, ``);
  lines.push(`#NorthernDial #CanCon #CanadianMusic #BestOf #WeeklyPlaylist #CanadianRadio #IndieRadio #DiscoverMusic #CanadianArtists #TopTracks`);

  const caption = lines.join("\n");
  log(`Caption:\n${caption}`);

  // Upload album art images
  log("Uploading images...");
  const children = [];
  for (let i = 0; i < Math.min(songs.length, 5); i++) {
    const imgUrl = songs[i].art || "https://northerndial.ca/img/logo.jpg";
    const id = await uploadImage(imgUrl);
    log(`  image ${i+1}: ${id}`);
    children.push(id);
    await sleep(1000);
  }

  // Pad to at least 2 items (Instagram requires minimum 2 for carousel)
  while (children.length < 2) children.push(children[0]);

  log("Creating container...");
  const container = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media`, {
    media_type: "CAROUSEL", children: children.join(","), caption, access_token: IG_TOKEN,
  });
  if (!container.id) throw new Error(`Container failed: ${JSON.stringify(container)}`);

  await sleep(3000);
  log("Publishing...");
  const result = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media_publish`, {
    creation_id: container.id, access_token: IG_TOKEN,
  });
  if (!result.id) throw new Error(`Publish failed: ${JSON.stringify(result)}`);
  return result.id;
}

async function main() {
  log("=== Northern Dial: Weekly Best Of ===");
  log("Fetching top songs this week...");
  const topSongs = await getTopSongsThisWeek();
  log(`Top ${topSongs.length} songs found`);
  topSongs.forEach((s, i) => log(`  ${i+1}. ${s.artist} - ${s.title} (${s.plays} plays)`));

  const postId = await postCarousel(topSongs);
  log(`✅ Best Of posted! ID: ${postId}`);
}

main().catch(err => { log(`Fatal: ${err.message}`); process.exit(1); });
