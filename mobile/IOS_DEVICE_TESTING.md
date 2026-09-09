# Northern Dial iPhone device test

The iOS project compiles in GitHub Actions. The next release gate is proving the native radio on a physical iPhone.

## One-time Mac setup

1. Install the current Xcode from the Mac App Store and open it once so it can finish installing components.
2. In Xcode, add the Apple ID that will be used for development under Xcode Settings > Accounts.
3. Connect the iPhone to the Mac by cable for the first run, unlock it and trust the Mac if prompted.
4. Enable Developer Mode on the iPhone if iOS requests it for local development builds.

## Get the branch

From Terminal:

```bash
git clone https://github.com/rileywallaceriley/Northern-Dial.git
cd Northern-Dial
git checkout mobile/app-foundation
cd mobile
npm ci
npm run sync
npx cap open ios
```

If the repository is already cloned locally, use `git pull` and `git checkout mobile/app-foundation` instead of cloning again.

## Xcode signing

In Xcode:

1. Select the **App** project, then the **App** target.
2. Open **Signing & Capabilities**.
3. Keep **Automatically manage signing** enabled.
4. Choose your Apple development team.
5. Confirm the bundle identifier is `ca.northerndial.radio`. If Apple reports that identifier is unavailable for your account, stop and choose a new identifier before changing the repository.
6. Confirm **Background Modes > Audio, AirPlay, and Picture in Picture** is enabled. The repository already declares the audio background mode in `Info.plist`.
7. Select the connected iPhone as the run destination and press **Run**.

## First physical-device test

Do these in order and record pass/fail plus anything unexpected:

1. **Launch:** Northern Dial opens without a blank screen or network error.
2. **Live playback:** Tap Play. Audio begins and the status changes from connecting to live.
3. **Now playing:** Track title and artist update from the station metadata feed.
4. **Artist overlay:** Tap the current artist. The artist drawer opens and the radio keeps playing continuously.
5. **Navigation:** Move between Listen, Artists and Listening Paths. Audio never restarts or stops because of navigation.
6. **Screen lock:** Lock the iPhone for at least two minutes. Audio continues.
7. **Lock-screen controls:** Pause and resume from the lock screen. Return to the app and verify its play/pause state matches the system state.
8. **Control Center:** Pause and resume from Control Center. Track and artist metadata should be visible.
9. **Interruption:** Start another audio source or take a phone/FaceTime interruption if convenient. Verify Northern Dial pauses appropriately and behaves sensibly when the interruption ends.
10. **Headphones/Bluetooth:** If available, play through headphones or Bluetooth, then disconnect them. Northern Dial should not unexpectedly blast audio through the phone speaker.
11. **Network transition:** While playing, move between Wi-Fi and cellular. Note whether playback recovers automatically or requires tapping Play.
12. **Pause/resume live edge:** Pause for roughly one minute, then resume. The app should reconnect to the live stream rather than playing an old buffered segment.

## Report format

Send the results back in this compact format:

```text
Device: iPhone model
OS: iOS version
Launch: PASS/FAIL
Playback: PASS/FAIL
Now playing: PASS/FAIL
Artist overlay while playing: PASS/FAIL
Navigation while playing: PASS/FAIL
Screen lock: PASS/FAIL
Lock-screen controls: PASS/FAIL
Control Center metadata: PASS/FAIL
Interruption: PASS/FAIL/NOT TESTED
Headphones/Bluetooth: PASS/FAIL/NOT TESTED
Wi-Fi/cellular transition: PASS/FAIL/NOT TESTED
Live-edge resume: PASS/FAIL
Notes: ...
```

## Do not merge yet

Keep PR #4 in draft until physical-device playback, signing, branding, privacy/store metadata and beta testing are complete. Device testing is intended to reveal native playback problems while the app remains isolated from the production website.
