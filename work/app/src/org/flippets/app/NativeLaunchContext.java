package org.flippets.app;

import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.os.*;
import android.view.*;
import org.json.*;
import java.util.ArrayDeque;

/** Bounded, in-memory observations of our own two ordinary Activities only. */
final class NativeLaunchContext {
    static final int LIMIT=24;
    private static final ArrayDeque<JSONObject> recent=new ArrayDeque<>();
    private static JSONObject rect(Rect r)throws JSONException{
        return new JSONObject().put("left",r.left).put("top",r.top).put("right",r.right).put("bottom",r.bottom);
    }
    private static JSONObject insets(Insets i)throws JSONException{
        return new JSONObject().put("left",i.left).put("top",i.top).put("right",i.right).put("bottom",i.bottom);
    }
    private static JSONObject windowInsets(WindowInsets w)throws JSONException{
        if(w==null)return null;
        Insets bars=Build.VERSION.SDK_INT>=30?w.getInsets(WindowInsets.Type.systemBars()):Insets.of(w.getSystemWindowInsetLeft(),w.getSystemWindowInsetTop(),w.getSystemWindowInsetRight(),w.getSystemWindowInsetBottom());
        JSONObject out=new JSONObject().put("systemBars",insets(bars));
        if(Build.VERSION.SDK_INT>=30)out.put("systemBarsIgnoringVisibility",insets(w.getInsetsIgnoringVisibility(WindowInsets.Type.systemBars())));
        DisplayCutout c=w.getDisplayCutout();
        JSONArray boxes=new JSONArray();
        if(c!=null)for(Rect r:c.getBoundingRects())boxes.put(rect(r));
        return out.put("cutoutBounds",boxes).put("cutoutSafe",insets(c==null?Insets.NONE:Insets.of(c.getSafeInsetLeft(),c.getSafeInsetTop(),c.getSafeInsetRight(),c.getSafeInsetBottom())));
    }
    static JSONObject snapshot(Activity a,String event)throws JSONException{
        if(!(a instanceof MainActivity)&&!(a instanceof CoverAppsActivity))throw new IllegalArgumentException("Ordinary Flip Pets Activities only");
        Display d=Build.VERSION.SDK_INT>=30?a.getDisplay():a.getWindowManager().getDefaultDisplay();
        JSONObject row=new JSONObject().put("activity",a.getClass().getSimpleName()).put("event",event)
            .put("elapsedRealtimeMs",SystemClock.elapsedRealtime()).put("densityDpi",a.getResources().getDisplayMetrics().densityDpi)
            .put("focused",a.hasWindowFocus()).put("nativeRoutingEnabled",NativeCards.enabled(a))
            .put("settingsBypass",a.getIntent().getBooleanExtra("nativeSettings",false));
        PowerManager power=(PowerManager)a.getSystemService(Context.POWER_SERVICE);
        KeyguardManager keyguard=(KeyguardManager)a.getSystemService(Context.KEYGUARD_SERVICE);
        row.put("awake",power!=null&&power.isInteractive()).put("locked",keyguard==null||keyguard.isKeyguardLocked());
        JSONObject declarations=new JSONObject().put("lookupSupported",Build.VERSION.SDK_INT>=31)
            .put("dumpPermissionGranted",a.checkSelfPermission("android.permission.DUMP")==PackageManager.PERMISSION_GRANTED)
            .put("shellAdmissionMutationEnabled",false);
        if(Build.VERSION.SDK_INT>=31){
            try{PackageManager.Property p=a.getPackageManager().getProperty("miui.continuity.policy",a.getComponentName());declarations.put("admissionIsInteger",p.isInteger()).put("admissionValue",p.getInteger());}catch(PackageManager.NameNotFoundException e){declarations.put("admissionValue",JSONObject.NULL);}
            try{PackageManager.Property p=a.getPackageManager().getProperty("miui.supportFlipWatchOverlayGroupView",a.getComponentName());declarations.put("widgetOverlayIsBoolean",p.isBoolean()).put("widgetOverlayValue",p.getBoolean());}catch(PackageManager.NameNotFoundException e){declarations.put("widgetOverlayValue",JSONObject.NULL);}
        }
        try{Bundle metadata=a.getPackageManager().getActivityInfo(a.getComponentName(),PackageManager.GET_META_DATA).metaData;Object value=metadata==null?null:metadata.get("miui.supportFlipFullScreen");declarations.put("fullscreenIsInteger",value instanceof Integer).put("fullscreenValue",value==null?JSONObject.NULL:value);}catch(PackageManager.NameNotFoundException ignored){}
        row.put("nativePolicyDeclarations",declarations);
        if(d!=null){Display.Mode mode=d.getMode();
            row.put("displayId",d.getDisplayId()).put("displayFlags",d.getFlags()).put("displayState",d.getState())
                .put("displayValid",d.isValid()).put("rotation",d.getRotation())
                .put("physicalModeWidth",mode.getPhysicalWidth()).put("physicalModeHeight",mode.getPhysicalHeight());
        }
        if(Build.VERSION.SDK_INT>=30){
            WindowMetrics current=a.getWindowManager().getCurrentWindowMetrics(),max=a.getWindowManager().getMaximumWindowMetrics();
            row.put("currentWindowBounds",rect(current.getBounds())).put("maximumWindowBounds",rect(max.getBounds()))
                .put("currentWindowInsets",windowInsets(current.getWindowInsets())).put("maximumWindowInsets",windowInsets(max.getWindowInsets()));
        }else{Rect bounds=new Rect();a.getWindowManager().getDefaultDisplay().getRectSize(bounds);
            row.put("currentWindowBounds",rect(bounds)).put("maximumWindowBounds",JSONObject.NULL);
        }
        row.put("decorInsets",a.getWindow().getDecorView().getRootWindowInsets()==null?JSONObject.NULL:windowInsets(a.getWindow().getDecorView().getRootWindowInsets()));
        row.put("routeMatches",NativeCoverRoute.isCover(a));
        return row;
    }
    static void record(Activity a,String event){
        try{JSONObject row=snapshot(a,event);synchronized(recent){while(recent.size()>=LIMIT)recent.removeFirst();recent.addLast(row);}}
        catch(RuntimeException|JSONException ignored){} // Diagnostic failure must never change routing/lifecycle.
    }
    static JSONObject report(Activity a,String apkSha256)throws Exception{
        record(a,"manual_export");JSONArray rows=new JSONArray();synchronized(recent){for(JSONObject row:recent)rows.put(row);}
        return new JSONObject().put("schemaVersion",1).put("device",Build.DEVICE).put("build",Build.VERSION.INCREMENTAL)
            .put("sdk",Build.VERSION.SDK_INT).put("apkSha256",apkSha256).put("observations",rows)
            .put("scope","Own Activity metrics only; no admission, policy baseline, physical camera, native motion or restore proof")
            .put("policyGrantPerformed",false).put("nativeApplyPerformed",false);
    }
    static void show(Activity a){
        final JSONObject report;
        try{report=report(a,"");}catch(Exception e){return;}
        // Hashing the APK is an explicit export action, outside the UI thread.
        new Thread(()->{try{String text=report.put("apkSha256",Qa.binarySha(a)).toString(2);a.runOnUiThread(()->{
            if(a.isFinishing()||a.isDestroyed())return;
            new AlertDialog.Builder(a).setTitle("Контекст запуска карточек").setMessage(text)
                .setPositiveButton("Сохранить отчёт",(dialog,which)->{try{Pets.write(a,"native-launch-context.json",text);new AlertDialog.Builder(a).setMessage("Отчёт сохранён в папке приложения: native-launch-context.json").setPositiveButton("Готово",null).show();}catch(Exception e){new AlertDialog.Builder(a).setMessage("Не удалось сохранить отчёт.").setPositiveButton("Готово",null).show();}})
                .setNeutralButton("Скопировать",(dialog,which)->((ClipboardManager)a.getSystemService(Context.CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("Контекст запуска",text)))
                .setNegativeButton("Закрыть",null).show();
        });}catch(Exception e){a.runOnUiThread(()->{if(!a.isFinishing()&&!a.isDestroyed())new AlertDialog.Builder(a).setMessage("Не удалось собрать контекст запуска.").setPositiveButton("Готово",null).show();});}},"native-context-export").start();
    }
}
