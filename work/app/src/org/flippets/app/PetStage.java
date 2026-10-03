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
    final PetVideo video;
    final CompositionView composition;
    final PhotoLayer photo,front;
    boolean gravityRegistered;
    final TextView clock;
    final PetBackdrop backdrop;
    final boolean full;
    final Handler handler=new Handler(Looper.getMainLooper());
    final SensorManager sensors;
    boolean running;
    String loaded="";long visualStamp=-1,lastBackdropMinute=-1;
    int tap;
    long lastPlayRevision=-1;
    String lastGeometry="";
    final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context c,Intent i){Pets.battery(c);update();}};
    final Runnable ticker=new Runnable(){public void run(){if(!running)return;update();handler.postDelayed(this,composition.getVisibility()==VISIBLE?composition.nextDelay():250);}};
    public PetStage(Context c,boolean showClock){
        super(c);full=showClock;sensors=(SensorManager)c.getSystemService(Context.SENSOR_SERVICE);
        photo=new PhotoLayer(c,false);addView(photo,new LayoutParams(-1,-1));photo.setVisibility(GONE);
        backdrop=new PetBackdrop(c,showClock);addView(backdrop,new LayoutParams(-1,-1));
        pag=new PAGView(c);pag.setRepeatCount(0);pag.setScaleMode(PAGScaleMode.LetterBox);pag.setMaxFrameRate(FlipPetsApp.frameRate(c));
        pag.addListener(new PAGView.PAGViewListener(){public void onAnimationStart(PAGView v){}public void onAnimationEnd(PAGView v){AppLog.event(c,"PLAYBACK_END",loaded+" progress="+v.getProgress());}public void onAnimationCancel(PAGView v){}public void onAnimationRepeat(PAGView v){}public void onAnimationUpdate(PAGView v){}});
        addView(pag,new LayoutParams(-1,-1));
        video=new PetVideo(c);addView(video,new LayoutParams(-1,-1));video.setVisibility(GONE);
        front=new PhotoLayer(c,true);addView(front,new LayoutParams(-1,-1));front.setVisibility(GONE);
        composition=new CompositionView(c);addView(composition,new LayoutParams(-1,-1));composition.setVisibility(GONE);
        clock=new TextView(c);clock.setTextColor(Color.WHITE);clock.setTextSize(34);clock.setGravity(Gravity.CENTER);clock.setShadowLayer(4,0,1,0x33000000);
        LayoutParams cp=new LayoutParams(-1,-2,Gravity.TOP|Gravity.CENTER_HORIZONTAL);cp.topMargin=24;addView(clock,cp);clock.setVisibility(GONE);
        setOnApplyWindowInsetsListener((v,insets)->{android.view.DisplayCutout cutout=insets.getDisplayCutout();backdrop.cameraRight=0;if(cutout!=null)for(android.graphics.Rect rect:cutout.getBoundingRects())if(rect.left==0)backdrop.cameraRight=Math.max(backdrop.cameraRight,rect.right);composition.renderer.cameraRight=backdrop.cameraRight;return insets;});
        View.OnClickListener clicked=v->{JSONObject pet=Pets.current(c);if(pet.optString("kind").equals("reactive")){if(Pets.stageIndex(c)>=8&&pag.isPlaying())return;Pets.override(c,12+(tap++%3),4500);}else{JSONObject clips=pet.optJSONObject("clips");int count=clips==null?0:clips.length();if(PlaybackPolicy.classic(pet.optString("id"))){if(pag.isPlaying())return;count=pet.optInt("touchSceneCount",count);int current=Pets.stageIndex(c),next=current;if(!pet.optString("id").startsWith("bird-")&&count>1)next=(current+1+new Random().nextInt(count-1))%count;Pets.choose(c,next);}else if(count>0)Pets.choose(c,(Pets.scene+1)%count);}};
        pag.setOnClickListener(clicked);video.setOnClickListener(clicked);
        setContentDescription("Анимированный питомец. Коснись для реакции.");
    }
    public void start(){
        if(running)return;running=true;AppLog.event(getContext(),"STAGE_START","display="+(getDisplay()==null?-1:getDisplay().getDisplayId())+" full="+full);
        IntentFilter f=new IntentFilter(Pets.EVENT);f.addAction(Intent.ACTION_BATTERY_CHANGED);
        if(Build.VERSION.SDK_INT>=33)getContext().registerReceiver(receiver,f,Context.RECEIVER_NOT_EXPORTED);else getContext().registerReceiver(receiver,f);
        if(getContext().checkSelfPermission(Manifest.permission.ACTIVITY_RECOGNITION)==PackageManager.PERMISSION_GRANTED){Sensor step=sensors.getDefaultSensor(Sensor.TYPE_STEP_DETECTOR);if(step!=null)sensors.registerListener(this,step,SensorManager.SENSOR_DELAY_NORMAL);}
        Pets.battery(getContext());requestApplyInsets();requestLayout();handler.post(ticker);video.start();
    }
    public void stop(){if(!running)return;running=false;AppLog.event(getContext(),"STAGE_STOP","full="+full);handler.removeCallbacks(ticker);getContext().unregisterReceiver(receiver);sensors.unregisterListener(this);gravityRegistered=false;pag.pause();pag.setComposition(null);pag.freeCache();video.pause();video.load("");loaded="";composition.renderer.release();backdrop.release();photo.release();front.release();}
    public void destroy(){stop();pag.setComposition(null);pag.freeCache();video.destroy();composition.renderer.release();backdrop.release();photo.release();front.release();}
    public void reload(){loaded="";visualStamp=-1;if(running)update();}
    private void update(){
        Context c=getContext();pag.setMaxFrameRate(FlipPetsApp.frameRate(c));JSONObject selected=Pets.current(c);boolean composed=selected.optString("kind").equals("composition");boolean glitter=selected.optString("name").equals("Flowing glitter");
        if(running&&glitter!=gravityRegistered){Sensor gravity=sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);if(gravity!=null){if(glitter)sensors.registerListener(this,gravity,SensorManager.SENSOR_DELAY_UI);else sensors.unregisterListener(this,gravity);}gravityRegistered=glitter;}
        if(composed){if(composition.getVisibility()!=VISIBLE){pag.pause();pag.setComposition(null);video.pause();video.load("");loaded="";}composition.setVisibility(VISIBLE);backdrop.setVisibility(GONE);pag.setVisibility(GONE);video.setVisibility(GONE);photo.setVisibility(GONE);front.setVisibility(GONE);long stamp=System.currentTimeMillis()/60000^c.getSharedPreferences(Pets.PREFS,0).getLong("changeRevision",0);if(composition.nextDelay()<1000||stamp!=visualStamp){composition.invalidate();visualStamp=stamp;}return;}
        composition.setVisibility(GONE);backdrop.setVisibility(VISIBLE);photo.setVisibility(glitter?VISIBLE:GONE);front.setVisibility(glitter?VISIBLE:GONE);if(glitter){photo.invalidate();front.invalidate();}
        int index=Pets.stageIndex(c);String path=Pets.path(c,index);
        if(path.isEmpty())path=Pets.path(c,0);
        if(!path.equals(loaded)){AppLog.event(c,"LOAD",path);
            if(path.endsWith(".mp4")){pag.pause();pag.setVisibility(GONE);video.setVisibility(VISIBLE);video.load(path);if(running)video.start();loaded=path;}
            else{video.pause();video.load("");video.setVisibility(GONE);pag.setVisibility(VISIBLE);PAGFile file=PAGFile.Load(c.getAssets(),path);if(file!=null){pag.setRepeatCount(repeats(selected,index)?0:1);pag.setComposition(file);pag.setProgress(0);pag.play();loaded=path;lastPlayRevision=Pets.playRevision;AppLog.event(c,"PLAYBACK",path+" repeat="+repeats(selected,index)+" durationUs="+file.duration());}else AppLog.event(c,"PAG_LOAD_ERROR",path);}
            lastBackdropMinute=-1;JSONObject pet=Pets.current(c);int from=parseColor(pet.optString("gradientFrom","#444E70")),to=parseColor(pet.optString("gradientTo","#647D98"));
            setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{from,to}));
        }
        if(pag.getVisibility()==VISIBLE&&pag.getComposition()!=null){pag.setRepeatCount(repeats(selected,index)?0:1);if(lastPlayRevision!=Pets.playRevision){lastPlayRevision=Pets.playRevision;pag.setProgress(0);pag.play();}}
        long minute=System.currentTimeMillis()/60000;if(glitter||minute!=lastBackdropMinute){backdrop.invalidate();lastBackdropMinute=minute;}
    }
    private boolean repeats(JSONObject pet,int index){boolean enabled=android.provider.Settings.Global.getFloat(getContext().getContentResolver(),"animator_duration_scale",1f)!=0;return enabled&&PlaybackPolicy.repeats(pet.optString("id"),pet.optString("kind"),index,getContext().getSharedPreferences(Pets.PREFS,0).getBoolean("calmPets",false));}
    static float renderHeight(int w,int h){float height=h*(w/(float)h<1.55f?1.05f:1f);return w/(float)h<.75f?Math.min(height,w*1.05f):height;}
    protected void onSizeChanged(int w,int h,int oldW,int oldH){super.onSizeChanged(w,h,oldW,oldH);if(full&&w>0&&h>0){float height=renderHeight(w,h);int width=w/(float)h<1.55f?Math.round(height*976/596):w;LayoutParams lp=new LayoutParams(width,Math.round(height),Gravity.RIGHT|Gravity.BOTTOM);lp.rightMargin=-Math.round(w/336f);lp.bottomMargin=-Math.round(4*h/213f);pag.setLayoutParams(lp);}}
    protected void onLayout(boolean changed,int left,int top,int right,int bottom){super.onLayout(changed,left,top,right,bottom);if(!full||getWidth()<=0||getHeight()<=0)return;int w=getWidth(),h=getHeight(),ph=Math.round(renderHeight(w,h)),pw=w/(float)h<1.55f?Math.round(renderHeight(w,h)*976/596):w;int pr=w+Math.round(w/336f),pb=h+Math.round(4*h/213f);if(pag.getVisibility()!=GONE)pag.layout(pr-pw,pb-ph,pr,pb);String geometry="display="+(getDisplay()==null?-1:getDisplay().getDisplayId())+" rotation="+(getDisplay()==null?-1:getDisplay().getRotation())+" stage="+w+"x"+h+" pag="+pag.getLeft()+","+pag.getTop()+","+pag.getRight()+","+pag.getBottom()+" camera="+backdrop.cameraRight;if(!geometry.equals(lastGeometry)){lastGeometry=geometry;AppLog.event(getContext(),"GEOMETRY",geometry);}}
    int parseColor(String s){try{return Color.parseColor(s);}catch(Exception e){return 0xff444e70;}}
    public void onSensorChanged(SensorEvent e){if(e.sensor.getType()==Sensor.TYPE_STEP_DETECTOR){Pets.state.sensorStep(e.timestamp,SystemClock.elapsedRealtime());StepStore.step(getContext(),e.timestamp);}else if(e.sensor.getType()==Sensor.TYPE_ACCELEROMETER){Pets.tiltX=Pets.tiltX*.85f+e.values[0]/9.81f*.15f;Pets.tiltY=Pets.tiltY*.85f+e.values[1]/9.81f*.15f;}}
    public void onAccuracyChanged(Sensor s,int accuracy){}
}
