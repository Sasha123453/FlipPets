package org.flippets.app;

import android.content.*;
import android.hardware.*;
import android.os.Build;
import android.view.View;
import android.view.animation.LinearInterpolator;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** On-change hinge sensor, active only for our visible cover session. No angle polling. */
final class HingeFade implements SensorEventListener,SharedPreferences.OnSharedPreferenceChangeListener {
    final Context context;final View target;final SensorManager manager;final File marker;
    final String token=Long.toString(android.os.SystemClock.elapsedRealtimeNanos());
    boolean started,registered,angular;float requested=1;
    HingeFade(Context c,View v){context=c;target=v;manager=(SensorManager)c.getSystemService(Context.SENSOR_SERVICE);marker=new File(c.getExternalFilesDir(null),"hinge-fade-active");}
    void start(){if(started)return;started=true;context.getSharedPreferences(Pets.PREFS,0).registerOnSharedPreferenceChangeListener(this);configure();}
    void configure(){manager.unregisterListener(this);registered=false;clearMarker();target.animate().cancel();requested=1;target.setAlpha(1);
        if(!started||!context.getSharedPreferences(Pets.PREFS,0).getBoolean("hingeFade",true))return;
        Sensor sensor=Build.VERSION.SDK_INT>=30?manager.getDefaultSensor(Sensor.TYPE_HINGE_ANGLE):null;angular=sensor!=null;
        if(sensor==null)for(Sensor candidate:manager.getSensorList(Sensor.TYPE_ALL))if("xiaomi.sensor.flip_status".equals(candidate.getStringType())){sensor=candidate;break;}
        if(sensor==null){AppLog.event(context,"HINGE_FADE","No hinge angle or Xiaomi flip-status sensor available; stock transition preserved");return;}
        try{registered=manager.registerListener(this,sensor,SensorManager.SENSOR_DELAY_UI);if(registered){try(FileOutputStream out=new FileOutputStream(marker)){out.write(token.getBytes(StandardCharsets.UTF_8));}AppLog.event(context,"HINGE_FADE","source="+(angular?"degrees":"discrete states")+" name="+sensor.getName()+" type="+sensor.getStringType());}}
        catch(Exception e){manager.unregisterListener(this);registered=false;clearMarker();AppLog.error(context,"HINGE_FADE_REGISTER",e);}
    }
    void stop(){if(!started)return;started=false;context.getSharedPreferences(Pets.PREFS,0).unregisterOnSharedPreferenceChangeListener(this);manager.unregisterListener(this);registered=false;clearMarker();target.animate().cancel();target.setAlpha(1);}
    void clearMarker(){try{if(!marker.exists())return;byte[] bytes=new byte[64];try(FileInputStream in=new FileInputStream(marker)){int n=in.read(bytes);if(n>0&&token.equals(new String(bytes,0,n,StandardCharsets.UTF_8)))marker.delete();}}catch(Exception e){AppLog.error(context,"HINGE_FADE_MARKER",e);}}
    public void onSensorChanged(SensorEvent event){if(!registered||event.values.length==0)return;float alpha=angular?HingeOpacity.degrees(event.values[0]):HingeOpacity.status(event.values[0]);if(Math.abs(alpha-requested)<.005f)return;requested=alpha;target.animate().cancel();target.animate().alpha(alpha).setDuration(angular?100:240).setInterpolator(new LinearInterpolator()).start();}
    public void onAccuracyChanged(Sensor sensor,int accuracy){}
    public void onSharedPreferenceChanged(SharedPreferences prefs,String key){if("hingeFade".equals(key))configure();}
}
