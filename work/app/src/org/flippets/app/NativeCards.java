package org.flippets.app;
import android.content.*;

/** Native-launch navigation is independent of the supervised pet/card selection. */
final class NativeCards {
    static final String PREFS="native-cards";
    static SharedPreferences prefs(Context c){return c.getSharedPreferences(PREFS,0);}
    static String selected(Context c){String id=prefs(c).getString("selected","focus");return MiniAppStore.valid(id)?id:"focus";}
    static void select(Context c,String id){if(MiniAppStore.valid(id))prefs(c).edit().putString("selected",id).apply();}
    static boolean enabled(Context c){return prefs(c).getBoolean("coverLaunch",false);}
}
