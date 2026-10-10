package org.flippets.app;

import android.content.*;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.*;
import android.view.View;
import org.json.*;
import org.libpag.PAGView;
import java.util.*;
import java.io.*;

/** Emulator-only real-player observations. No progress injection or synthetic timelines. */
public final class Donor18Qa {
    private static volatile boolean running;
    private static final String CARP="butterfly-carp-hongkong",VORTEX="vortex-hongkong",PIN="pin-hongkong";
    private static final String[] IDS={CARP,VORTEX,PIN},GLOBAL_KEYS={"pet","petId","changeRevision"};
    private static final String[] LAYOUT_KEYS={"petClockless","petClockScale","petClockX","petClockY","petLargeScale","petLargeX","petLargeY"};
    private final PetActivity activity;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final JSONArray results=new JSONArray();
    private final Map<String,Map<String,?>> savedScenes=new HashMap<>();
    private final Map<String,Object> savedGlobal=new HashMap<>();
    private final long began=SystemClock.elapsedRealtime();
    private String initialSha;
    private QaPetMode petMode;
    private final List<StartObservation> sourceStarts=Collections.synchronizedList(new ArrayList<>());
    private final JSONArray cycleDiagnostics=new JSONArray(),phaseDiagnostics=new JSONArray();
    private String diagnosticPhase="";
    private float minimumPollAlpha=1;
    private long cycleOutTime,cycleHiddenTime,cycleNativeHiddenTime,cycleInTime,cycleChangedTime;
    private volatile boolean observing;
    private long savedPlayRevision,savedOverrideUntil,autoPlayRevision,autoOverrideUntil,deadline,holdSince;
    private int savedScene,savedOverrideIndex,autoScene,autoOverrideIndex,failed,cycles,lastScene,manualScene;
    private volatile int pinEnds;
    private boolean saved,finished,previewSurface,cycleOut,cycleThreshold,cycleHidden,cycleIn,cycleChanged;
    private boolean allOut=true,allThreshold=true,allHidden=true,allIn=true,allDifferent=true,allStartProgress=true;
    private int previewCamera;
    private String lastPath,pinPath;
    private Map<String,?> autoPrefs,manualPrefs;
    private Map<String,Object> autoGlobal,manualGlobal;
    private float[] clockMatrix;
    private boolean activeFadeBeforeHide,homeRequested;
    private static final class StartObservation {
        final String path;final int scene;final long time,loadAck;final float alpha;final CarpSequence.Phase phase;volatile long firstFadeIn;
        StartObservation(String path,int scene,long time,long loadAck,float alpha,CarpSequence.Phase phase){this.path=path;this.scene=scene;this.time=time;this.loadAck=loadAck;this.alpha=alpha;this.phase=phase;}
    }
    private final PAGView.PAGViewListener pinListener=new PAGView.PAGViewListener(){
        public void onAnimationStart(PAGView v){CarpSequence model=stage().carp;if(!observing||model==null)return;synchronized(sourceStarts){if(sourceStarts.size()<16)sourceStarts.add(new StartObservation(stage().loaded,model.scene(),now(),model.phaseStartedAt(),v.getAlpha(),model.phase()));}}
        public void onAnimationCancel(PAGView v){}public void onAnimationRepeat(PAGView v){}
        public void onAnimationUpdate(PAGView v){CarpSequence model=stage().carp;if(!observing||model==null||model.phase()!=CarpSequence.Phase.FADING_IN||v.getAlpha()<=0||v.getAlpha()>=1)return;String path=stage().loaded;long time=now();synchronized(sourceStarts){for(int i=sourceStarts.size()-1;i>=0;i--){StartObservation point=sourceStarts.get(i);if(point.path.equals(path)&&point.scene==model.scene()){if(point.firstFadeIn==0)point.firstFadeIn=time;break;}}}}
        public void onAnimationEnd(PAGView v){if(PIN.equals(Pets.current(activity).optString("id"))&&v.getProgress()>=.999)pinEnds++;}
    };
    private Donor18Qa(PetActivity activity){this.activity=activity;}
    public static void start(PetActivity activity){
        if(!(Build.HARDWARE.contains("ranchu")||Build.HARDWARE.contains("goldfish")))throw new IllegalStateException("Donor18Qa is emulator-only");
        if(Looper.myLooper()!=Looper.getMainLooper()){activity.runOnUiThread(()->start(activity));return;}
        if(running)return;running=true;new Donor18Qa(activity).begin();
    }
    private PetStage stage(){return activity.stage;}
    private long now(){return SystemClock.elapsedRealtime();}
    private void record(String name,boolean pass,String detail){try{results.put(new JSONObject().put("test",name).put("ok",pass).put("detail",detail));}catch(JSONException ignored){}if(!pass)failed++;}
    private void poll(Runnable step){handler.postDelayed(()->{
        if(finished)return;try{if(!homeRequested&&(activity.isDestroyed()||activity.isFinishing()))throw new IllegalStateException("Activity ended before intentional QA hide");step.run();}
        catch(Throwable e){record("unexpected_error",false,e.getClass().getSimpleName()+": "+e.getMessage());finish();}
    },50);}
    private int index(String id){JSONArray catalog=Pets.catalog(activity);for(int i=0;i<catalog.length();i++)if(id.equals(catalog.optJSONObject(i).optString("id")))return i;throw new IllegalStateException("Donor catalogue ID absent: "+id);}
    private Map<String,Object> global(){Map<String,Object> values=new HashMap<>();SharedPreferences prefs=activity.getSharedPreferences(Pets.PREFS,0);for(String key:GLOBAL_KEYS)if(prefs.contains(key))values.put(key,prefs.getAll().get(key));return values;}
    private void select(String id){Pets.select(activity,index(id));stage().reload();deadline=now()+5000;}
    private void begin(){try{
        initialSha=Qa.binarySha(activity);petMode=new QaPetMode(activity);
        for(String id:IDS){index(id);savedScenes.put(id,new HashMap<>(SceneSettings.prefs(activity,id).getAll()));}
        savedGlobal.putAll(global());savedScene=Pets.scene;savedPlayRevision=Pets.playRevision;savedOverrideIndex=Pets.state.overrideIndex;savedOverrideUntil=Pets.state.overrideUntil;saved=true;
        previewSurface=stage().previewSurface;previewCamera=stage().previewCameraRight;stage().pag.addListener(pinListener);
        SharedPreferences.Editor clean=SceneSettings.prefs(activity,CARP).edit().remove("scene");for(String key:LAYOUT_KEYS)clean.remove(key);clean.apply();Pets.state.overrideUntil=0;
        select(CARP);poll(this::carpReady);
    }catch(Throwable e){record("setup",false,e.getClass().getSimpleName()+": "+e.getMessage());finish();}}
    private boolean pagReady(){return stage().running&&stage().pag.getVisibility()==View.VISIBLE&&stage().pag.getComposition()!=null&&!stage().loaded.isEmpty();}
    private void carpReady(){
        if((!pagReady()||stage().carp==null||!stage().backdrop.clockLoaded)&&now()<deadline){poll(this::carpReady);return;}
        JSONObject pet=Pets.current(activity);boolean ready=pagReady()&&stage().carp!=null&&CARP.equals(pet.optString("id"));
        record("carp_native_sequence_loaded",ready&&pet.optString("playbackPolicy").equals("carp-sequence")&&!SceneSettings.prefs(activity,CARP).contains("scene")&&stage().carpScene>=0&&stage().carpScene<4,"Real PAG composition, local cold scene0..3, no saved scene");
        record("carp_repeat_count_one",stage().pag.repeatCount()==1,"Actual PAGView repeatCount="+stage().pag.repeatCount());
        record("carp_desk29_asset_dimensions",clockDigits(),"Loaded29 desk bitmaps compared to bundled source PNG dimensions");
        if(!ready)throw new IllegalStateException("Carp stage did not load");
        autoPrefs=new HashMap<>(SceneSettings.prefs(activity,CARP).getAll());autoGlobal=global();autoPlayRevision=Pets.playRevision;autoScene=Pets.scene;autoOverrideIndex=Pets.state.overrideIndex;autoOverrideUntil=Pets.state.overrideUntil;
        lastPath=stage().loaded;lastScene=stage().carp.scene();observing=true;deadline=now()+40000;poll(this::observeCycles);
    }
    private boolean clockDigits(){
        if(!stage().backdrop.clockEnabled()||!stage().backdrop.clockLoaded)return false;
        String[] slots={"hour_0","hour_1","minute_0","minute_1"};int[] expected={3,10,6,10};int total=0;boolean valid=true;
        for(int slot=0;slot<4;slot++){int count=0;for(int digit=0;digit<10;digit++){Bitmap bitmap=stage().backdrop.desk[slot][digit];if(bitmap==null)continue;count++;total++;
            BitmapFactory.Options options=new BitmapFactory.Options();options.inJustDecodeBounds=true;
            try(java.io.InputStream in=activity.getAssets().open("pets/"+CARP+"/desk/"+slots[slot]+"/temp_"+digit+".png")){BitmapFactory.decodeStream(in,null,options);valid&=options.outWidth>0&&options.outHeight>0&&bitmap.getWidth()==options.outWidth&&bitmap.getHeight()==options.outHeight;}catch(Exception e){valid=false;}
        }valid&=count==expected[slot];}return valid&&total==29;
    }
    private void observeCycles(){
        CarpSequence model=stage().carp;if(model==null)throw new IllegalStateException("Carp timeline disappeared");
        CarpSequence.Phase phase=model.phase();float alpha=stage().pag.getAlpha();double progress=stage().pag.getProgress();String path=stage().loaded;
        minimumPollAlpha=Math.min(minimumPollAlpha,alpha);String phaseKey=model.scene()+"/"+phase;if(!phaseKey.equals(diagnosticPhase)){diagnosticPhase=phaseKey;if(phaseDiagnostics.length()<32)try{phaseDiagnostics.put(new JSONObject().put("elapsedMs",now()-began).put("scene",model.scene()).put("phase",phase.toString()).put("alpha",alpha).put("progress",progress));}catch(JSONException ignored){}}
        if(phase==CarpSequence.Phase.FADING_OUT&&alpha>0&&alpha<1){cycleOut=true;if(cycleOutTime==0)cycleOutTime=now();cycleThreshold|=progress>model.threshold(model.scene());}
        if(!path.equals(lastPath)){
            allDifferent&=model.scene()!=lastScene;allStartProgress&=progress<.10;cycleChanged=true;cycleChangedTime=now();lastPath=path;lastScene=model.scene();
        }
        if(cycleChanged&&phase==CarpSequence.Phase.HIDDEN_DELAY&&alpha<=.001f){cycleHidden=true;if(cycleHiddenTime==0){cycleHiddenTime=model.phaseStartedAt();cycleNativeHiddenTime=now();}}
        if(cycleChanged&&phase==CarpSequence.Phase.FADING_IN&&alpha>0&&alpha<1){cycleIn=true;if(cycleInTime==0)cycleInTime=now();}
        if(cycleChanged)synchronized(sourceStarts){for(int i=sourceStarts.size()-1;i>=0;i--){StartObservation point=sourceStarts.get(i);if(point.path.equals(path)&&point.scene==model.scene()&&point.time>=cycleOutTime){if(point.phase==CarpSequence.Phase.HIDDEN_DELAY&&point.alpha<=.001f){cycleHidden=true;cycleHiddenTime=point.loadAck;cycleNativeHiddenTime=point.time;}if(point.firstFadeIn>0&&(cycleInTime==0||point.firstFadeIn<cycleInTime))cycleInTime=point.firstFadeIn;break;}}}
        if(cycleChanged&&phase==CarpSequence.Phase.PLAYING&&alpha>=.999f){cycles++;allOut&=cycleOut;allThreshold&=cycleThreshold;allHidden&=cycleHidden&&cycleHiddenTime>0&&cycleInTime-cycleHiddenTime>=100;allIn&=cycleIn;
            try{cycleDiagnostics.put(new JSONObject().put("cycle",cycles).put("scene",model.scene()).put("minimumPollAlpha",minimumPollAlpha).put("outMs",cycleOutTime-began).put("sourceChangeMs",cycleChangedTime-began).put("loadAckMs",cycleHiddenTime==0?-1:cycleHiddenTime-began).put("nativeHiddenObservationMs",cycleNativeHiddenTime==0?-1:cycleNativeHiddenTime-began).put("firstFadeInViewStateMs",cycleInTime==0?-1:cycleInTime-began).put("ackToFadeInMs",cycleHiddenTime==0||cycleInTime==0?-1:cycleInTime-cycleHiddenTime).put("completeMs",now()-began));}catch(JSONException ignored){}
            cycleOut=cycleThreshold=cycleHidden=cycleIn=cycleChanged=false;cycleOutTime=cycleHiddenTime=cycleNativeHiddenTime=cycleInTime=cycleChangedTime=0;minimumPollAlpha=1;}
        if(cycles<2&&now()<deadline){poll(this::observeCycles);return;}
        record("carp_two_actual_auto_transitions",cycles>=2&&allStartProgress,"Completed automatic transitions="+cycles+"; every new PAG observed near progress0");
        record("carp_fade_out_native_threshold",cycles>=2&&allOut&&allThreshold,"Real FADING_OUT samples alpha0..1 after each native threshold");
        observing=false;
        record("carp_hidden_delay_alpha_zero",cycles>=2&&allHidden,"Loaded PAGView observed HIDDEN_DELAY alpha0 via native start or50ms sample; first actual fade-in observation>=100ms after model load acknowledgement, not callback delivery. Load-ack/view-property evidence, not compositor-frame proof. "+cycleDiagnostics);
        record("carp_fade_in_alpha_path",cycles>=2&&allIn,"New source observed at intermediate FADING_IN alpha before returning to1");
        record("carp_next_scene_differs",cycles>=2&&allDifferent,"Every real source change selected another scene");
        record("carp_auto_scene_preferences_unchanged",autoPrefs.equals(SceneSettings.prefs(activity,CARP).getAll()),"All selected-pet preferences unchanged across automatic transitions");
        record("carp_auto_global_state_unchanged",autoGlobal.equals(global())&&autoPlayRevision==Pets.playRevision&&autoScene==Pets.scene&&autoOverrideIndex==Pets.state.overrideIndex&&autoOverrideUntil==Pets.state.overrideUntil,"Selection keys, playRevision and override unchanged");
        int previous=model.scene();stage().pag.performClick();manualScene=SceneSettings.prefs(activity,CARP).getInt("scene",-1);deadline=now()+3000;
        // Save the previous scene separately to validate the actual tap's choice.
        lastScene=previous;poll(this::manualReady);
    }
    private void manualReady(){
        boolean ready=stage().carp!=null&&stage().carp.scene()==manualScene&&manualScene!=lastScene&&stage().pag.getProgress()<.10&&stage().pag.isPlaying();
        if(!ready&&now()<deadline){poll(this::manualReady);return;}
        record("carp_manual_tap_restarts_saved_scene",ready&&manualScene>=0&&manualScene<4&&Pets.playRevision>autoPlayRevision&&stage().pag.getAlpha()>=.999f,"Actual PAGView tap, changed scene saved and playback restarted");
        clockMatrix=matrix();manualPrefs=new HashMap<>(SceneSettings.prefs(activity,CARP).getAll());manualGlobal=global();
        stage().previewSurface=true;stage().previewCameraRight=stage().backdrop.cameraRight;stage().previewLayout(new PetLayoutProfile(true,1,0,0));deadline=now()+1500;poll(this::draftReady);
    }
    private float[] matrix(){float[] values=new float[9];stage().pag.matrix().getValues(values);return values;}
    private void draftReady(){
        if(stage().backdrop.clockLoaded&&now()<deadline){poll(this::draftReady);return;}
        record("carp_clockless_draft_resources_local",!stage().backdrop.clockEnabled()&&!stage().backdrop.clockLoaded&&stage().backdrop.font==null&&manualPrefs.equals(SceneSettings.prefs(activity,CARP).getAll())&&manualGlobal.equals(global()),"Only this stage emulates Main preview; clock assets released with no saved changes");
        record("carp_clockless_real_matrix_larger",matrix()[0]>clockMatrix[0]+.001f,"Actual PAGView scale exceeds with-clock scale");
        stage().previewLayout(null);stage().previewSurface=previewSurface;stage().previewCameraRight=previewCamera;stage().requestLayout();deadline=now()+1500;poll(this::cancelReady);
    }
    private void cancelReady(){
        if(!stage().backdrop.clockLoaded&&now()<deadline){poll(this::cancelReady);return;}float[] values=matrix();boolean equal=true;for(int i:new int[]{0,2,5})equal&=Math.abs(values[i]-clockMatrix[i])<.02f;
        record("carp_draft_cancel_restores_clock_matrix",equal&&stage().backdrop.clockEnabled()&&stage().backdrop.clockLoaded&&manualPrefs.equals(SceneSettings.prefs(activity,CARP).getAll())&&manualGlobal.equals(global()),"Same source clock/geometry restored; saved preferences unchanged");
        select(VORTEX);poll(this::vortexReady);
    }
    private void vortexReady(){
        boolean ready=stage().video.getVisibility()==View.VISIBLE&&stage().video.player!=null&&stage().video.prepared&&stage().video.player.isPlaying();
        if(!ready&&now()<deadline){poll(this::vortexReady);return;}
        record("vortex_real_media_player_playing",ready&&stage().video.videoW>0&&stage().video.videoH>0&&stage().loaded.endsWith(".mp4")&&stage().pag.getComposition()==null,"Real MediaPlayer preparation/playback; previous invisible PAG composition released");
        View video=stage().video;boolean bounds=video.getLeft()==0&&video.getTop()==0&&video.getWidth()==stage().getWidth()&&video.getHeight()==stage().getHeight();record("vortex_background_cover_bounds",ready&&bounds,"Video TextureView covers actual stage bounds");
        record("vortex_no_clock_or_pet_tap_controls",!stage().backdrop.clockEnabled()&&!stage().backdrop.clockLoaded&&!stage().video.hasOnClickListeners()&&!stage().video.isClickable()&&!PetLayout.supported(Pets.current(activity)),"No visible video tap handler/app clock; pet-layout controls ineligible for background role");
        select(PIN);pinEnds=0;poll(this::pinReady);
    }
    private void pinReady(){
        if(!pagReady()&&now()<deadline){poll(this::pinReady);return;}boolean ready=pagReady()&&PIN.equals(Pets.current(activity).optString("id"));
        record("pin_finite_preview_loaded",ready&&stage().pag.repeatCount()==1&&stage().carp==null&&stage().video.player==null,"Actual finite PAG preview, no video/carp decoder");
        if(!ready)throw new IllegalStateException("PIN composition not loaded");pinPath=stage().loaded;deadline=now()+stage().pag.getComposition().duration()/1000+5000;holdSince=0;poll(this::pinHold);
    }
    private void pinHold(){
        boolean complete=pinEnds>0&&stage().pag.getProgress()>=.999&& !stage().pag.isPlaying();if(complete){if(holdSince==0)holdSince=now();}else holdSince=0;
        if((holdSince==0||now()-holdSince<600)&&now()<deadline){poll(this::pinHold);return;}
        record("pin_completes_then_holds",complete&&holdSince>0&&now()-holdSince>=600,"Actual onAnimationEnd and completed progress held at least600ms");
        stage().pag.performClick();deadline=now()+3000;poll(this::pinReplay);
    }
    private void pinReplay(){
        boolean replay=pinPath.equals(stage().loaded)&&stage().pag.isPlaying()&&stage().pag.getProgress()<.15;
        if(!replay&&now()<deadline){poll(this::pinReplay);return;}record("pin_tap_replays_existing_player",replay,"Actual PAGView tap restarts the same finite source");
        select(CARP);deadline=now()+24000;poll(this::fadeBeforeHide);
    }
    private void fadeBeforeHide(){
        boolean fade=stage().carp!=null&&stage().carp.phase()==CarpSequence.Phase.FADING_OUT&&stage().pag.getAlpha()>0&&stage().pag.getAlpha()<1;
        if(!fade&&now()<deadline){poll(this::fadeBeforeHide);return;}activeFadeBeforeHide=fade;try{Pets.write(activity,"donor18-hide-request.json",new JSONObject().put("apkSha256",initialSha).put("runToken",Long.toString(began)).put("observedFade",fade).put("alpha",stage().pag.getAlpha()).put("elapsedMs",now()-began).toString());homeRequested=true;}catch(Exception e){homeRequested=false;}deadline=now()+12000;poll(this::hidden);
    }
    private boolean homeAcknowledged(){try(BufferedReader input=new BufferedReader(new FileReader(new File(activity.getExternalFilesDir(null),"donor18-home-ack.txt")))){return Long.toString(began).equals(input.readLine());}catch(IOException e){return false;}}
    private void hidden(){
        boolean ack=homeAcknowledged();if((stage().running||!ack)&&now()<deadline){poll(this::hidden);return;}
        String detail="activeFade="+activeFadeBeforeHide+" homeRequested="+homeRequested+" hostHomeAck="+ack+" running="+stage().running+" carp="+(stage().carp==null?"null":stage().carp.phase())+" sampleCallback="+stage().handler.hasCallbacks(stage().carpSample)+" switchCallback="+stage().handler.hasCallbacks(stage().carpSwitch)+" pagComposition="+(stage().pag.getComposition()!=null)+" videoPlayer="+(stage().video.player!=null)+" alpha="+stage().pag.getAlpha();
        record("actual_activity_hide_stops_active_carp",activeFadeBeforeHide&&homeRequested&&ack&&!stage().running,"Actual host KEYCODE_HOME after native fade handshake; "+detail);
        record("hidden_releases_players_and_callbacks",!stage().running&&stage().carp==null&&!stage().handler.hasCallbacks(stage().carpSample)&&!stage().handler.hasCallbacks(stage().carpSwitch)&&stage().pag.getComposition()==null&&stage().video.player==null&&stage().pag.getAlpha()==1,detail);finish();
    }
    private static void put(SharedPreferences.Editor edit,String key,Object value){if(value instanceof Boolean)edit.putBoolean(key,(Boolean)value);else if(value instanceof Float)edit.putFloat(key,(Float)value);else if(value instanceof Integer)edit.putInt(key,(Integer)value);else if(value instanceof Long)edit.putLong(key,(Long)value);else if(value instanceof String)edit.putString(key,(String)value);else if(value instanceof Set)edit.putStringSet(key,new HashSet<>((Set<String>)value));}
    private void restore(){
        boolean exact=true;if(saved){for(String id:IDS){SharedPreferences prefs=SceneSettings.prefs(activity,id);SharedPreferences.Editor edit=prefs.edit().clear();Map<String,?> values=savedScenes.get(id);for(Map.Entry<String,?> entry:values.entrySet())put(edit,entry.getKey(),entry.getValue());edit.apply();exact&=values.equals(prefs.getAll());}
            SharedPreferences.Editor edit=activity.getSharedPreferences(Pets.PREFS,0).edit();for(String key:GLOBAL_KEYS){edit.remove(key);if(savedGlobal.containsKey(key))put(edit,key,savedGlobal.get(key));}edit.apply();Pets.scene=savedScene;Pets.playRevision=savedPlayRevision;Pets.state.overrideIndex=savedOverrideIndex;Pets.state.overrideUntil=savedOverrideUntil;exact&=savedGlobal.equals(global())&&Pets.scene==savedScene&&Pets.playRevision==savedPlayRevision&&Pets.state.overrideIndex==savedOverrideIndex&&Pets.state.overrideUntil==savedOverrideUntil;
        }if(petMode!=null)exact&=petMode.restore();record("donor_preferences_and_selection_restored",saved&&exact,"Original donor preferences/key presence, selection, playback revision and override restored");
    }
    private void finish(){if(finished)return;finished=true;observing=false;handler.removeCallbacksAndMessages(null);try{stage().pag.removeListener(pinListener);stage().previewLayout(null);stage().previewSurface=previewSurface;stage().previewCameraRight=previewCamera;restore();}catch(Throwable e){record("restore_error",false,e.getClass().getSimpleName()+": "+e.getMessage());}
        new Thread(()->{try{Pets.write(activity,"donor18-qa.json",new JSONObject().put("apkSha256",Qa.binarySha(activity)).put("environment","Standard Android emulator; real app players/view properties, not compositor-frame or HyperOS/physical camera proof").put("tested",results.length()).put("failed",failed).put("durationMs",now()-began).put("cycles",cycleDiagnostics).put("phaseObservations",phaseDiagnostics).put("results",results).put("skipped",new JSONArray()).toString(2));}catch(Exception ignored){}finally{running=false;}},"donor18-qa-report").start();
    }
}
