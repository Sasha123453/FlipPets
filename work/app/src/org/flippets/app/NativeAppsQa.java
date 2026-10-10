package org.flippets.app;
import android.app.*;
import android.content.*;
import android.content.pm.ActivityInfo;
import android.graphics.*;
import android.os.*;
import android.view.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.*;

/** Emulator-only real card input/lifecycle QA, with a random isolated origin. */
final class NativeAppsQa {
    static NativeAppsQa active;CoverAppsActivity a;final Handler h=new Handler(Looper.getMainLooper());JSONArray rows=new JSONArray();
    String token,origin,binary,oldSelected,globalBefore;boolean oldPresent,ended,captured;int failed,oldOrientation;
    MainActivity settingsMain;boolean observingActivities;
    final Application.ActivityLifecycleCallbacks activities=new Application.ActivityLifecycleCallbacks(){
        public void onActivityCreated(Activity activity,Bundle state){if(activity instanceof MainActivity&&activity.getIntent().getBooleanExtra("nativeSettings",false))settingsMain=(MainActivity)activity;}
        public void onActivityStarted(Activity activity){}public void onActivityResumed(Activity activity){}public void onActivityPaused(Activity activity){}
        public void onActivityStopped(Activity activity){}public void onActivitySaveInstanceState(Activity activity,Bundle state){}public void onActivityDestroyed(Activity activity){}
    };
    NativeAppsQa(CoverAppsActivity a){this.a=a;}
    static boolean emulator(){return Build.HARDWARE.contains("ranchu")||Build.HARDWARE.contains("goldfish");}
    static void attach(CoverAppsActivity a){if(active!=null&&!active.ended)active.a=a;}
    static void start(CoverAppsActivity a){if(!emulator())throw new IllegalStateException("Emulator only");if(active!=null&&!active.ended){active.a=a;return;}active=new NativeAppsQa(a);active.later(active::begin,500);}
    File checkpoint(){return new File(a.getFilesDir(),"native-cards-qa-checkpoint.json");}
    void check(String name,boolean ok){try{rows.put(new JSONObject().put("test",name).put("ok",ok));}catch(Exception ignored){}if(!ok)failed++;}
    void later(Runnable r,long delay){h.postDelayed(()->{if(ended)return;try{r.run();}catch(Throwable e){check("unexpected_"+e.getClass().getSimpleName(),false);finish();}},delay);}
    void waitFor(BooleanSupplier condition,Runnable next,String name){long deadline=SystemClock.elapsedRealtime()+12000;poll(condition,next,name,deadline);}
    void poll(BooleanSupplier condition,Runnable next,String name,long deadline){if(condition.getAsBoolean()){later(()->{if(condition.getAsBoolean())next.run();else poll(condition,next,name,deadline);},350);return;}if(SystemClock.elapsedRealtime()>deadline){check(name+"_timeout",false);finish();return;}later(()->poll(condition,next,name,deadline),100);}
    void ready(String mode,Runnable next){waitFor(()->a.cards.active&&a.cards.ready&&a.cards.mode.equals(mode),next,"ready_"+mode);}
    void read(String expression,Consumer<JSONObject> next){a.cards.web.evaluateJavascript("JSON.stringify("+expression+")",r->{if(ended)return;try{next.accept(new JSONObject(new JSONTokener(r).nextValue().toString()));}catch(Throwable e){check("javascript_read_error",false);finish();}});}
    void tap(JSONObject p){View decor=a.getWindow().getDecorView();int[] webLocation=new int[2],decorLocation=new int[2];a.cards.web.getLocationOnScreen(webLocation);decor.getLocationOnScreen(decorLocation);float x=webLocation[0]-decorLocation[0]+(float)p.optDouble("x")*a.cards.web.getWidth()/976f,y=webLocation[1]-decorLocation[1]+(float)p.optDouble("y")*a.cards.web.getHeight()/a.cards.canvasHeight;long now=SystemClock.uptimeMillis();MotionEvent down=MotionEvent.obtain(now,now,0,x,y,0),up=MotionEvent.obtain(now,now+80,1,x,y,0);decor.dispatchTouchEvent(down);decor.dispatchTouchEvent(up);down.recycle();up.recycle();}
    String fingerprint()throws Exception{
        JSONArray all=new JSONArray();for(String name:new String[]{Pets.PREFS,MiniAppStore.PREFS}){
            Map<String,?> values=a.getSharedPreferences(name,0).getAll();for(String key:new TreeSet<>(values.keySet())){Object v=values.get(key);if(v instanceof Set)v=new JSONArray(new TreeSet<>((Set<String>)v));all.put(new JSONArray().put(name).put(key).put(v));}
        }byte[] digest=MessageDigest.getInstance("SHA-256").digest(all.toString().getBytes(StandardCharsets.UTF_8));StringBuilder out=new StringBuilder();for(byte b:digest)out.append(String.format(Locale.ROOT,"%02x",b&255));return out.toString();
    }
    void begin(){try{
        token=a.getIntent().getStringExtra("qaToken");origin=a.cards.qaOrigin;binary=Qa.binarySha(a);
        if(token==null||!token.matches("[a-z0-9-]{1,64}")||!origin.equals("qa-native-"+token+".invalid"))throw new IllegalStateException("Invalid QA origin/token");
        if(a.getIntent().getBooleanExtra("qaPhase2",false)){secondPhase();return;}
        oldPresent=NativeCards.prefs(a).contains("selected");oldSelected=NativeCards.prefs(a).getString("selected",null);oldOrientation=a.getRequestedOrientation();globalBefore=fingerprint();captured=true;
        a.getApplication().registerActivityLifecycleCallbacks(activities);observingActivities=true;
        a.select("water");ready("water",this::water);
    }catch(Exception e){check("begin_error",false);finish();}}
    void water(){
        check("native_origin",a.cards.nativeLaunch&&a.cards.web.getUrl().startsWith("https://"+origin+"/"));
        int forbidden=WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON|WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON|WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED;
        check("foreground_only_flags",(a.getWindow().getAttributes().flags&forbidden)==0);
        boolean guard=false;for(ActivityManager.RunningServiceInfo s:((ActivityManager)a.getSystemService(Context.ACTIVITY_SERVICE)).getRunningServices(64))if(s.service.getClassName().equals(CoverGuard.class.getName()))guard=true;
        check("no_cover_membership",PetActivity.covers.isEmpty()&&!guard);
        android.webkit.WebSettings s=a.cards.web.getSettings();check("offline_settings",s.getBlockNetworkLoads()&&!s.getAllowFileAccess()&&!s.getAllowContentAccess()&&s.getDomStorageEnabled());
        read("({height:CANVAS_H,width:CANVAS_W,cups:state.cups,bridge:typeof Android,x:(BTN_X+BTN_W/2)*FIT+DX,y:(BTN_Y+BTN_H/2)*FIT+DY})",p->{
            check("no_native_bridge","undefined".equals(p.optString("bridge")));check("first_measured_canvas",p.optInt("width")==976&&p.optInt("height")==Math.round(976f*a.cards.getHeight()/a.cards.getWidth()));check("water_empty_qa_storage",p.optInt("cups")==0);tap(p);
            later(()->read("({cups:state.cups,saved:JSON.parse(localStorage.getItem('water_progress_v1')).cups})",q->{check("water_touch",q.optInt("cups")==1&&q.optInt("saved")==1);capture("native-water.png",()->{a.cards.load();ready("water",()->read("({cups:state.cups})",v->{check("water_persistence",v.optInt("cups")==1);check("nav_focus",a.cards.tabs.findViewWithTag("focus").performClick());ready("focus",this::focus);}));});}),500);
        });
    }
    void focus(){capture("native-focus.png",()->read("(()=>{const W=window.__DIAL_CANVAS_SIZE.width,H=window.__DIAL_CANVAS_SIZE.height,CAM=Math.floor(W/3),FIT=Math.min((W-CAM)/608,H/596),DX=Math.round((CAM+(W-CAM)/2)-608*FIT),DY=Math.round((H-596*FIT)/2);return {x:636.5*FIT+DX,y:530*FIT+DY};})()",p->{tap(p);later(()->read("JSON.parse(localStorage.getItem('pomodoro_v1'))",q->{check("focus_touch_start",q.optBoolean("running")&&q.optLong("endAt")>System.currentTimeMillis());tap(p);later(()->read("JSON.parse(localStorage.getItem('pomodoro_v1'))",v->{check("focus_touch_pause",!v.optBoolean("running"));check("nav_words",a.cards.tabs.findViewWithTag("words").performClick());ready("words",this::words);}),350);}),400);}));}
    void words(){read("({x:unkBtnCenter().x*FIT+DX,y:unkBtnCenter().y*FIT+DY})",p->{tap(p);later(()->read("({index:state.cardIdx,unknown:Object.keys(state.unknown).length,x:knowBtnCenter().x*FIT+DX,y:knowBtnCenter().y*FIT+DY})",q->{check("words_touch_unknown",q.optInt("index")==1&&q.optInt("unknown")==1);tap(q);later(()->read("({index:state.cardIdx})",v->{check("words_touch_known",v.optInt("index")==2);capture("native-words.png",this::rotate);}),400);}),400);});}
    void rotate(){try{check("native_selection_isolated",NativeCards.selected(a).equals("words")&&globalBefore.equals(fingerprint()));}catch(Exception e){check("native_selection_isolated",false);}
        int before=a.cards.getWidth();android.webkit.WebView previous=a.cards.web;a.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE);waitFor(()->a.cards.getWidth()!=before&&a.cards.active&&a.cards.ready&&a.cards.web!=previous,()->read("({height:CANVAS_H,index:state.cardIdx})",p->{check("rotation_measured_canvas",p.optInt("height")==Math.round(976f*a.cards.getHeight()/a.cards.getWidth()));check("rotation_state",p.optInt("index")==2);a.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);waitFor(()->a.cards.getWidth()==before&&a.cards.ready,this::recreate,"portrait");}),"landscape");
    }
    void recreate(){CoverAppsActivity old=a;a.recreate();waitFor(()->a!=old&&a.cards.ready,()->read("({index:state.cardIdx})",p->{check("recreate_selection_state",NativeCards.selected(a).equals("words")&&a.cards.mode.equals("words")&&p.optInt("index")==2);request("broadcast");waitFor(()->ack("broadcast"),()->{check("stop_cover_preserves_native",!a.isFinishing()&&a.cards.active&&a.cards.ready);a.cards.note.performClick();waitFor(()->!a.cards.active&&a.cards.web==null&&settingsMain!=null,()->{request("settings-intent");waitFor(()->token.equals(settingsMain.getIntent().getStringExtra("qaIntentProof"))&&!settingsMain.getIntent().getBooleanExtra("nativeSettings",false),()->{check("settings_hidden_release",!a.cards.active&&a.cards.web==null);request("settings-back");ready("words",()->{check("settings_back_state",a.cards.mode.equals("words"));request("home");waitFor(()->!a.cards.active&&a.cards.web==null,()->{check("home_hidden_release",true);request("resume");ready("words",()->{check("home_resume_state",a.cards.mode.equals("words"));processCheckpoint();});},"home_hidden");});},"settings_new_intent");},"settings_hidden");},"broadcast_ack");}),"activity_recreation");}
    void processCheckpoint(){try{a.select("water");ready("water",()->{try{
        JSONObject saved=new JSONObject().put("token",token).put("origin",origin).put("apk",binary).put("rows",rows).put("failed",failed).put("oldPresent",oldPresent).put("oldSelected",oldSelected==null?JSONObject.NULL:oldSelected).put("oldOrientation",oldOrientation).put("global",globalBefore);
        try(FileOutputStream out=new FileOutputStream(checkpoint())){out.write(saved.toString().getBytes(StandardCharsets.UTF_8));out.getFD().sync();}request("process");
    }catch(Exception e){check("checkpoint_error",false);finish();}});}catch(Exception e){check("checkpoint_error",false);finish();}}
    void secondPhase()throws Exception{
        JSONObject saved=new JSONObject(new String(java.nio.file.Files.readAllBytes(checkpoint().toPath()),StandardCharsets.UTF_8));if(!token.equals(saved.getString("token"))||!origin.equals(saved.getString("origin"))||!binary.equals(saved.getString("apk")))throw new IllegalStateException("Stale checkpoint");
        rows=saved.getJSONArray("rows");failed=saved.getInt("failed");oldPresent=saved.getBoolean("oldPresent");oldSelected=saved.isNull("oldSelected")?null:saved.getString("oldSelected");oldOrientation=saved.getInt("oldOrientation");globalBefore=saved.getString("global");captured=true;
        ready("water",()->read("({cups:state.cups})",p->{check("native_process_recreation",NativeCards.selected(a).equals("water")&&a.cards.mode.equals("water"));check("native_process_storage",p.optInt("cups")==1);finish();}));
    }
    void request(String phase){try{Pets.write(a,"native-cards-qa-pending.json",new JSONObject().put("phase",phase).put("token",token).put("apkSha256",binary).toString());}catch(Exception e){check("host_handshake_error",false);finish();}}
    boolean ack(String phase){try{JSONObject p=new JSONObject(new String(java.nio.file.Files.readAllBytes(new File(a.getExternalFilesDir(null),"native-cards-qa-ack.json").toPath()),StandardCharsets.UTF_8));return token.equals(p.optString("token"))&&binary.equals(p.optString("apkSha256"))&&phase.equals(p.optString("phase"));}catch(Exception e){return false;}}
    void capture(String name,Runnable next){Bitmap bitmap=Bitmap.createBitmap(a.getWindow().getDecorView().getWidth(),a.getWindow().getDecorView().getHeight(),Bitmap.Config.ARGB_8888);PixelCopy.request(a.getWindow(),bitmap,status->{try{Set<Integer> colors=new HashSet<>();int count=0,lit=0;for(int y=0;y<bitmap.getHeight();y+=7)for(int x=0;x<bitmap.getWidth();x+=7){int c=bitmap.getPixel(x,y);colors.add(c);count++;if((c&0xffffff)!=0)lit++;}check("capture_"+name,status==PixelCopy.SUCCESS&&colors.size()>32&&lit>count/20);try(FileOutputStream out=new FileOutputStream(new File(a.getExternalFilesDir(null),name))){bitmap.compress(Bitmap.CompressFormat.PNG,100,out);}bitmap.recycle();later(next,100);}catch(Exception e){bitmap.recycle();check("capture_error",false);finish();}},h);}
    void finish(){if(ended)return;ended=true;h.removeCallbacksAndMessages(null);if(observingActivities){a.getApplication().unregisterActivityLifecycleCallbacks(activities);observingActivities=false;}try{
        if(captured){SharedPreferences p=NativeCards.prefs(a);SharedPreferences.Editor edit=p.edit().remove("selected");if(oldPresent)edit.putString("selected",oldSelected);edit.commit();check("preferences_restored",oldPresent==p.contains("selected")&&Objects.equals(oldSelected,p.getString("selected",null)));check("global_preferences_preserved",globalBefore!=null&&globalBefore.equals(fingerprint()));a.setRequestedOrientation(oldOrientation);checkpoint().delete();}
        Pets.write(a,"native-cards-qa.json",new JSONObject().put("apkSha256",Qa.binarySha(a)).put("token",token).put("tested",rows.length()).put("failed",failed).put("results",rows).put("skipped",new JSONArray()).put("environment","Android emulator; app-owned Activity only, not Xiaomi admission/physical continuity proof").toString(2));
    }catch(Exception ignored){}active=null;
    }
}
