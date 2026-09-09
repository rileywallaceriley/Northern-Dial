import UIKit
import Capacitor

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate {

    var window: UIWindow?

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        // Override point for customization after application launch.
        return true
    }

    func applicationWillResignActive(_ application: UIApplication) {
        // Sent when the application is about to move from active to inactive state. This can occur for certain types of temporary interruptions (such as an incoming phone call or SMS message) or when the user quits the application and it begins the transition to the background state.
        // Use this method to pause ongoing tasks, disable timers, and invalidate graphics rendering callbacks. Games should use this method to pause the game.
    }

    func applicationDidEnterBackground(_ application: UIApplication) {
        // Use this method to release shared resources, save user data, invalidate timers, and store enough application state information to restore your application to its current state in case it is terminated later.
        // If your application supports background execution, this method is called instead of applicationWillTerminate: when the user quits.
    }

    func applicationWillEnterForeground(_ application: UIApplication) {
        // Called as part of the transition from the background to the active state; here you can undo many of the changes made on entering the background.
    }

    func applicationDidBecomeActive(_ application: UIApplication) {
        // Restart any tasks that were paused (or not yet started) while the application was inactive. If the application was previously in the background, optionally refresh the user interface.
    }

    func applicationWillTerminate(_ application: UIApplication) {
        // Called when the application is about to terminate. Save data if appropriate. See also applicationDidEnterBackground:.
    }

    func application(_ application: UIApplication,
                     configurationForConnecting connectingSceneSession: UISceneSession,
                     options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let config = UISceneConfiguration(name: "Default Configuration",
                                          sessionRole: connectingSceneSession.role)
        config.delegateClass = SceneDelegate.self
        return config
    }
}

// Kept in this compiled source file so the generated Xcode target includes the plugin.
import AVFoundation
import MediaPlayer

class RadioViewController: CAPBridgeViewController {
    override func capacitorDidLoad() { bridge?.registerPluginInstance(NativeRadioPlugin()) }
}

@objc(NativeRadioPlugin)
public class NativeRadioPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "NativeRadioPlugin"
    public let jsName = "NativeRadio"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "play", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "pause", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getState", returnType: CAPPluginReturnPromise)
    ]
    private let engine = RadioEngine.shared
    public override func load() {
        engine.changed = { [weak self] state in self?.notifyListeners("stateChange", data: ["state": state]) }
    }
    @objc func play(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            do { try self.engine.play(); call.resolve() } catch { call.reject("Unable to start radio", nil, error) }
        }
    }
    @objc func pause(_ call: CAPPluginCall) { DispatchQueue.main.async { self.engine.pause(); call.resolve() } }
    @objc func getState(_ call: CAPPluginCall) { DispatchQueue.main.async { call.resolve(["state": self.engine.state]) } }
}

