package ca.northerndial.radio;

import android.content.ComponentName;
import androidx.core.content.ContextCompat;
import androidx.media3.common.*;
import androidx.media3.session.*;
import com.google.common.util.concurrent.ListenableFuture;
import com.getcapacitor.*;
import com.getcapacitor.annotation.CapacitorPlugin;

@CapacitorPlugin(name = "NativeRadio")
public class NativeRadioPlugin extends Plugin {
    private ListenableFuture<MediaController> future;
    private MediaController controller;
    private final Player.Listener listener = new Player.Listener() {
        @Override public void onEvents(Player player, Player.Events events) { emit(); }
    };
    @Override public void load() {
        getActivity().runOnUiThread(() -> {
            SessionToken token = new SessionToken(getContext(), new ComponentName(getContext(), RadioService.class));
            future = new MediaController.Builder(getContext(), token).buildAsync();
            future.addListener(() -> {
                try { controller = future.get(); controller.addListener(listener); emit(); }
                catch (Exception ignored) { JSObject s = new JSObject(); s.put("state", "error"); notifyListeners("stateChange", s); }
            }, ContextCompat.getMainExecutor(getContext()));
        });
    }
    private String state() {
        if (controller == null) return "paused";
        if (controller.getPlayerError() != null) return "error";
        if (!controller.getPlayWhenReady()) return "paused";
        return controller.isPlaying() ? "playing" : "buffering";
    }
    private void emit() { JSObject s = new JSObject(); s.put("state", state()); notifyListeners("stateChange", s); }
    @PluginMethod public void getState(PluginCall call) {
        getActivity().runOnUiThread(() -> { JSObject s = new JSObject(); s.put("state", state()); call.resolve(s); });
    }
    @PluginMethod public void play(PluginCall call) {
        getActivity().runOnUiThread(() -> {
            if (controller == null) { call.reject("Audio service is connecting. Please try again."); return; }
            controller.seekToDefaultPosition(); controller.prepare(); controller.play(); call.resolve();
        });
    }
    @PluginMethod public void pause(PluginCall call) {
        getActivity().runOnUiThread(() -> { if (controller != null) controller.pause(); call.resolve(); });
    }
    @Override protected void handleOnDestroy() {
        if (future != null) MediaController.releaseFuture(future);
    }
}
