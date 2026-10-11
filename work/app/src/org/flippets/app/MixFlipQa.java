package org.flippets.app;

import android.content.SharedPreferences;
import android.os.*;
import android.view.*;
import org.json.*;
import java.util.*;

/** Real app renderer/touches and natural finite playback. Emulator only; never invokes OEM/Shizuku. */
final class MixFlipQa {
    static final String[] STEMS={"dewen","shuitun","shuita","bixiong","xianluo","heibao"};
    final MainActivity a;final Handler h=new Handler(Looper.getMainLooper());final JSONArray rows=new JSONArray();final Map<SharedPreferences,Map<String,?>> saved=new HashMap<>();
    final QaPetMode mode;final int oldScene=Pets.scene,oldOverride=Pets.state.overrideIndex;final long oldUntil=Pets.state.overrideUntil,oldRevision=Pets.playRevision;
    int pet,scene,failed,charlieScene;long deadline;double held;String stem;boolean finished;
    MixFlipQa(MainActivity a){this.a=a;SharedPreferences main=a.getSharedPreferences(Pets.PREFS,0);save(main);save(MiniAppStore.prefs(a));for(String s:STEMS)save(SceneSettings.prefs(a,"mixflip-"+s));save(SceneSettings.prefs(a,"bird-pandora"));mode=new QaPetMode(a);}
    void save(SharedPreferences p){saved.put(p,new HashMap<>(p.getAll()));}
    static void start(MainActivity a){if(!NativeAppsQa.emulator())throw new SecurityException("Emulator only");new MixFlipQa(a).begin();}
    void record(String name,boolean ok){try{rows.put(new JSONObject().put("test",name).put("ok",ok));}catch(Exception ignored){}if(!ok)failed++;}
    void later(Runnable next,long ms){h.postDelayed(()->{if(finished)return;try{if(a.isDestroyed()||!a.preview.running)throw new IllegalStateException("Stage stopped");next.run();}catch(Throwable e){record("unexpected_error",false);finish();}},ms);}
    void begin(){try{
        String summary=NativePetState.summarize("{\"pets\":{\"petType\":2}}","[{\"pets\":{\"petType\":2}},{\"pets\":{\"petType\":4}}]");record("native_summary_fixed_labels",summary.contains("Капибара")&&summary.contains("2 / 3")&&summary.contains("свободно 1"));
        String privateInput="{\"privatePhoto\":\"sensitive-path\",\"name\":\"private-name\"}";record("native_summary_excludes_private_fields",!NativePetState.summarize(privateInput,"["+privateInput+"]").contains("private"));
        boolean rejected=false;try{NativePetState.summarize("{}","{}");}catch(JSONException expected){rejected=true;}record("native_summary_refuses_unknown_history",rejected);nextPet();
    }catch(Throwable e){record("setup_error",false);finish();}}
    void nextPet(){if(pet==STEMS.length){charlieStart();return;}stem=STEMS[pet];scene=0;int index=-1;for(int i=0;i<Pets.catalog(a).length();i++)if(Pets.catalog(a).optJSONObject(i).optString("id").equals("mixflip-"+stem))index=i;
        if(index<0)throw new IllegalStateException("Missing pet");SceneSettings.prefs(a,"mixflip-"+stem).edit().remove("scene").apply();a.select(index);later(this::loaded,600);
    }
    void touch(){View target=a.preview.pag;long now=SystemClock.uptimeMillis();float x=target.getWidth()*.7f,y=target.getHeight()*.7f;MotionEvent down=MotionEvent.obtain(now,now,MotionEvent.ACTION_DOWN,x,y,0),up=MotionEvent.obtain(now,now+60,MotionEvent.ACTION_UP,x,y,0);target.dispatchTouchEvent(down);target.dispatchTouchEvent(up);down.recycle();up.recycle();}
    void loaded(){PetStage s=a.preview;JSONObject p=Pets.current(a);float[] actual=new float[9];s.pag.matrix().getValues(actual);org.libpag.PAGComposition f=s.pag.getComposition();
        float[] expected=f==null?new float[4]:MixFlipGeometry.matrix(s.getWidth(),s.getHeight(),f.width(),f.height(),p.optInt("nativePetType"),0,s.previewClockRotation);
        record(stem+"_loaded_original_geometry",f!=null&&s.loaded.endsWith("pag_0.pag")&&s.pag.repeatCount()==1&&GalleryDialog.collection(p).equals("MIX Flip")&&s.backdrop.nativeForeground!=null&&Math.abs(actual[0]-expected[0])<.001&&Math.abs(actual[2]-expected[2])<.001&&Math.abs(actual[5]-expected[3])<.001&&!PetLayout.supported(p));
        boolean playing=s.pag.isPlaying();touch();later(()->{record(stem+"_busy_tap_ignored",playing&&Pets.stageIndex(a)==0&&a.preview.loaded.endsWith("pag_0.pag"));waitEnd();},200);
    }
    void waitEnd(){org.libpag.PAGComposition f=a.preview.pag.getComposition();deadline=SystemClock.elapsedRealtime()+(f==null?1000:f.duration()/1000+8000);poll();}
    void poll(){PetStage s=a.preview;double progress=s.pag.getProgress();if(!s.pag.isPlaying()&&progress>=.999999){held=progress;later(this::ended,450);return;}if(SystemClock.elapsedRealtime()>deadline){record(stem+"_scene"+scene+"_finite_hold",false);finish();return;}later(this::poll,150);}
    void ended(){PetStage s=a.preview;record(stem+"_scene"+scene+"_finite_hold",!s.pag.isPlaying()&&s.pag.getProgress()==held&&s.pag.repeatCount()==1);int next=(scene+1)%3;touch();later(()->{record(stem+"_scene"+scene+"_tap_next",Pets.stageIndex(a)==next&&a.preview.loaded.endsWith("pag_"+next+".pag")&&a.preview.pag.isPlaying());scene++;if(scene<3)waitEnd();else restart();},450);}
    void restart(){PetStage s=a.preview;s.stop();record(stem+"_stop_releases",s.pag.getComposition()==null&&s.loaded.isEmpty()&&!s.running&&s.backdrop.nativeForeground==null);s.start();later(()->{record(stem+"_restart_plays_saved_scene",a.preview.loaded.endsWith("pag_0.pag")&&a.preview.pag.getComposition()!=null&&a.preview.pag.isPlaying());pet++;nextPet();},600);}
    void charlieStart(){SceneSettings.prefs(a,"bird-pandora").edit().clear().commit();int index=-1;for(int i=0;i<Pets.catalog(a).length();i++)if(Pets.catalog(a).optJSONObject(i).optString("id").equals("bird-pandora"))index=i;
        if(index<0)throw new IllegalStateException("Charlie missing");a.select(index);charlieScene=0;charlieLoad();}
    void charlieLoad(){Pets.choose(a,charlieScene);deadline=SystemClock.elapsedRealtime()+5000;later(this::charlieLoaded,400);}
    boolean charlieMatrix(float manual,float dx,float dy){try{JSONObject root;try(java.io.InputStream in=a.getAssets().open("native-pet-layout.json")){root=new JSONObject(new String(in.readAllBytes(),java.nio.charset.StandardCharsets.UTF_8));}
        JSONObject p=root.getJSONObject("layouts").getJSONObject("bird-pandora");PetStage s=a.preview;float fit=Math.min(s.getWidth()/1208f,s.getHeight()/1392f),ox=(s.getWidth()-1208*fit)/2,oy=(s.getHeight()-1392*fit)/2;
        float[] m=new float[9];s.pag.matrix().getValues(m);float scale=(float)p.getDouble("scale"),x=(float)p.getDouble("x"),y=(float)p.getDouble("y"),r=(float)p.getDouble("subjectRight"),b=(float)p.getDouble("subjectBottom");
        return Math.abs(m[0]-scale*fit*manual)<.002&&Math.abs(m[4]-m[0])<.002&&Math.abs(m[2]-(ox+(r+(x-r)*manual)*fit+dx*s.getWidth()))<.002&&Math.abs(m[5]-(oy+(b+(y-b)*manual)*fit+dy*s.getHeight()))<.002;
    }catch(Exception e){return false;}}
    void charlieLoaded(){PetStage s=a.preview;String path=Pets.current(a).optJSONObject("clips").optString(""+charlieScene);if(s.pag.getComposition()==null||!path.equals(s.loaded)){if(SystemClock.elapsedRealtime()<deadline){later(this::charlieLoaded,100);return;}throw new IllegalStateException("Charlie load timeout");}
        record("charlie_scene"+charlieScene+"_native_geometry",s.pag.getComposition().width()==976&&s.pag.getComposition().height()==596&&charlieMatrix(1,0,0));
        if(++charlieScene<12){charlieLoad();return;}
        s.previewLayout(new PetLayoutProfile(true,1,0,0));later(()->{record("charlie_clockless_same_native_size",charlieMatrix(1,0,0)&&!s.backdrop.clockEnabled()&&!PetLayout.read(a,Pets.current(a)).clockless);s.previewLayout(new PetLayoutProfile(false,1.1f,.05f,-.03f));later(()->{
            record("charlie_manual_relative_to_native",charlieMatrix(1.1f,.05f,-.03f)&&PetLayout.read(a,Pets.current(a)).scale==1);s.previewLayout(null);later(()->{record("charlie_cancel_native_geometry",charlieMatrix(1,0,0)&&s.backdrop.clockEnabled());s.stop();record("charlie_stop_releases",s.pag.getComposition()==null&&s.loaded.isEmpty()&&!s.running);s.start();finish();},350);
        },350);},350);
    }
    @SuppressWarnings("unchecked") void finish(){if(finished)return;finished=true;h.removeCallbacksAndMessages(null);a.preview.stop();boolean restored=true;
        for(Map.Entry<SharedPreferences,Map<String,?>> entry:saved.entrySet()){SharedPreferences.Editor e=entry.getKey().edit().clear();for(Map.Entry<String,?> v:entry.getValue().entrySet()){Object x=v.getValue();if(x instanceof String)e.putString(v.getKey(),(String)x);else if(x instanceof Integer)e.putInt(v.getKey(),(Integer)x);else if(x instanceof Long)e.putLong(v.getKey(),(Long)x);else if(x instanceof Float)e.putFloat(v.getKey(),(Float)x);else if(x instanceof Boolean)e.putBoolean(v.getKey(),(Boolean)x);else if(x instanceof Set)e.putStringSet(v.getKey(),(Set<String>)x);}e.commit();restored&=entry.getKey().getAll().equals(entry.getValue());}
        Pets.scene=oldScene;Pets.state.overrideIndex=oldOverride;Pets.state.overrideUntil=oldUntil;Pets.playRevision=oldRevision;record("preferences_restored",restored);a.preview.start();a.refreshSelection();
        try{Pets.write(a,"mixflip-qa.json",new JSONObject().put("apkSha256",Qa.binarySha(a)).put("tested",rows.length()).put("failed",failed).put("skipped",new JSONArray()).put("results",rows).toString(2));}catch(Exception ignored){}
    }
}
