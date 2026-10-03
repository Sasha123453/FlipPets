package org.flippets.app;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.content.pm.ServiceInfo;
import android.os.*;
import android.provider.Settings;

/** Keeps the user-enabled cover session independent of the configuration task. No polling. */
public final class CoverGuard extends Service {
    public static final String ACTION_STOP="org.flippets.app.COVER_SESSION_STOP";
    public static final int NOTIFICATION_PERMISSION_REQUEST=42;
    private static final String CHANNEL="cover_session",WANTED="coverGuardEnabled",BOOT="coverGuardBoot";
    private static final int NOTIFICATION=1701;
    private static boolean running;
    private boolean foreground;

    private static int boot(Context c){try{return Settings.Global.getInt(c.getContentResolver(),Settings.Global.BOOT_COUNT,-1);}catch(Exception e){return -1;}}
    public static boolean isEnabled(Context c){android.content.SharedPreferences p=c.getSharedPreferences(Pets.PREFS,0);return p.getBoolean(WANTED,false)&&p.getInt(BOOT,-2)==boot(c);}
    /** Accepted shell Start, or a visible controller-launched session on the secondary display. */
    public static void activate(Context c){java.io.File stop=new java.io.File(c.getExternalFilesDir(null),"controller-stop");if(stop.exists())return;c.getSharedPreferences(Pets.PREFS,0).edit().putBoolean(WANTED,true).putInt(BOOT,boot(c)).apply();ensureStarted(c);}
    /** A visible cover activity can retry a start denied while the configuration UI was hidden. */
    public static void ensureStarted(Context c){if(!isEnabled(c)||running)return;try{c.startForegroundService(new Intent(c,CoverGuard.class));}catch(Exception e){AppLog.error(c,"GUARD_START_DENIED",e);}}
    /** Explicit user stop; fold/screen-off lifecycle transitions must not call this. */
    public static void stop(Context c){ShizukuBridge.cancelPendingStart();c.getSharedPreferences(Pets.PREFS,0).edit().putBoolean(WANTED,false).apply();running=false;c.stopService(new Intent(c,CoverGuard.class));AppLog.event(c,"GUARD_STOP","user requested");}
    /** Local notification/UI stop, usable even if Shizuku is temporarily unavailable. */
    public static boolean requestStop(Context c){boolean written=true;try{Pets.write(c,"controller-stop","stop\n");}catch(Exception e){written=false;AppLog.error(c,"GUARD_STOP_FILE",e);}PetActivity.closeCovers();stop(c);return written;}
    public static boolean notificationPermissionNeeded(Context c){return Build.VERSION.SDK_INT>=33&&c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED;}
    /** Optional: denial hides the notification but does not prohibit a foreground service. */
    public static void requestNotificationPermission(Activity a){if(notificationPermissionNeeded(a))a.requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},NOTIFICATION_PERMISSION_REQUEST);}

    public void onCreate(){super.onCreate();NotificationChannel channel=new NotificationChannel(CHANNEL,"Внешний экран",NotificationManager.IMPORTANCE_LOW);channel.setDescription("Постоянный сеанс внешнего экрана, включённый пользователем");channel.setSound(null,null);channel.enableVibration(false);getSystemService(NotificationManager.class).createNotificationChannel(channel);}
    private Notification notification(){
        Intent open=new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent content=PendingIntent.getActivity(this,1,open,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop=PendingIntent.getService(this,2,new Intent(this,CoverGuard.class).setAction(ACTION_STOP),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b=new Notification.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_menu_view).setContentTitle("Внешний экран · Flip Pets").setContentText("Сеанс включён · открыть настройки").setContentIntent(content).setOngoing(true).setOnlyAlertOnce(true).setCategory(Notification.CATEGORY_SERVICE).setShowWhen(false).addAction(new Notification.Action.Builder(null,"Выключить",stop).build());
        if(Build.VERSION.SDK_INT>=31)b.setForegroundServiceBehavior(Notification.FOREGROUND_SERVICE_IMMEDIATE);
        return b.build();
    }
    public int onStartCommand(Intent intent,int flags,int startId){
        if(intent!=null&&ACTION_STOP.equals(intent.getAction())){requestStop(this);stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();return START_NOT_STICKY;}
        if(!isEnabled(this)){stopSelf();return START_NOT_STICKY;}
        if(!foreground)try{if(Build.VERSION.SDK_INT>=34)startForeground(NOTIFICATION,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);else startForeground(NOTIFICATION,notification());foreground=true;running=true;AppLog.event(this,"GUARD_START",intent==null?"OS recreated foreground session":"foreground session enabled");}catch(Exception e){AppLog.error(this,"GUARD_FOREGROUND_FAILED",e);stopSelf();return START_NOT_STICKY;}
        return START_STICKY;
    }
    public void onTaskRemoved(Intent root){AppLog.event(this,"GUARD_TASK_REMOVED","task removed; enabled cover session retained");super.onTaskRemoved(root);}
    public void onDestroy(){running=false;foreground=false;AppLog.event(this,"GUARD_DESTROY","service destroyed; enabled="+isEnabled(this));super.onDestroy();}
    public IBinder onBind(Intent intent){return null;}
}
