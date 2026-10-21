package com.arrakis.atlas;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.os.Build;
import android.view.WindowInsets;
import android.widget.FrameLayout;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.TextView;

public final class AtlasActivity extends Activity {
    private WebView map;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(14, 21, 25));
        getWindow().setNavigationBarColor(Color.rgb(14, 21, 25));
        try {
            map = new WebView(this);
            map.getSettings().setJavaScriptEnabled(true);
            map.getSettings().setDomStorageEnabled(true);
            map.getSettings().setAllowFileAccess(true);
            map.setBackgroundColor(Color.rgb(14, 21, 25));
            map.setWebViewClient(new WebViewClient() {
                @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                    if (request.isForMainFrame()) showFallback("Die Karte konnte nicht geladen werden.");
                }
            });
            FrameLayout safeArea = new FrameLayout(this);
            safeArea.addView(map, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
            // Android 15+ enforces edge-to-edge. Keep the app's header and buttons
            // away from the system status/navigation bars without hiding those bars.
            if (Build.VERSION.SDK_INT >= 35) {
                safeArea.setOnApplyWindowInsetsListener((view, insets) -> {
                    android.graphics.Insets system = insets.getInsets(
                        WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                    view.setPadding(system.left, system.top, system.right, system.bottom);
                    return insets;
                });
            }
            setContentView(safeArea);
            map.loadUrl("file:///android_asset/index.html");
        } catch (RuntimeException e) {
            showFallback("Die Kartenansicht konnte nicht gestartet werden.");
        }
    }
    private void showFallback(String message) {
        TextView text = new TextView(this);
        text.setText("Arrakis Atlas\n\n" + message);
        text.setTextSize(18);
        text.setTextColor(Color.WHITE);
        text.setBackgroundColor(Color.rgb(14, 21, 25));
        text.setPadding(40, 60, 40, 40);
        setContentView(text);
    }
    @Override public void onBackPressed() {
        if (map != null && map.canGoBack()) map.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if (map != null) { map.destroy(); map = null; }
        super.onDestroy();
    }
}
