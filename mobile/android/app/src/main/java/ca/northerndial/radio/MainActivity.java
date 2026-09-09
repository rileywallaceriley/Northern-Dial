package ca.northerndial.radio;
import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
public class MainActivity extends BridgeActivity {
    @Override public void onCreate(Bundle state) { registerPlugin(NativeRadioPlugin.class); super.onCreate(state); }
}
