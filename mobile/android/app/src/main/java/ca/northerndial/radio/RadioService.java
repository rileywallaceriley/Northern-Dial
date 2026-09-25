package ca.northerndial.radio;

import android.os.Handler;
import android.os.Looper;
import androidx.annotation.Nullable;
import androidx.media3.common.*;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.session.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import org.json.JSONObject;

public class RadioService extends MediaSessionService {
    private ExoPlayer player;
    private MediaSession session;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private boolean fetching = false;
    private boolean destroyed = false;
    private final Runnable metadataTick = new Runnable() {
        public void run() {
            if (player != null && player.getPlayWhenReady() && !fetching) refreshMetadata();
            handler.postDelayed(this, 10000);
        }
    };
    @Override public void onCreate() {
        super.onCreate();
        player = new ExoPlayer.Builder(this).build();
        player.setAudioAttributes(new AudioAttributes.Builder().setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_MUSIC).build(), true);
        player.setHandleAudioBecomingNoisy(true);
        player.setWakeMode(C.WAKE_MODE_NETWORK);
        player.setMediaItem(new MediaItem.Builder().setMediaId("northern-dial-live").setUri("https://a10.asurahosting.com:7220/radio.mp3")
            .setMediaMetadata(new MediaMetadata.Builder().setTitle("Northern Dial").setArtist("Live Canadian radio").build()).build());
        session = new MediaSession.Builder(this, player).build();
        handler.post(metadataTick);
    }
    private void refreshMetadata() {
        fetching = true;
        network.execute(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL("https://a10.asurahosting.com/api/nowplaying/northern_dial").openConnection();
                connection.setConnectTimeout(8000); connection.setReadTimeout(8000);
                String body;
                try (java.io.InputStream in = connection.getInputStream()) { java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream(); byte[] buffer = new byte[8192]; int count; while ((count = in.read(buffer)) != -1) out.write(buffer, 0, count); body = out.toString("UTF-8"); }
                JSONObject song = new JSONObject(body).getJSONObject("now_playing").getJSONObject("song");
                String title = song.optString("title", "Northern Dial"), artist = song.optString("artist", "Live Canadian radio");
                handler.post(() -> {
                    if (destroyed || player == null || player.getCurrentMediaItem() == null) return;
                    MediaItem item = player.getCurrentMediaItem().buildUpon().setMediaMetadata(new MediaMetadata.Builder().setTitle(title).setArtist(artist).build()).build();
                    // Metadata-only replacement preserves the current playback connection.
                    player.replaceMediaItem(0, item);
                });
            } catch (Exception ignored) { /* Metadata failure must never stop audio. */ }
            finally { if (connection != null) connection.disconnect(); handler.post(() -> fetching = false); }
        });
    }
    @Nullable @Override public MediaSession onGetSession(MediaSession.ControllerInfo controller) { return session; }
    @Override public void onDestroy() {
        destroyed = true; handler.removeCallbacksAndMessages(null); network.shutdownNow();
        if (session != null) session.release();
        if (player != null) { player.release(); player = null; }
        super.onDestroy();
    }
}
