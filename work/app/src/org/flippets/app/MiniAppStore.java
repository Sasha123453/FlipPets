package org.flippets.app;
import android.content.*;
/** Explicit choice only. Original cards keep their own private localStorage state. */
final class MiniAppStore {
    static final String PREFS="mini-apps";
    static SharedPreferences prefs(Context c){return c.getSharedPreferences(PREFS,0);}
    static boolean valid(String id){return "focus".equals(id)||"water".equals(id)||"words".equals(id);}
    static String selected(Context c){String id=prefs(c).getString("selected","none");return valid(id)?id:"none";}
    static int sourceId(String id){return "focus".equals(id)?5:"water".equals(id)?1:3;}
    static String title(String id){return "focus".equals(id)?"Pomodoro Xiaomi":"water".equals(id)?"Вода Xiaomi":"Слова Xiaomi";}
    static void select(Context c,String id){prefs(c).edit().putString("selected",valid(id)?id:"none").apply();c.sendBroadcast(new Intent(Pets.EVENT).setPackage(c.getPackageName()));}
}
