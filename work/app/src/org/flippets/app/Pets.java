package org.flippets.app;

import android.content.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.util.*;

public final class Pets {
    public static final String PREFS="pets", EVENT="org.flippets.app.EVENT";
    public static final PetState state=new PetState();
    public static final String[] EVENTS={"Ожидание","Бег","Ходьба","Музыка","Уведомление","Зарядка","Низкий заряд","Дождь","Победа ✌","Лайк","Сердечко","Большое сердце","Касание 1","Касание 2","Касание 3","Появление","NFC (просмотр)"};
    static JSONArray catalog;
    public static int scene;
    public static volatile float tiltX,tiltY;
    public static synchronized JSONArray catalog(Context c) {
        if(catalog==null) try(InputStream s=c.getAssets().open("catalog.json")) {
            ByteArrayOutputStream bytes=new ByteArrayOutputStream(); byte[] buffer=new byte[8192];int n;
            while((n=s.read(buffer))!=-1)bytes.write(buffer,0,n);
            catalog=new JSONArray(new String(bytes.toByteArray(), java.nio.charset.StandardCharsets.UTF_8));
        }catch(Exception e){catalog=new JSONArray();}
        return catalog;
    }
    public static JSONObject current(Context c) {
        JSONArray a=catalog(c); if(a.length()==0) return new JSONObject();
        SharedPreferences pref=c.getSharedPreferences(PREFS,0);int index=pref.getInt("pet",0);String id=pref.getString("petId","");if(!id.isEmpty())for(int i=0;i<a.length();i++)if(id.equals(a.optJSONObject(i).optString("id"))){index=i;break;}
        return a.optJSONObject(Math.max(0,Math.min(index,a.length()-1)));
    }
    public static void select(Context c,int index){JSONArray a=catalog(c);if(index<0||index>=a.length())return;c.getSharedPreferences(PREFS,0).edit().putInt("pet",index).putString("petId",a.optJSONObject(index).optString("id")).apply();scene=0;state.overrideUntil=0;AppLog.event(c,"SELECT",a.optJSONObject(index).optString("id"));signal(c);}
    public static String path(Context c,int index){return current(c).optJSONObject("clips")==null ? "" : current(c).optJSONObject("clips").optString(Integer.toString(index),"");}
    public static int stageIndex(Context c){long now=SystemClock.elapsedRealtime();JSONObject pet=current(c);if(pet.optString("kind").equals("reactive"))return state.index(now);if(state.overrideIndex>=0&&now<state.overrideUntil&& !path(c,state.overrideIndex).isEmpty())return state.overrideIndex;if(pet.optString("name").equals("Flowing glitter")&&SceneSettings.prefs(c,pet.optString("id")).getBoolean("gravity",true)){if(Math.abs(tiltX)+Math.abs(tiltY)<.25f)return 0;return Math.abs(tiltX)>Math.abs(tiltY)?(tiltX>0?1:2):3;}return SceneSettings.prefs(c,pet.optString("id")).getInt("scene",0);}
    public static void choose(Context c,int index){scene=index;if(!current(c).optString("kind").equals("reactive"))SceneSettings.prefs(c,current(c).optString("id")).edit().putInt("scene",index).apply();override(c,index,8000);}
    public static void signal(Context c){c.getSharedPreferences(PREFS,0).edit().putLong("changeRevision",SystemClock.elapsedRealtimeNanos()).apply();c.sendBroadcast(new Intent(EVENT).setPackage(c.getPackageName()));}
    public static void override(Context c,int index,long ms){state.overrideIndex=index;state.overrideUntil=SystemClock.elapsedRealtime()+ms;signal(c);}
    public static int battery(Context c){Intent i=c.registerReceiver(null,new IntentFilter(Intent.ACTION_BATTERY_CHANGED));if(i==null)return 0;state.charging=i.getIntExtra(BatteryManager.EXTRA_PLUGGED,0)!=0;int level=i.getIntExtra(BatteryManager.EXTRA_LEVEL,0),scale=i.getIntExtra(BatteryManager.EXTRA_SCALE,100);int pct=scale>0 ? level*100/scale:0;state.lowBattery=pct<20;return pct;}
    public static String displayReport(Context c){
        StringBuilder b=new StringBuilder("Flip Pets — диагностика\n");
        b.append(Build.MANUFACTURER).append(' ').append(Build.MODEL).append("\nAndroid ").append(Build.VERSION.RELEASE).append(" / API ").append(Build.VERSION.SDK_INT).append("\nBuild: ").append(Build.DISPLAY).append("\nIncremental: ").append(Build.VERSION.INCREMENTAL).append('\n');
        android.hardware.display.DisplayManager dm=(android.hardware.display.DisplayManager)c.getSystemService(Context.DISPLAY_SERVICE);
        for(android.view.Display d:dm.getDisplays()) {android.graphics.Point p=new android.graphics.Point();d.getRealSize(p);b.append("\nDisplay ").append(d.getDisplayId()).append(": ").append(d.getName()).append("\n").append(p.x).append('×').append(p.y).append(" flags=0x").append(Integer.toHexString(d.getFlags())).append(" state=").append(d.getState()).append('\n');}
        b.append("\nЕсли при раскрытом телефоне доступен только Display 0, APK не может сам создать второй физический экран.\nВиртуальный экран эмулятора не доказывает совместимость с MIX Flip.\n");
        return b.toString();
    }
    public static void write(Context c,String name,String text) throws IOException {File f=new File(c.getExternalFilesDir(null),name);try(FileOutputStream s=new FileOutputStream(f)){s.write(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));}}
}
