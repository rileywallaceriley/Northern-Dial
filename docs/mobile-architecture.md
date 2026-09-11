# Northern Dial mobile architecture

Audit date: September 9, 2026. Baseline: 4f08a6210d50eb09d7a6b8a707de9d5dac21ab33.

## Findings

The site is static HTML with Python generation scripts, not an existing JavaScript application. No package manifest or native app projects existed at the baseline. The homepage owns an HTML audio element and polls now-playing every 10 seconds; ordinary page navigation destroys that player. Browser Media Session handlers exist but do not establish native background playback.

The stream is `https://a10.asurahosting.com:7220/radio.mp3`. Metadata is `https://a10.asurahosting.com/api/nowplaying/northern_dial`. Both responded HTTP 200 during the audit; this verifies reachability, not long-duration device playback. The website's listening_paths.json also returned 200 with permissive CORS.

Artist content comes from artist_profiles.json, artist_enrichment.json and alphabetically merged artist_enrichment_batches. build_artist_pages.py generates profile HTML. The directory is generated from the station request catalogue with removal filtering. Listening paths use listening_paths.json and existing artist slugs. Artist matching needs care around punctuation, accents, collaborations and ambiguous names.

The artist-build workflow has path triggers without a branch restriction and explicitly pushes HEAD to main. Its concurrency group is shared across branches. Do not edit those triggering paths on a mobile feature branch until a separately reviewed workflow isolation fix exists. Leave enrichment jobs running. New mobile code lives entirely under mobile/; this document is outside existing mutation workflow triggers.

service-worker.js contains curly quote delimiters and should not be reused by the app. Its cache-first strategy would also need content freshness changes. This build does not modify it.

## Decision

Use a locally bundled Capacitor UI with a single persistent audio controller outside all browsing views. Native platforms own audio independently of WebView lifecycle. iOS uses AVPlayer, AVAudioSession playback, background audio and remote commands; Android uses Media3 with a MediaSessionService. Browser previews use HTML audio and are not evidence of native background support.

Keep the website as the published content source. Initially read its existing artist directory and profile markup through a small, tested adapter, and read listening_paths.json directly. This avoids interrupting the enrichment pipeline and makes newly published bios available without an app release. Never execute fetched HTML; extract text and validated HTTPS links only. A future versioned JSON projection should be generated from the SAME editorial sources, with no separate authoring database. Switching the adapter to that projection should not affect playback or screens.

Cache is optional and disposable, never an editorial source. Content failures must not stop radio playback. No audio downloads, account system, microphone access, or Alexa implementation are in this release scope. The radio is live: no seek or skip controls. Listening paths are editorial discovery journeys, not on-demand playlists.

## Verification and release gates

Verify real published HTML parsing, exact/ambiguous artist resolution, malicious markup exclusion, stream state races, missing profiles, failed metadata, navigation with unchanged player identity and dialog focus restoration. Test native background playback, phone interruptions, unplugged headphones, lock-screen controls and network recovery on actual devices before claiming release readiness.

This Linux workspace has Node/npm and Java, but initially no adb, Gradle CLI or Xcode. iOS compilation/signing requires macOS/Xcode. Store signing accounts, identifiers, screenshots, privacy declarations and distribution rights require verification before submission. The proposed app ID is ca.northerndial.radio and must be checked against the owner's store accounts before release.

Work proceeds in dependency order without waiting for calendar dates: audit; shell; persistent radio; native audio; metadata; overlay; discovery; polish; device testing; store preparation. September 24 is a target, not a guarantee or proof that background automation exists.

References: [Capacitor configuration](https://capacitorjs.com/docs/config), [Android background playback](https://developer.android.com/media/media3/session/background-playback), [Apple audio configuration](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/MediaPlaybackGuide/Contents/Resources/en.lproj/ConfiguringAudioSettings/ConfiguringAudioSettings.html).
