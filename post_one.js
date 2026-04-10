#!/usr/bin/env node
/**
 * Northern Dial — Post ONE pending carousel to Instagram
 * Called by cron at scheduled times. Posts the oldest pending folder, then exits.
 */

const https = require("https");
const fs = require("fs");
const path = require("path");

const SCRIPT_DIR = path.dirname(__filename);
const CONFIG_FILE = path.join(SCRIPT_DIR, "config.json");
const POSTED_LOG = path.join(SCRIPT_DIR, "posted.json");
const RUN_LOG = path.join(SCRIPT_DIR, "run.log");

const cfg = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
const { github_token: GH_TOKEN, github_repo: GH_REPO, instagram_token: IG_TOKEN, instagram_account_id: IG_ID } = cfg;

const RAW_BASE = `https://raw.githubusercontent.com/${GH_REPO}/main`;
const API_BASE = `https://api.github.com/repos/${GH_REPO}`;

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
  "jacksoul": "@jacksoul",
  "deborah cox": "@deborahcox",
  "hailey blake": "@haileyblakeofficial",
  "löv": "@lovband",
  "lov": "@lovband",
};

const BASE_TAGS = ["#CanadianMusic", "#CanCon", "#NorthernDial", "#IndieRadio", "#DiscoverMusic", "#SupportCanadianArtists"];
const GENRE_TAGS = {
  hiphop: ["#CanadianHipHop", "#HipHop", "#Rap", "#UndergroundHipHop", "#TorontoHipHop", "#CanadianRap"],
  rnb: ["#RnB", "#CanadianRnB", "#SoulMusic", "#NeoSoul"],
  indie: ["#IndieMusic", "#CanadianIndie", "#IndiePop", "#IndieArtist"],
  pop: ["#CanadianPop", "#PopMusic", "#NewMusic"],
  rock: ["#CanadianRock", "#IndieRock", "#AlternativeRock"],
  electronic: ["#ElectronicMusic", "#CanadianElectronic", "#Beats"],
  classic: ["#CanadianClassics", "#ThrowbackCanCon", "#CanadianLegends"],
};

