# Northern Dial iPhone device test

The iOS project compiles in GitHub Actions. Riley does not have a Mac, so physical iPhone testing uses a cloud macOS runner plus TestFlight rather than local Xcode.

## iPad-only route

The repository includes `.github/workflows/ios-testflight.yml`. It can archive and upload Northern Dial to App Store Connect/TestFlight from GitHub Actions. A Mac is not required for routine beta builds once Apple signing is configured.

### Apple prerequisites

1. Be enrolled in the Apple Developer Program.
2. In App Store Connect, create the Northern Dial iOS app record using bundle ID `ca.northerndial.radio`.
3. Enable App Store Connect API access if it is not already enabled.
4. Create a **team App Store Connect API key** with sufficient signing/distribution access. A team key is required because individual keys do not support provisioning endpoints.
5. Download the `.p8` private key and keep it private. Apple only lets you download it once.
6. Record the API Key ID, Issuer ID and Apple Developer Team ID.

### GitHub Actions secrets

From GitHub in Safari on iPad, open the Northern Dial repository and add these Actions secrets under repository **Settings > Secrets and variables > Actions**:

- `APP_STORE_CONNECT_KEY_ID` — the App Store Connect API Key ID.
- `APP_STORE_CONNECT_ISSUER_ID` — the App Store Connect Issuer ID.
- `APP_STORE_CONNECT_PRIVATE_KEY` — the complete contents of the downloaded `.p8` private key, including the BEGIN/END lines.
- `APPLE_TEAM_ID` — the Apple Developer Team ID.

Never commit the `.p8` key or any of these values to the repository.

### Send a build to TestFlight

1. In GitHub, switch to the `mobile/app-foundation` branch.
2. Open **Actions > iOS TestFlight**.
3. Tap **Run workflow** and choose `mobile/app-foundation`.
4. GitHub runs the web tests, syncs Capacitor, archives the native iOS app using a hosted Mac and asks Apple to cloud-sign and upload it.
5. After Apple processes the upload, open App Store Connect/TestFlight and enable the build for internal testing.
6. On the iPhone, install Apple's TestFlight app and install Northern Dial from the invitation/account.

The first TestFlight upload may expose account-level setup that CI cannot complete for you, such as an app record, agreements, API access, signing permissions or a bundle-ID conflict. Fix the Apple account item and rerun the workflow rather than changing application code blindly.

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