final class RadioEngine: NSObject {
    static let shared = RadioEngine()
    let player = AVPlayer()
    var changed: ((String) -> Void)?
    private var observation: NSKeyValueObservation?
    private var itemObservation: NSKeyValueObservation?
    private var timer: Timer?
    private var fetching = false
    private var wantsPlayback = false
    private var resumeAfterInterruption = false
    private(set) var state = "paused" { didSet { changed?(state) } }
    override init() {
        super.init()
        observation = player.observe(\.timeControlStatus, options: [.new]) { [weak self] player, _ in
            DispatchQueue.main.async {
                guard let self = self else { return }
                if self.player.currentItem?.status == .failed { self.state = "error" }
                else { self.state = player.timeControlStatus == .playing ? "playing" : (self.wantsPlayback ? "buffering" : "paused") }
                self.updatePlaybackInfo()
            }
        }
        NotificationCenter.default.addObserver(self, selector: #selector(interruption), name: AVAudioSession.interruptionNotification, object: nil)
        NotificationCenter.default.addObserver(self, selector: #selector(routeChanged), name: AVAudioSession.routeChangeNotification, object: nil)
        let remote = MPRemoteCommandCenter.shared()
        remote.playCommand.addTarget { [weak self] _ in
            guard let self = self else { return .commandFailed }
            do { try self.play(); return .success } catch { return .commandFailed }
        }
        remote.pauseCommand.addTarget { [weak self] _ in self?.pause(); return .success }
        remote.togglePlayPauseCommand.addTarget { [weak self] _ in
            guard let self = self else { return .commandFailed }
            if self.wantsPlayback { self.pause(); return .success }
            do { try self.play(); return .success } catch { return .commandFailed }
        }
        remote.nextTrackCommand.isEnabled = false
        remote.previousTrackCommand.isEnabled = false
        remote.changePlaybackPositionCommand.isEnabled = false
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [MPMediaItemPropertyTitle: "Northern Dial", MPMediaItemPropertyArtist: "Live Canadian radio", MPNowPlayingInfoPropertyIsLiveStream: true]
    }
    func play() throws {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.playback, mode: .default)
        try session.setActive(true)
        wantsPlayback = true
        state = "buffering"
        // Reconnect to the live edge after a pause; do not resume old buffered radio.
        let item = AVPlayerItem(url: URL(string: "https://a10.asurahosting.com:7220/radio.mp3")!)
        itemObservation = item.observe(\.status, options: [.new]) { [weak self] item, _ in
            if item.status == .failed { DispatchQueue.main.async { self?.state = "error" } }
        }
        player.replaceCurrentItem(with: item)
        player.play()
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { [weak self] _ in self?.refreshMetadata() }
        refreshMetadata()
    }
    func pause() {
        wantsPlayback = false; resumeAfterInterruption = false
        player.pause(); state = "paused"; timer?.invalidate(); timer = nil
        updatePlaybackInfo()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
    private func updatePlaybackInfo() {
        var info = MPNowPlayingInfoCenter.default().nowPlayingInfo ?? [:]
        info[MPNowPlayingInfoPropertyPlaybackRate] = state == "playing" ? 1.0 : 0.0
        info[MPNowPlayingInfoPropertyIsLiveStream] = true
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }
    private func refreshMetadata() {
        guard wantsPlayback, !fetching else { return }; fetching = true
        var request = URLRequest(url: URL(string: "https://a10.asurahosting.com/api/nowplaying/northern_dial")!)
        request.timeoutInterval = 8
        URLSession.shared.dataTask(with: request) { [weak self] data, response, _ in
            DispatchQueue.main.async {
                guard let self = self else { return }; self.fetching = false
                guard let data = data, (response as? HTTPURLResponse)?.statusCode == 200,
                      let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                      let current = root["now_playing"] as? [String: Any], let song = current["song"] as? [String: Any] else { return }
                var info = MPNowPlayingInfoCenter.default().nowPlayingInfo ?? [:]
                info[MPMediaItemPropertyTitle] = song["title"] as? String ?? "Northern Dial"
                info[MPMediaItemPropertyArtist] = song["artist"] as? String ?? "Live Canadian radio"
                MPNowPlayingInfoCenter.default().nowPlayingInfo = info
                self.updatePlaybackInfo()
            }
        }.resume()
    }
    @objc private func interruption(_ notification: Notification) {
        guard let raw = notification.userInfo?[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
        if type == .began {
            resumeAfterInterruption = wantsPlayback
            wantsPlayback = false; player.pause(); state = "paused"
        } else {
            let rawOptions = notification.userInfo?[AVAudioSessionInterruptionOptionKey] as? UInt ?? 0
            if resumeAfterInterruption && AVAudioSession.InterruptionOptions(rawValue: rawOptions).contains(.shouldResume) { try? play() }
            resumeAfterInterruption = false
        }
    }
    @objc private func routeChanged(_ notification: Notification) {
        guard let reason = notification.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt else { return }
        if reason == AVAudioSession.RouteChangeReason.oldDeviceUnavailable.rawValue { pause() }
    }
}
