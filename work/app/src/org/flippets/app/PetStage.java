package org.flippets.app;

import android.Manifest;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.hardware.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.libpag.*;
import org.json.*;
import java.text.SimpleDateFormat;
import java.util.*;

/** Shared renderer for preview and an independently launched display activity. */
public final class PetStage extends FrameLayout implements SensorEventListener {
    public final PAGView pag;
    final PetSceneFrame pagFrame;
    final PetVideo video;
    final CompositionView composition;
    final PhotoLayer photo,front;
    boolean gravityRegistered;
    final TextView clock;
    final PetBackdrop backdrop;
    final UtilityCardView utility;
    final MiniAppView mini;
    boolean miniVisible;
    final boolean full;
    final View.OnClickListener mediaClicked;
    boolean previewSurface;int previewCameraRight;
    private PetLayoutProfile layoutDraft;
    final Handler handler=new Handler(Looper.getMainLooper());
    final SensorManager sensors;
    boolean running;
    String loaded="";long visualStamp=-1,lastBackdropMinute=-1;
    int tap;
    long lastPlayRevision=-1;
    String lastGeometry="";
    String mediaGeometry="";
    CarpSequence carp;String carpId="",carpFailedPath="";long carpPlayRevision=-1;int carpScene,carpPending=-1;boolean carpSwitchPosted;
    final Random carpRandom=new Random();
    final Runnable carpSample=()->carpFrame();
    final Runnable carpSwitch=()->{carpSwitchPosted=false;if(!running||carp==null||!carp.needsNextScene())return;carpPending=carp.nextScene(carpRandom.nextInt(3));carpScene=carpPending;update();};
    final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context c,Intent i){Pets.battery(c);utility.batteryChanged(i);update();if(!miniVisible&&!handler.hasCallbacks(ticker))handler.post(ticker);}};
    final Runnable ticker=new Runnable(){public void run(){if(!running)return;update();if(!miniVisible)handler.postDelayed(this,composition.getVisibility()==VISIBLE?composition.nextDelay():250);}};
    public PetStage(Context c,boolean showClock){
        super(c);full=showClock;sensors=(SensorManager)c.getSystemService(Context.SENSOR_SERVICE);
        photo=new PhotoLayer(c,false);addView(photo,new LayoutParams(-1,-1));photo.setVisibility(GONE);
        backdrop=new PetBackdrop(c,showClock);addView(backdrop,new LayoutParams(-1,-1));
        pag=new PAGView(c);pag.setRepeatCount(0);pag.setScaleMode(PAGScaleMode.LetterBox);pag.setMaxFrameRate(FlipPetsApp.frameRate(c));
        pag.addListener(new PAGView.PAGViewListener(){public void onAnimationStart(PAGView v){}public void onAnimationEnd(PAGView v){AppLog.event(c,"PLAYBACK_END",loaded+" progress="+v.getProgress());}public void onAnimationCancel(PAGView v){}public void onAnimationRepeat(PAGView v){}public void onAnimationUpdate(PAGView v){if(!running||carp==null)return;if(Looper.myLooper()==Looper.getMainLooper())carpFrame();else if(!handler.hasCallbacks(carpSample))handler.post(carpSample);}});
        pagFrame=new PetSceneFrame(c,pag);addView(pagFrame,new LayoutParams(-1,-1));
        video=new PetVideo(c);addView(video,new LayoutParams(-1,-1));video.setVisibility(GONE);
        front=new PhotoLayer(c,true);addView(front,new LayoutParams(-1,-1));front.setVisibility(GONE);
        composition=new CompositionView(c);addView(composition,new LayoutParams(-1,-1));composition.setVisibility(GONE);
        clock=new TextView(c);clock.setTextColor(Color.WHITE);clock.setTextSize(34);clock.setGravity(Gravity.CENTER);clock.setShadowLayer(4,0,1,0x33000000);
        LayoutParams cp=new LayoutParams(-1,-2,Gravity.TOP|Gravity.CENTER_HORIZONTAL);cp.topMargin=24;addView(clock,cp);clock.setVisibility(GONE);
        utility=new UtilityCardView(c,true);addView(utility,new LayoutParams(-2,-2,Gravity.RIGHT|Gravity.BOTTOM));
        mini=new MiniAppView(c,true,id->MiniAppStore.select(c,id));addView(mini,new LayoutParams(-1,-1));mini.setVisibility(GONE);
        setOnApplyWindowInsetsListener((v,insets)->{android.view.DisplayCutout cutout=previewSurface?null:insets.getDisplayCutout();backdrop.cameraRight=previewSurface?previewCameraRight:0;if(cutout!=null)for(android.graphics.Rect rect:cutout.getBoundingRects())if(rect.left==0)backdrop.cameraRight=Math.max(backdrop.cameraRight,rect.right);composition.renderer.cameraRight=backdrop.cameraRight;mini.camera(backdrop.cameraRight);utility.windowBounds(getWidth(),full?Math.max(backdrop.cameraRight,getWidth()*.34f):0);requestLayout();return insets;});
        mediaClicked=v->{JSONObject pet=Pets.current(c);if(carpPolicy(pet)){int current=carp==null?Pets.stageIndex(c):carp.scene();Pets.choose(c,(Math.max(0,Math.min(3,current))+1+carpRandom.nextInt(3))%4);}else if(pet.optString("kind").equals("reactive")){if(Pets.stageIndex(c)>=8&&pag.isPlaying())return;Pets.override(c,12+(tap++%3),4500);}else{JSONObject clips=pet.optJSONObject("clips");int count=clips==null?0:clips.length();if(PlaybackPolicy.classic(pet.optString("id"))){if(pag.isPlaying())return;count=pet.optInt("touchSceneCount",count);int current=Pets.stageIndex(c),next=current;if(!pet.optString("id").startsWith("bird-")&&count>1)next=(current+1+new Random().nextInt(count-1))%count;Pets.choose(c,next);}else if(count>0)Pets.choose(c,(Pets.scene+1)%count);}};
        pag.setOnClickListener(mediaClicked);video.setOnClickListener(mediaClicked);
        setContentDescription("Анимированный питомец. Коснись для реакции.");
    }
    public void start(){
        if(running)return;running=true;AppLog.event(getContext(),"STAGE_START","display="+(getDisplay()==null?-1:getDisplay().getDisplayId())+" full="+full);
        IntentFilter f=new IntentFilter(Pets.EVENT);f.addAction(Intent.ACTION_BATTERY_CHANGED);
        if(Build.VERSION.SDK_INT>=33)getContext().registerReceiver(receiver,f,Context.RECEIVER_NOT_EXPORTED);else getContext().registerReceiver(receiver,f);
        if(!MiniAppStore.valid(MiniAppStore.selected(getContext()))&&getContext().checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION)==PackageManager.PERMISSION_GRANTED){Sensor step=sensors.getDefaultSensor(Sensor.TYPE_STEP_DETECTOR);if(step!=null)sensors.registerListener(this,step,SensorManager.SENSOR_DELAY_NORMAL);}
        Pets.battery(getContext());requestApplyInsets();requestLayout();handler.post(ticker);
    }
    public void stop(){if(!running)return;running=false;mini.stop();miniVisible=false;mini.setVisibility(GONE);pagFrame.setVisibility(VISIBLE);clearCarp();utility.stop();AppLog.event(getContext(),"STAGE_STOP","full="+full);handler.removeCallbacks(ticker);getContext().unregisterReceiver(receiver);sensors.unregisterListener(this);gravityRegistered=false;pag.pause();pag.setComposition(null);pag.freeCache();video.pause();video.load("");loaded="";composition.renderer.release();backdrop.release();photo.release();front.release();}
    public void destroy(){stop();pag.setComposition(null);pag.freeCache();video.destroy();composition.renderer.release();backdrop.release();photo.release();front.release();}
    public void reload(){loaded="";visualStamp=-1;mediaGeometry="";requestLayout();if(running)update();}
    /** Main-only staged geometry: neither preferences nor another stage is changed. */
    void previewLayout(PetLayoutProfile draft){layoutDraft=draft;backdrop.layoutDraft=draft;mediaGeometry="";lastBackdropMinute=-1;backdrop.invalidate();if(full)configureMediaGeometry(getWidth(),getHeight());}
    private PetLayoutProfile layoutProfile(JSONObject pet){return previewSurface&&layoutDraft!=null?layoutDraft:PetLayout.read(getContext(),pet);}
    private void update(){
        String app=MiniAppStore.selected(getContext());if(MiniAppStore.valid(app)){
            mini.preview(previewSurface&&mini.qaOrigin.isEmpty());
            if(!miniVisible){miniVisible=true;clearCarp();utility.stop();sensors.unregisterListener(this);gravityRegistered=false;pag.pause();pag.setComposition(null);pag.freeCache();video.pause();video.load("");loaded="";composition.renderer.release();backdrop.release();photo.release();front.release();for(View v:new View[]{photo,front,backdrop,pagFrame,video,composition,clock,utility})v.setVisibility(GONE);mini.setVisibility(VISIBLE);mini.show(app);mini.start();}
            handler.removeCallbacks(ticker);mini.camera(previewSurface?previewCameraRight:backdrop.cameraRight);mini.show(app);return;
        }
        if(miniVisible){miniVisible=false;mini.stop();mini.setVisibility(GONE);pagFrame.setVisibility(VISIBLE);lastBackdropMinute=-1;mediaGeometry="";if(getContext().checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION)==PackageManager.PERMISSION_GRANTED){Sensor step=sensors.getDefaultSensor(Sensor.TYPE_STEP_DETECTOR);if(step!=null)sensors.registerListener(this,step,SensorManager.SENSOR_DELAY_NORMAL);}video.start();}
        utility.start();
        Context c=getContext();pag.setMaxFrameRate(FlipPetsApp.frameRate(c));JSONObject selected=Pets.current(c);boolean composed=selected.optString("kind").equals("composition");boolean glitter=selected.optString("name").equals("Flowing glitter");
        boolean background=selected.optString("renderRole").equals("background");video.setOnClickListener(background?null:mediaClicked);video.setClickable(!background);
        if(running&&glitter!=gravityRegistered){Sensor gravity=sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);if(gravity!=null){if(glitter)sensors.registerListener(this,gravity,SensorManager.SENSOR_DELAY_UI);else sensors.unregisterListener(this,gravity);}gravityRegistered=glitter;}
        if(composed){clearCarp();if(composition.getVisibility()!=VISIBLE){pag.pause();pag.setComposition(null);video.pause();video.load("");loaded="";}composition.setVisibility(VISIBLE);backdrop.setVisibility(GONE);pag.setVisibility(GONE);video.setVisibility(GONE);photo.setVisibility(GONE);front.setVisibility(GONE);long stamp=System.currentTimeMillis()/60000^c.getSharedPreferences(Pets.PREFS,0).getLong("changeRevision",0);if(composition.nextDelay()<1000||stamp!=visualStamp){composition.invalidate();visualStamp=stamp;}return;}
        composition.setVisibility(GONE);backdrop.setVisibility(VISIBLE);photo.setVisibility(glitter?VISIBLE:GONE);front.setVisibility(glitter?VISIBLE:GONE);if(glitter){photo.invalidate();front.invalidate();}
        int index=Pets.stageIndex(c);boolean sequence=carpPolicy(selected);
        if(sequence){String id=selected.optString("id");if(carp==null||!id.equals(carpId)){clearCarp();carp=createCarp(selected);carpId=id;carpPlayRevision=Pets.playRevision;carpScene=SceneSettings.prefs(c,id).contains("scene")?Math.max(0,Math.min(3,index)):carpRandom.nextInt(4);carp.start(carpScene,SystemClock.elapsedRealtime());}else if(carpPlayRevision!=Pets.playRevision){cancelCarpCallbacks();carpPlayRevision=Pets.playRevision;carpScene=Math.max(0,Math.min(3,index));carpPending=-1;carpFailedPath="";carp.start(carpScene,SystemClock.elapsedRealtime());pag.setAlpha(1);}index=carpScene;}else if(carp!=null)clearCarp();
        String path=Pets.path(c,index);
        if(path.isEmpty())path=Pets.path(c,0);
        if(!path.equals(loaded)&&(!sequence||!path.equals(carpFailedPath))){AppLog.event(c,"LOAD",path);
            if(path.endsWith(".mp4")){pag.pause();pag.setComposition(null);pag.freeCache();pag.setVisibility(GONE);video.setVisibility(VISIBLE);video.load(path);if(running)video.start();loaded=path;}
            else{video.pause();video.load("");video.setVisibility(GONE);pag.setVisibility(VISIBLE);PAGFile file=PAGFile.Load(c.getAssets(),path);if(file!=null){pag.setRepeatCount(repeats(selected,index)?0:1);pag.setComposition(file);pag.setProgress(0);loaded=path;lastPlayRevision=Pets.playRevision;if(sequence){carpFailedPath="";if(carpPending<0)carp.start(index,SystemClock.elapsedRealtime());pag.setAlpha(carp.alpha(SystemClock.elapsedRealtime()));}pag.play();AppLog.event(c,"PLAYBACK",path+" repeat="+repeats(selected,index)+" durationUs="+file.duration());}else{AppLog.event(c,"PAG_LOAD_ERROR",path);if(sequence){carpFailedPath=path;carpScene=carp.scene();carpPending=-1;carp.stop();cancelCarpCallbacks();pag.pause();pag.setAlpha(1);lastPlayRevision=Pets.playRevision;}}}
            lastBackdropMinute=-1;JSONObject pet=Pets.current(c);int from=parseColor(pet.optString("gradientFrom","#444E70")),to=parseColor(pet.optString("gradientTo","#647D98"));
            setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{from,to}));
            mediaGeometry="";requestLayout();
        }
        if(pag.getVisibility()==VISIBLE&&pag.getComposition()!=null){pag.setRepeatCount(repeats(selected,index)?0:1);if(lastPlayRevision!=Pets.playRevision){lastPlayRevision=Pets.playRevision;pag.setProgress(0);pag.play();}}
        long minute=System.currentTimeMillis()/60000;if(glitter||(backdrop.clockEnabled()&&minute!=lastBackdropMinute)){backdrop.invalidate();lastBackdropMinute=minute;}
        if(full)configureMediaGeometry(getWidth(),getHeight());
        if(sequence){if(carpPending>=0&&carp.needsNextScene()&&path.equals(loaded)&&pag.getComposition()!=null){carp.loaded(carpPending,SystemClock.elapsedRealtime());carpPending=-1;pag.setAlpha(0);}carpFrame();}
    }
    private static boolean carpPolicy(JSONObject pet){return pet.optString("playbackPolicy").equals("carp-sequence");}
    private CarpSequence createCarp(JSONObject pet){double[] thresholds=CarpSequence.defaultThresholds();JSONObject values=pet.optJSONObject("transitionThresholds");if(values!=null)for(int i=0;i<4;i++)thresholds[i]=values.optDouble(Integer.toString(i),thresholds[i]);try{return new CarpSequence(thresholds,pet.optLong("fadeOutMs",500),pet.optLong("fadeDelayMs",100),pet.optLong("fadeInMs",300));}catch(IllegalArgumentException e){AppLog.event(getContext(),"CARP_CONFIG_FALLBACK",e.getMessage());return new CarpSequence();}}
    private void cancelCarpCallbacks(){handler.removeCallbacks(carpSample);handler.removeCallbacks(carpSwitch);carpSwitchPosted=false;}
    private void clearCarp(){if(carp==null&&carpId.isEmpty())return;cancelCarpCallbacks();if(carp!=null)carp.stop();carp=null;carpId="";carpFailedPath="";carpPending=-1;carpPlayRevision=-1;pag.setAlpha(1);}
    private void carpFrame(){if(!running||carp==null||pag.getVisibility()!=VISIBLE||loaded.isEmpty())return;if(carp.phase()==CarpSequence.Phase.PLAYING){double actual=pag.getProgress();carp.progress(SystemClock.elapsedRealtime(),actual);}long now=SystemClock.elapsedRealtime();pag.setAlpha(carp.alpha(now));handler.removeCallbacks(carpSample);if(carp.needsNextScene()){if(carpPending<0&&!carpSwitchPosted){carpSwitchPosted=true;handler.post(carpSwitch);}}else if(carp.transitioning())handler.postDelayed(carpSample,16);}
    private boolean repeats(JSONObject pet,int index){boolean enabled=android.provider.Settings.Global.getFloat(getContext().getContentResolver(),"animator_duration_scale",1f)!=0;return enabled&&!carpPolicy(pet)&&PlaybackPolicy.repeats(pet.optString("id"),pet.optString("kind"),index,getContext().getSharedPreferences(Pets.PREFS,0).getBoolean("calmPets",false));}
    static float renderHeight(int w,int h){float height=h*(w/(float)h<1.55f?1.05f:1f);return w/(float)h<.75f?Math.min(height,w*1.05f):height;}
    protected void onSizeChanged(int w,int h,int oldW,int oldH){super.onSizeChanged(w,h,oldW,oldH);utility.windowBounds(w,full?Math.max(backdrop.cameraRight,w*.34f):0);mediaGeometry="";}
    protected void onLayout(boolean changed,int left,int top,int right,int bottom){super.onLayout(changed,left,top,right,bottom);if(full){mediaGeometry="";configureMediaGeometry(getWidth(),getHeight());}}
    private void configureMediaGeometry(int w,int h){
        if(miniVisible)return;
        if(w<=0||h<=0)return;JSONObject pet=Pets.current(getContext());boolean glitter=pet.optString("name").equals("Flowing glitter");
        float fraction=getContext().getSharedPreferences(Pets.PREFS,0).getFloat("cameraSafeFraction",CoverGeometry.CAMERA_FRACTION);
        int camera=previewSurface?previewCameraRight:backdrop.cameraRight;
        PAGComposition file=pag.getComposition();boolean isVideo=video.getVisibility()==VISIBLE;
        int sourceW=isVideo?video.videoW:(file==null?0:file.width()),sourceH=isVideo?video.videoH:(file==null?0:file.height());
        if(isVideo&&(sourceW<=0||sourceH<=0)){int[] size=PetEnvelopes.videoSize(getContext(),loaded);sourceW=size[0];sourceH=size[1];}
        if(sourceW<=0||sourceH<=0)return;
        PetLayoutProfile profile=layoutProfile(pet);
        String key=w+"/"+h+"/"+camera+"/"+fraction+"/"+sourceW+"/"+sourceH+"/"+loaded+"/"+profile.key();
        if(key.equals(mediaGeometry))return;mediaGeometry=key;
        if(glitter){pagFrame.topFeather(-1);backdrop.sceneTransform(0,0,0,0,0);LayoutParams params=(LayoutParams)pag.getLayoutParams();if(params.width!=-1||params.height!=-1||params.leftMargin!=0||params.topMargin!=0)pag.setLayoutParams(new LayoutParams(-1,-1));pag.setScaleMode(PAGScaleMode.LetterBox);pag.layout(0,0,w,h);return;}
        float[] envelope=isVideo?null:PetEnvelopes.get(getContext(),pet.optString("id"),loaded);
        PetLayoutProfile geometryProfile=loaded.contains("nfc_")||loaded.contains("pin_show")?PetLayoutProfile.CLOCK:profile;
        boolean canvasRole=!pet.optString("renderRole","pet").equals("pet");
        CoverGeometry.Placement placement=canvasRole?CoverGeometry.canvas(w,h,sourceW,sourceH):CoverGeometry.profile(w,h,sourceW,sourceH,envelope,camera,fraction,pet.optString("id"),geometryProfile);backdrop.invalidate();
        boolean scenery=!isVideo&&PetEnvelopes.opaqueScenery(pet.optString("id"));
        backdrop.sceneTransform(scenery?sourceW:0,scenery?sourceH:0,placement.scale,placement.x,placement.y);pagFrame.topFeather(scenery?placement.y:-1);
        if(isVideo){if(canvasRole)video.layout(0,0,w,h);else{int vw=Math.max(1,Math.round(sourceW*placement.scale)),vh=Math.max(1,Math.round(sourceH*placement.scale));video.layout(Math.round(placement.x),Math.round(placement.y),Math.round(placement.x)+vw,Math.round(placement.y)+vh);}video.fit();}
        else {
            // Keep lower branches/ground continuous: camera safety comes from
            // fixed subject placement, never a straight full-height column crop.
            LayoutParams params=(LayoutParams)pag.getLayoutParams();if(params.width!=-1||params.height!=-1||params.leftMargin!=0||params.topMargin!=0)pag.setLayoutParams(new LayoutParams(-1,-1));
            pag.layout(0,0,w,h);pag.setScaleMode(PAGScaleMode.None);android.graphics.Matrix matrix=new android.graphics.Matrix();matrix.setScale(placement.scale,placement.scale);matrix.postTranslate(placement.x,placement.y);pag.setMatrix(matrix);
        }
        String geometry="display="+(getDisplay()==null?-1:getDisplay().getDisplayId())+" preview="+previewSurface+" stage="+w+"x"+h+" safe="+placement.left+","+placement.top+","+placement.right+","+placement.bottom+" source="+sourceW+"x"+sourceH+" scale="+placement.scale+" translate="+placement.x+","+placement.y;
        if(!geometry.equals(lastGeometry)){lastGeometry=geometry;AppLog.event(getContext(),"GEOMETRY",geometry);}
    }
    int parseColor(String s){try{return Color.parseColor(s);}catch(Exception e){return 0xff444e70;}}
    public void onSensorChanged(SensorEvent e){if(e.sensor.getType()==Sensor.TYPE_STEP_DETECTOR){Pets.state.sensorStep(e.timestamp,SystemClock.elapsedRealtime());StepStore.step(getContext(),e.timestamp);}else if(e.sensor.getType()==Sensor.TYPE_ACCELEROMETER){Pets.tiltX=Pets.tiltX*.85f+e.values[0]/9.81f*.15f;Pets.tiltY=Pets.tiltY*.85f+e.values[1]/9.81f*.15f;}}
    public void onAccuracyChanged(Sensor s,int accuracy){}
}
