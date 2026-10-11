package org.flippets.app;
import android.app.*;
import android.content.*;
import android.content.res.Configuration;
import android.graphics.*;
import android.os.*;
import android.view.*;

/** Ordinary foreground cards. No supervisor, CoverGuard, hinge or wake ownership. */
public final class CoverAppsActivity extends Activity {
    MiniAppView cards;boolean qaStarted,resumed;
    protected void onCreate(Bundle saved){
        setTheme(android.R.style.Theme_Material_NoActionBar);super.onCreate(saved);
        getWindow().setStatusBarColor(Color.BLACK);getWindow().setNavigationBarColor(Color.BLACK);
        WindowManager.LayoutParams attributes=getWindow().getAttributes();attributes.layoutInDisplayCutoutMode=WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS;getWindow().setAttributes(attributes);
        if(Build.VERSION.SDK_INT>=30)getWindow().setDecorFitsSystemWindows(false);
        cards=new MiniAppView(this,true,this::select,true);
        if(NativeAppsQa.emulator()&&getIntent().getBooleanExtra("qaNativeApps",false)){
            String origin=getIntent().getStringExtra("qaOrigin");if(origin!=null&&origin.matches("qa-native-[a-z0-9-]+\\.invalid"))cards.qaOrigin=origin;
            NativeAppsQa.attach(this);
        }
        cards.note.setText("Настройки Flip Pets · карточки Xiaomi");cards.note.setTextColor(Color.WHITE);
        cards.note.setBackground(new UiTheme(this).shape(0xff17202e,24));
        cards.note.setPadding(cards.dp(12),cards.dp(4),cards.dp(12),cards.dp(4));
        cards.note.setContentDescription("Открыть настройки Flip Pets");cards.note.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_YES);
        cards.note.setMinHeight(cards.dp(48));cards.note.setOnClickListener(v->openSettings());
        cards.show(saved!=null?saved.getString("card",NativeCards.selected(this)):NativeCards.selected(this));
        setContentView(cards);cards.setOnApplyWindowInsetsListener((v,insets)->{
            Insets safe=Build.VERSION.SDK_INT>=30?insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout()):Insets.of(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());
            DisplayCutout cutout=insets.getDisplayCutout();
            if(cutout!=null)safe=Insets.of(Math.max(safe.left,cutout.getSafeInsetLeft()),Math.max(safe.top,cutout.getSafeInsetTop()),Math.max(safe.right,cutout.getSafeInsetRight()),Math.max(safe.bottom,cutout.getSafeInsetBottom()));
            cards.safeInsets(safe);return insets;
        });cards.requestApplyInsets();
    }
    void select(String id){if(!MiniAppStore.valid(id))return;NativeCards.select(this,id);cards.show(id);}
    void openSettings(){startActivity(new Intent(this,MainActivity.class).putExtra("nativeSettings",true));}
    void updateActive(){
        PowerManager power=(PowerManager)getSystemService(POWER_SERVICE);KeyguardManager keyguard=(KeyguardManager)getSystemService(KEYGUARD_SERVICE);
        if(cards!=null&&resumed&&hasWindowFocus()&&power!=null&&power.isInteractive()&&keyguard!=null&&!keyguard.isKeyguardLocked())cards.start();else if(cards!=null)cards.stop();
    }
    protected void onResume(){super.onResume();resumed=true;updateActive();if(!qaStarted&&NativeAppsQa.emulator()&&getIntent().getBooleanExtra("qaNativeApps",false)){qaStarted=true;NativeAppsQa.start(this);}}
    protected void onPause(){resumed=false;cards.stop();super.onPause();}
    public void onWindowFocusChanged(boolean focused){super.onWindowFocusChanged(focused);updateActive();if(focused)NativeLaunchContext.record(this,"cards_focus");}
    protected void onDestroy(){cards.stop();super.onDestroy();}
    protected void onSaveInstanceState(Bundle state){state.putString("card",cards.mode);super.onSaveInstanceState(state);}
    public void onConfigurationChanged(Configuration c){super.onConfigurationChanged(c);cards.requestApplyInsets();cards.requestLayout();NativeLaunchContext.record(this,"cards_configuration");}
}
