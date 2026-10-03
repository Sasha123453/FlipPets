package org.flippets.app;

import android.content.*;
import android.media.MediaMetadata;
import android.media.session.MediaController;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;

/** Emulator-only asynchronous UI/API checks. No audio, network, or other-app metadata. */
public final class UtilityQa {
    private static boolean running;
    private static final String TRACK="Flip Pets test track";
    private static final String[] SAVED_KEYS={"utilityCard","utilityTimerMode","utilityTimerRunning","utilityTimerElapsed","utilityTimerStart","utilityTimerBoot","pet","petId"};
    private final PetActivity activity;
    private final SharedPreferences prefs;
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final Map<String,Object> saved=new HashMap<>();
    private final JSONArray results=new JSONArray(),skipped=new JSONArray();
    private final long began=SystemClock.elapsedRealtime();
    private MediaSession session;
    private int failed,pauses,plays,nexts;
    private boolean finished;
    private long timerElapsed,pausedElapsed,mediaDeadline;
    private String timerText,pausedText;
    private UtilityQa(PetActivity a){activity=a;prefs=a.getSharedPreferences(Pets.PREFS,0);Map<String,?> all=prefs.getAll();for(String key:SAVED_KEYS)if(all.containsKey(key))saved.put(key,all.get(key));}
    public static void start(PetActivity a){
        if(!(Build.HARDWARE.contains("ranchu")||Build.HARDWARE.contains("goldfish")))throw new IllegalStateException("UtilityQa is emulator-only");
        if(Looper.myLooper()!=Looper.getMainLooper()){a.runOnUiThread(()->start(a));return;}
        if(running)return;running=true;UtilityQa qa=new UtilityQa(a);qa.later(qa::battery,200);
    }
    private void later(Runnable step,long delay){handler.postDelayed(()->{
        if(finished)return;
        try{if(activity.isDestroyed()||activity.isFinishing()||activity.stage==null||!activity.stage.running)throw new IllegalStateException("Activity/stage stopped before QA completed");step.run();}
        catch(Throwable e){record("unexpected_error",false,e.getClass().getSimpleName()+": "+e.getMessage());finish();}
    },delay);}
    private void record(String name,boolean ok,String detail){try{results.put(new JSONObject().put("test",name).put("ok",ok).put("detail",detail));}catch(JSONException ignored){}if(!ok)failed++;}
    private UtilityCardView card(){return activity.stage.utility;}
    private void choose(String mode){prefs.edit().putString("utilityCard",mode).apply();Pets.signal(activity);}
    private void battery(){choose("battery");later(()->{
        String percent=textValue();boolean valid=percent.matches("[0-9]{1,3}%");if(valid){int n=Integer.parseInt(percent.substring(0,percent.length()-1));valid=n>=0&&n<=100;}
        record("battery_percent",valid,valid?percent:"No valid percentage in battery card");
        UtilityCardView c=card();PetStage s=activity.stage;float safe=s.full?Math.max(s.backdrop.cameraRight,s.getWidth()*.34f):0;
        boolean bounds=c.isShown()&&c.getWidth()>0&&c.getHeight()>0&&c.getLeft()>=Math.floor(safe)&&c.getTop()>=0&&c.getRight()<=s.getWidth()&&c.getBottom()<=s.getHeight();
        record("card_bounds_camera_safe",bounds,"card="+c.getLeft()+","+c.getTop()+","+c.getRight()+","+c.getBottom()+" stage="+s.getWidth()+"x"+s.getHeight()+" safeLeft="+Math.round(safe));
        TimerState timer=UtilityTimerStore.read(activity);timer.select("stopwatch",SystemClock.elapsedRealtime());UtilityTimerStore.save(activity,timer);choose("timer");later(this::timerStart,250);
    },350);}
    private void timerStart(){
        Button start=button("toggle");boolean click=start!=null&&start.isEnabled()&&start.performClick();TimerState timer=UtilityTimerStore.read(activity);
        timerElapsed=timer.elapsed(SystemClock.elapsedRealtime());timerText=textValue();record("timer_start_button",click&&timer.running,"running="+timer.running);
        later(this::timerPause,1300);
    }
    private void timerPause(){
        TimerState timer=UtilityTimerStore.read(activity);long elapsed=timer.elapsed(SystemClock.elapsedRealtime());String value=textValue();
        record("timer_advances_visible",elapsed-timerElapsed>=1000&&!value.equals(timerText),"elapsedDeltaMs="+(elapsed-timerElapsed)+" displayChanged="+!value.equals(timerText));
        Button pause=button("toggle");boolean click=pause!=null&&pause.isEnabled()&&pause.performClick();TimerState paused=UtilityTimerStore.read(activity);pausedElapsed=paused.elapsed(SystemClock.elapsedRealtime());pausedText=textValue();
        record("timer_pause_button",click&&!paused.running,"running="+paused.running);later(this::timerReset,1300);
    }
    private void timerReset(){
        TimerState paused=UtilityTimerStore.read(activity);record("timer_pause_stable",paused.elapsed(SystemClock.elapsedRealtime())==pausedElapsed&&textValue().equals(pausedText),"elapsed unchanged="+(paused.elapsed(SystemClock.elapsedRealtime())==pausedElapsed));
        Button reset=button("reset");boolean click=reset!=null&&reset.performClick();TimerState clear=UtilityTimerStore.read(activity);record("timer_reset_button",click&&!clear.running&&clear.elapsed(SystemClock.elapsedRealtime())==0,"elapsed="+clear.elapsed(SystemClock.elapsedRealtime()));
        TimerState focus=UtilityTimerStore.read(activity);focus.select("focus",SystemClock.elapsedRealtime());UtilityTimerStore.save(activity,focus);later(()->{TimerState focused=UtilityTimerStore.read(activity);String expected=String.format(Locale.getDefault(),"%02d:%02d",25,0);record("focus_25_display","focus".equals(focused.mode)&&!focused.running&&focused.displayed(SystemClock.elapsedRealtime())==TimerState.FOCUS_MS&&expected.equals(textValue()),"Settings-like mode change; only rendered display checked");mediaCreate();},250);
    }
    private void mediaCreate(){
        choose("media");session=new MediaSession(activity,"FlipPetsUtilityQa");session.setFlags(MediaSession.FLAG_HANDLES_MEDIA_BUTTONS|MediaSession.FLAG_HANDLES_TRANSPORT_CONTROLS);
        session.setCallback(new MediaSession.Callback(){
            @Override public void onPause(){pauses++;playback(PlaybackState.STATE_PAUSED,true);}
            @Override public void onPlay(){plays++;playback(PlaybackState.STATE_PLAYING,true);}
            @Override public void onSkipToNext(){nexts++;}
        },handler);
        session.setMetadata(new MediaMetadata.Builder().putString(MediaMetadata.METADATA_KEY_TITLE,TRACK).putString(MediaMetadata.METADATA_KEY_ARTIST,"Flip Pets QA").putLong(MediaMetadata.METADATA_KEY_DURATION,60000).build());
        playback(PlaybackState.STATE_PLAYING,true);session.setActive(true);mediaDeadline=SystemClock.elapsedRealtime()+4000;later(this::mediaDiscover,800);
    }
    private void playback(int state,boolean next){long actions=PlaybackState.ACTION_PLAY_PAUSE|PlaybackState.ACTION_PLAY|PlaybackState.ACTION_PAUSE;if(next)actions|=PlaybackState.ACTION_SKIP_TO_NEXT;session.setPlaybackState(new PlaybackState.Builder().setState(state,0,state==PlaybackState.STATE_PLAYING?1:0,SystemClock.elapsedRealtime()).setActions(actions).build());}
    private boolean ownMedia(){MediaController c=PetNotifications.currentMedia();return session!=null&&c!=null&&session.getSessionToken().equals(c.getSessionToken());}
    private void mediaDiscover(){
        if(!ownMedia()&&SystemClock.elapsedRealtime()<mediaDeadline){later(this::mediaDiscover,400);return;}
        record("media_discovery_notification_listener",ownMedia(),ownMedia()?"Synthetic session discovered through real listener":"Synthetic session not discovered. Check notification-listener access/connection; no metadata was injected into the card.");
        if(!ownMedia()){skipped.put("media_card_metadata").put("media_pause_callback").put("media_next_callback").put("media_play_button").put("media_unsupported_next");finish();return;}
        later(()->{
            record("media_card_metadata",TRACK.equals(textValue()),"Only synthetic title compared");
            boolean sent=PetNotifications.control("toggle");later(()->{
                record("media_pause_callback",sent&&pauses==1&&ownMedia()&&!PetNotifications.isPlaying(PetNotifications.currentMedia().getPlaybackState()),"syntheticPauseCallbacks="+pauses);
                boolean nextSent=ownMedia()&&PetNotifications.control("next");later(()->{
                    record("media_next_callback",nextSent&&nexts==1,"syntheticNextCallbacks="+nexts);Button play=button("toggle");boolean clicked=ownMedia()&&play!=null&&play.isEnabled()&&play.performClick();later(()->{
                        record("media_play_button",clicked&&plays==1&&ownMedia()&&PetNotifications.isPlaying(PetNotifications.currentMedia().getPlaybackState()),"syntheticPlayCallbacks="+plays);
                        playback(PlaybackState.STATE_PLAYING,false);later(()->{Button disabled=button("next");boolean refused=ownMedia()&&!PetNotifications.control("next");record("media_unsupported_next",refused&&disabled!=null&&!disabled.isEnabled()&&nexts==1,"unsupported next disabled; callbacks="+nexts);finish();},400);
                    },400);
                },400);
            },400);
        },250);
    }
    private String textValue(){return card().qaDisplayValue();}
    private Button button(String action){return card().qaButton(action);}
    private void restore(){
        card().resetForQaRestore();SharedPreferences.Editor edit=prefs.edit();for(String key:SAVED_KEYS){edit.remove(key);if(!saved.containsKey(key))continue;Object value=saved.get(key);if(value instanceof String)edit.putString(key,(String)value);else if(value instanceof Boolean)edit.putBoolean(key,(Boolean)value);else if(value instanceof Integer)edit.putInt(key,(Integer)value);else if(value instanceof Long)edit.putLong(key,(Long)value);else if(value instanceof Float)edit.putFloat(key,(Float)value);}
        edit.apply();
        Map<String,?> after=prefs.getAll();boolean exact=true;for(String key:SAVED_KEYS)if(saved.containsKey(key)?!Objects.equals(saved.get(key),after.get(key)):after.containsKey(key))exact=false;
        record("preferences_restored",exact,"Utility/timer and scene selection keys restored");Pets.signal(activity);if(activity.stage.running)card().start();
    }
    private void finish(){
        if(finished)return;finished=true;handler.removeCallbacksAndMessages(null);
        if(session!=null){try{session.setActive(false);session.release();}catch(RuntimeException ignored){}session=null;}
        try{restore();}catch(Throwable e){record("restore_error",false,e.getClass().getSimpleName()+": "+e.getMessage());}
        final int failedCount=failed;final long duration=SystemClock.elapsedRealtime()-began;
        new Thread(()->{try{Pets.write(activity,"utility-qa.json",new JSONObject().put("apkSha256",Qa.binarySha(activity)).put("environment","Android emulator; no HyperOS/hardware claim").put("tested",results.length()).put("failed",failedCount).put("durationMs",duration).put("results",results).put("skipped",skipped).toString(2));}catch(Exception e){try{Pets.write(activity,"utility-qa-error.txt",e.toString());}catch(Exception ignored){}}finally{handler.post(()->running=false);}},"utility-qa-report").start();
    }
}