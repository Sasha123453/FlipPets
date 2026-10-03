package org.flippets.app;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.SystemClock;
import android.provider.Settings;

/** Writes on user actions, hiding, or completion; never on the one-second UI tick. */
final class UtilityTimerStore {
    static int boot(Context c){try{return Settings.Global.getInt(c.getContentResolver(),"boot_count",-1);}catch(RuntimeException e){return -1;}}
    static TimerState read(Context c){
        SharedPreferences p=c.getSharedPreferences(Pets.PREFS,0);
        return new TimerState(p.getString("utilityTimerMode","stopwatch"),p.getBoolean("utilityTimerRunning",false),p.getLong("utilityTimerElapsed",0),p.getLong("utilityTimerStart",0),p.getInt("utilityTimerBoot",-1),SystemClock.elapsedRealtime(),boot(c));
    }
    static void save(Context c,TimerState s){
        s.checkpoint(SystemClock.elapsedRealtime());s.boot=boot(c);
        c.getSharedPreferences(Pets.PREFS,0).edit().putString("utilityTimerMode",s.mode).putBoolean("utilityTimerRunning",s.running).putLong("utilityTimerElapsed",s.accumulated).putLong("utilityTimerStart",s.started).putInt("utilityTimerBoot",s.boot).apply();
    }
    static void checkpoint(Context c){TimerState s=read(c);if(s.running)save(c,s);}
}
