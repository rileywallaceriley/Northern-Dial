#!/usr/bin/env node
/**
 * Northern Dial — Instagram Auto-Poster
 * Watches GitHub repo for new instagram-posts folders,
 * resolves artist handles, enhances captions with hashtags,
 * posts a carousel, then deletes the folder from the repo.
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

const SCRIPT_DIR = path.dirname(require.resolve ? __filename : ".");
const CONFIG_FILE = path.join(SCRIPT_DIR, "config.json");
const POSTED_LOG = path.join(SCRIPT_DIR, "posted.json");

const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
const { github_token: GH_TOKEN, github_repo: GH_REPO, instagram_token: IG_TOKEN, instagram_account_id: IG_ID } = cfg;

const RAW_BASE = `https://raw.githubusercontent.com/${GH_REPO}/main`;
const API_BASE = `https://api.github.com/repos/${GH_REPO}`;

// ── Known handles ──────────────────────────────────────────────────────────
const KNOWN_HANDLES = {
  "katie tupper": "@katietupper",
  "vbnd": "@vbnd",
  "shantel may": "@shantelmay",
  "puma june": "@pumajune",
  "2nd son": "@_2ndson_",
  "unotopic": "@unotopicmusica",
  "apollo brown": "@apollobrown",
  "eternia": "@eterniamc",
  "maestro": "@maestrofreshwes",
  "maestro fresh wes": "@maestrofreshwes",
  "88glam": "@88glam",
  "melanie fiona": "@melaniefiona",
  "livingthing": "@livingthingmusic",
  "harvey stripes": "@harveystripes",
  "buck 65": "@buck65",
  "snow": "@snow",
  "la sécurité": "@lasecurite",
  "la securite": "@lasecurite",
  "serena ryder": "@serenaryder",
  "hedley": "@hedleyband",
  "casey mq": "@caseymq",
  "hailey blake": "@haileyblakeofficial",
  "löv": "@lovband",
  "lov": "@lovband",
};

// ── Genre hashtag sets ─────────────────────────────────────────────────────
const BASE_TAGS = ["#CanadianMusic", "#CanCon", "#NorthernDial", "#IndieRadio", "#DiscoverMusic", "#SupportCanadianArtists"];

const GENRE_TAGS = {
  hiphop: ["#CanadianHipHop", "#HipHop", "#Rap", "#UndergroundHipHop", "#TorontoHipHop", "#CanadianRap"],
  rnb: ["#RnB", "#CanadianRnB", "#SoulMusic", "#NeoSoul"],
  indie: ["#IndieMusic", "#CanadianIndie", "#IndiePop", "#IndieArtist"],
  pop: ["#CanadianPop", "#PopMusic", "#NewMusic"],
  rock: ["#CanadianRock", "#IndieRock", "#AlternativeRock"],
  electronic: ["#ElectronicMusic", "#CanadianElectronic", "#Beats"],
  folk: ["#FolkMusic", "#CanadianFolk", "#Acoustic"],
  classic: ["#CanadianClassics", "#ThrowbackCanCon", "#CanadianLegends"],
};

// ── Helpers ────────────────────────────────────────────────────────────────
function log(msg) {
  const ts = new Date().toISOString().replace("T", " ").slice(0, 19);
  console.log(`[${ts}] ${msg}`);
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function fetchJson(url, options = {}) {
  return new Promise((resolve, reject) => {
    const { method = "GET", headers = {}, body } = options;
    const urlObj = new URL(url);
    const reqOptions = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method,
      headers: { "User-Agent": "northern-dial-bot/1.0", ...headers },
    };
    const req = https.request(reqOptions, (res) => {
      let data = "";
      res.on("data", (chunk) => (data += chunk));
      res.on("end", () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch (e) { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on("error", reject);
    if (body) req.write(body);
    req.end();
  });
}

function ghHeaders() {
  return { Authorization: `token ${GH_TOKEN}`, Accept: "application/vnd.github.v3+json" };
}

function encodeFormData(params) {
  return Object.entries(params)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
}

function postForm(url, params) {
  const body = encodeFormData(params);
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const req = https.request(
      {
        hostname: urlObj.hostname,
        path: urlObj.pathname + urlObj.search,
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "Content-Length": Buffer.byteLength(body),
          "User-Agent": "northern-dial-bot/1.0",
        },
      },
      (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => {
          try { resolve(JSON.parse(data)); }
          catch { resolve(data); }
        });
      }
    );
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

// ── Logic ──────────────────────────────────────────────────────────────────
function loadPostedLog() {
  if (fs.existsSync(POSTED_LOG)) return new Set(JSON.parse(fs.readFileSync(POSTED_LOG)));
  return new Set();
}

function savePostedLog(posted) {
  fs.writeFileSync(POSTED_LOG, JSON.stringify([...posted], null, 2));
}

async function getPendingPosts() {
  const { status, body } = await fetchJson(`${API_BASE}/contents/instagram-posts`, { headers: ghHeaders() });
  if (status === 404) return [];
  return body.filter((i) => i.type === "dir").map((i) => i.name).sort();
}

async function getPostInfo(folder) {
  const { body } = await fetchJson(`${RAW_BASE}/instagram-posts/${folder}/post_info.json`);
  return body;
}

function resolveHandle(artistName) {
  const key = artistName.toLowerCase().trim();
  for (const [known, handle] of Object.entries(KNOWN_HANDLES)) {
    if (key.includes(known) || known.includes(key)) return handle;
  }
  return null;
}

function detectGenreTags(songs) {
  const combined = songs.map((s) => `${s.artist || ""} ${s.title || ""}`).join(" ").toLowerCase();
  const tags = [...BASE_TAGS];

  if (/rap|hip.?hop|beat|glam|son|buck|maestro|apollo|potlood|2nd son/.test(combined)) tags.push(...GENRE_TAGS.hiphop);
  if (/r&b|rnb|soul|fiona|shantel/.test(combined)) tags.push(...GENRE_TAGS.rnb);
  if (/indie|living|puma|stripes|june/.test(combined)) tags.push(...GENRE_TAGS.indie);
  if (/pop|hedley|snow|serena/.test(combined)) tags.push(...GENRE_TAGS.pop);
  if (/rock|ryder|never too late/.test(combined)) tags.push(...GENRE_TAGS.rock);
  if (/securit|electronic|unotopic|beat factory/.test(combined)) tags.push(...GENRE_TAGS.electronic);

  // Deduplicate, cap at 20
  return [...new Set(tags)].slice(0, 20);
}

function buildCaption(postInfo) {
  const songs = postInfo.songs || [];
  const lines = ["🎵 RECENTLY PLAYED ON NORTHERN DIAL", ""];

  for (let i = 0; i < songs.length; i++) {
    const { artist, title } = songs[i];
    const parts = artist.split(/[,/]|\s+(?:feat\.?|ft\.?|&)\s+/i).map((p) => p.trim()).filter(Boolean);
    const tagged = parts.map((p) => resolveHandle(p) || p).join(" & ");
    lines.push(`${i + 1}. ${tagged} - "${title}"`);
  }

  lines.push("", "All Killer, All CanCon 🍁", "Tune in: northerndial.ca", "");
  lines.push(detectGenreTags(songs).join(" "));
  return lines.join("\n");
}

async function uploadImage(imgUrl) {
  const result = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media`, {
    image_url: imgUrl,
    is_carousel_item: "true",
    access_token: IG_TOKEN,
  });
  if (!result.id) throw new Error(`Image upload failed: ${JSON.stringify(result)}`);
  return result.id;
}

async function postCarousel(folder, caption) {
  const baseUrl = `${RAW_BASE}/instagram-posts/${folder}`;
  const children = [];

  log("Uploading images...");
  for (let i = 1; i <= 5; i++) {
    const id = await uploadImage(`${baseUrl}/image_${i}.jpg`);
    log(`  image_${i}: ${id}`);
    children.push(id);
    await sleep(1000);
  }

  log("Creating carousel container...");
  const container = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media`, {
    media_type: "CAROUSEL",
    children: children.join(","),
    caption,
    access_token: IG_TOKEN,
  });
  if (!container.id) throw new Error(`Container failed: ${JSON.stringify(container)}`);
  log(`Container: ${container.id}`);

  await sleep(3000);

  log("Publishing...");
  const result = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media_publish`, {
    creation_id: container.id,
    access_token: IG_TOKEN,
  });
  if (!result.id) throw new Error(`Publish failed: ${JSON.stringify(result)}`);
  return result.id;
}

async function deleteFolderFromGitHub(folder) {
  const { body: files } = await fetchJson(`${API_BASE}/contents/instagram-posts/${folder}`, { headers: ghHeaders() });

  for (const file of files) {
    const delBody = JSON.stringify({ message: `Remove ${folder} after Instagram post`, sha: file.sha });
    await new Promise((resolve, reject) => {
      const urlObj = new URL(file.url);
      const req = https.request(
        {
          hostname: urlObj.hostname,
          path: urlObj.pathname + urlObj.search,
          method: "DELETE",
          headers: { ...ghHeaders(), "Content-Type": "application/json", "Content-Length": Buffer.byteLength(delBody) },
        },
        (res) => {
          res.resume();
          res.on("end", resolve);
        }
      );
      req.on("error", reject);
      req.write(delBody);
      req.end();
    });
    log(`  Deleted: ${file.name}`);
    await sleep(300);
  }
}

// ── Main ───────────────────────────────────────────────────────────────────
async function main() {
  log("=== Northern Dial Instagram Auto-Poster ===");
  const posted = loadPostedLog();
  const pending = await getPendingPosts();

  if (pending.length === 0) {
    log("Queue is empty — nothing to post.");
    return;
  }

  log(`Found ${pending.length} pending post(s): ${pending.join(", ")}`);

  for (let i = 0; i < pending.length; i++) {
    const folder = pending[i];
    if (posted.has(folder)) { log(`Skipping ${folder} (already posted)`); continue; }

    log(`\n--- Processing ${folder} ---`);
    try {
      const postInfo = await getPostInfo(folder);
      const caption = buildCaption(postInfo);
      log(`Caption:\n${caption}\n`);

      const postId = await postCarousel(folder, caption);
      log(`✅ Posted! Instagram ID: ${postId}`);

      log(`Deleting ${folder} from GitHub...`);
      await deleteFolderFromGitHub(folder);
      log(`✅ Deleted from repo.`);

      posted.add(folder);
      savePostedLog(posted);

      if (i < pending.length - 1) {
        log("Waiting 30s before next post...");
        await sleep(30000);
      }
    } catch (err) {
      log(`❌ Error on ${folder}: ${err.message}`);
    }
  }

  log("\n=== Done ===");
}

main().catch((err) => { log(`Fatal: ${err.message}`); process.exit(1); });