function log(msg) {
  const ts = new Date().toISOString().replace("T", " ").slice(0, 19);
  const line = `[${ts}] ${msg}`;
  console.log(line);
  fs.appendFileSync(RUN_LOG, line + "\n");
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function ghReq(method, urlOrPath, body) {
  return new Promise((resolve, reject) => {
    const isFullUrl = urlOrPath.startsWith("https://");
    const urlObj = isFullUrl ? new URL(urlOrPath) : new URL("https://api.github.com" + urlOrPath);
    const b = body ? JSON.stringify(body) : null;
    const req = https.request({
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method,
      headers: {
        Authorization: `token ${GH_TOKEN}`,
        Accept: "application/vnd.github.v3+json",
        "User-Agent": "northern-dial-bot",
        ...(b ? { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(b) } : {}),
      },
    }, res => {
      let d = ""; res.on("data", c => d += c);
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on("error", reject);
    if (b) req.write(b);
    req.end();
  });
}

function postForm(url, params) {
  const body = Object.entries(params).map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join("&");
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const req = https.request({
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": Buffer.byteLength(body),
        "User-Agent": "northern-dial-bot",
      },
    }, res => {
      let d = ""; res.on("data", c => d += c);
      res.on("end", () => { try { resolve(JSON.parse(d)); } catch { resolve(d); } });
    });
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

function loadPostedLog() {
  if (fs.existsSync(POSTED_LOG)) return new Set(JSON.parse(fs.readFileSync(POSTED_LOG)));
  return new Set();
}
function savePostedLog(posted) { fs.writeFileSync(POSTED_LOG, JSON.stringify([...posted], null, 2)); }

function resolveHandle(artist) {
  const key = artist.toLowerCase().trim();
  for (const [k, v] of Object.entries(KNOWN_HANDLES)) {
    if (key.includes(k) || k.includes(key)) return v;
  }
  return null;
}

function detectTags(songs) {
  const combined = songs.map(s => `${s.artist} ${s.title}`).join(" ").toLowerCase();
  const tags = [...BASE_TAGS];
  if (/rap|hip.?hop|beat|glam|buck|maestro|apollo|potlood|2nd son/.test(combined)) tags.push(...GENRE_TAGS.hiphop);
  if (/r&b|rnb|soul|fiona|shantel|deborah|jacksoul/.test(combined)) tags.push(...GENRE_TAGS.rnb);
  if (/indie|living|puma|stripes/.test(combined)) tags.push(...GENRE_TAGS.indie);
  if (/pop|hedley|snow|serena/.test(combined)) tags.push(...GENRE_TAGS.pop);
  if (/rock|ryder/.test(combined)) tags.push(...GENRE_TAGS.rock);
  if (/securit|electronic|unotopic|beat factory/.test(combined)) tags.push(...GENRE_TAGS.electronic);
  if (/maestro|wizkid|len |shawn desman/.test(combined)) tags.push(...GENRE_TAGS.classic);
  return [...new Set(tags)].slice(0, 20);
}

function buildCaption(postInfo) {
  const songs = postInfo.songs || [];
  const lines = ["🎵 RECENTLY PLAYED ON NORTHERN DIAL", ""];
  for (let i = 0; i < songs.length; i++) {
    const { artist, title } = songs[i];
    const parts = artist.split(/[,/]|\s+(?:feat\.?|ft\.?|&)\s+/i).map(p => p.trim()).filter(Boolean);
    const tagged = parts.map(p => resolveHandle(p) || p).join(" & ");
    lines.push(`${i + 1}. ${tagged} - "${title}"`);
  }
  lines.push("", "All Killer, All CanCon 🍁", "Tune in: northerndial.ca", "");
  lines.push(detectTags(songs).join(" "));
  return lines.join("\n");
}

async function getPendingPosts() {
  const result = await ghReq("GET", `/repos/${GH_REPO}/contents/instagram-posts`);
  if (!Array.isArray(result)) return [];
  return result.filter(i => i.type === "dir").map(i => i.name).sort();
}

async function uploadImage(imgUrl) {
  const result = await postForm(`https://graph.facebook.com/v19.0/${IG_ID}/media`, {
    image_url: imgUrl, is_carousel_item: "true", access_token: IG_TOKEN,
  });
  if (!result.id) throw new Error(`Upload failed: ${JSON.stringify(result)}`);
  return result.id;
}

async function postCarousel(folder, caption) {
  const base = `${RAW_BASE}/instagram-posts/${folder}`;
  const children = [];
  log("Uploading images...");
  for (let i = 1; i <= 5; i++) {
    const id = await uploadImage(`${base}/image_${i}.jpg`);
    log(`  image_${i}: ${id}`);
    children.push(id);
    await sleep(1000);
  }
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

async function deleteFolderFromGitHub(folder) {
  const files = await ghReq("GET", `/repos/${GH_REPO}/contents/instagram-posts/${folder}`);
  for (const file of files) {
    await ghReq("DELETE", file.url, { message: `Remove ${folder} after Instagram post`, sha: file.sha });
    log(`  Deleted: ${file.name}`);
    await sleep(300);
  }
}

async function main() {
  log("=== Northern Dial: Post One ===");
  const posted = loadPostedLog();
  const pending = await getPendingPosts();

  if (pending.length === 0) {
    log("Queue empty — nothing to post.");
    return;
  }

  // Post only the oldest unposted folder
  const folder = pending.find(f => !posted.has(f));
  if (!folder) { log("All pending posts already processed."); return; }

  log(`Posting: ${folder} (${pending.length} in queue)`);
  try {
    const postInfo = await ghReq("GET", `https://raw.githubusercontent.com/${GH_REPO}/main/instagram-posts/${folder}/post_info.json`);
    const caption = buildCaption(postInfo);
    log(`Caption:\n${caption}`);

    const postId = await postCarousel(folder, caption);
    log(`✅ Posted! ID: ${postId}`);

    await deleteFolderFromGitHub(folder);
    log(`✅ Deleted ${folder} from repo.`);

    posted.add(folder);
    savePostedLog(posted);
    log(`${pending.length - 1} posts remaining in queue.`);
  } catch (err) {
    log(`❌ Failed: ${err.message}`);
    process.exit(1);
  }
}

main().catch(err => { log(`Fatal: ${err.message}`); process.exit(1); });
