package org.flippets.app;

public class FlipPetsApp extends android.app.Application {
    protected void attachBaseContext(android.content.Context c){super.attachBaseContext(c);rikka.shizuku.ShizukuProvider.disableAutomaticSuiInitialization();}
    public static int frameRate(android.content.Context c){return Math.max(8,Math.min(30,c.getSharedPreferences(Pets.PREFS,0).getInt("frameRate",20)));}
    public void onCreate(){super.onCreate();AppLog.install(this);boolean emulator=android.os.Build.HARDWARE.contains("ranchu")||android.os.Build.HARDWARE.contains("goldfish");boolean compatible=getSharedPreferences(Pets.PREFS,0).getBoolean("softwareDecoder",false);org.libpag.VideoDecoder.SetMaxHardwareDecoderCount(emulator||compatible?0:4);AppLog.event(this,"START","build="+android.os.Build.DISPLAY+" hardware="+android.os.Build.HARDWARE+" decoder="+(emulator||compatible?"software":"hardware allowed")+" fps="+frameRate(this));}
}
