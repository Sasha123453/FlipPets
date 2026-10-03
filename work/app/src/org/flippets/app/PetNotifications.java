package org.flippets.app;
import android.service.notification.*;
import android.os.*;
import android.media.session.*;
import android.content.*;
import java.util.*;
import java.util.concurrent.CopyOnWriteArraySet;

public class PetNotifications extends NotificationListenerService {
    private MediaSessionManager manager;
    private final Map<MediaController,MediaController.Callback> callbacks=new LinkedHashMap<>();
    private final MediaSessionManager.OnActiveSessionsChangedListener sessions=this::bind;
    private static volatile MediaController media;
    private static volatile boolean available;
    private static final Set<Runnable> mediaListeners=new CopyOnWriteArraySet<>();
    private static final Handler main=new Handler(Looper.getMainLooper());
    public static void addMediaListener(Runnable listener){mediaListeners.add(listener);}
    public static void removeMediaListener(Runnable listener){mediaListeners.remove(listener);}
    public static MediaController currentMedia(){return media;}
    public static boolean listenerAvailable(){return available;}
    public static boolean isPlaying(PlaybackState state){return state!=null&&(state.getState()==PlaybackState.STATE_PLAYING||state.getState()==PlaybackState.STATE_BUFFERING||state.getState()==PlaybackState.STATE_CONNECTING);}
    public static boolean canControl(String action){
        MediaController c=media;PlaybackState s=c==null?null:c.getPlaybackState();if(s==null)return false;long mask=s.getActions();
        if("next".equals(action))return (mask&PlaybackState.ACTION_SKIP_TO_NEXT)!=0;
        if(!"toggle".equals(action))return false;
        return (mask&(PlaybackState.ACTION_PLAY_PAUSE|(isPlaying(s)?PlaybackState.ACTION_PAUSE:PlaybackState.ACTION_PLAY)))!=0;
    }
    public static boolean control(String action){
        MediaController c=media;if(c==null||!canControl(action))return false;
        try{MediaController.TransportControls t=c.getTransportControls();if("next".equals(action))t.skipToNext();else if(isPlaying(c.getPlaybackState()))t.pause();else t.play();return true;}catch(RuntimeException e){return false;}
    }
    private static void notifyMedia(){for(Runnable listener:mediaListeners)main.post(()->{if(mediaListeners.contains(listener))listener.run();});}
    @Override public void onListenerConnected(){
        if(manager!=null){try{manager.removeOnActiveSessionsChangedListener(sessions);}catch(RuntimeException ignored){}}
        available=true;manager=(MediaSessionManager)getSystemService(MEDIA_SESSION_SERVICE);
        try{manager.addOnActiveSessionsChangedListener(sessions,new ComponentName(this,PetNotifications.class));bind(manager.getActiveSessions(new ComponentName(this,PetNotifications.class)));}catch(SecurityException e){available=false;bind(Collections.emptyList());}
    }
    private void bind(List<MediaController> list){
        for(Map.Entry<MediaController,MediaController.Callback> e:callbacks.entrySet())e.getKey().unregisterCallback(e.getValue());callbacks.clear();
        if(list!=null)for(MediaController controller:list){
            MediaController.Callback cb=new MediaController.Callback(){
                @Override public void onPlaybackStateChanged(PlaybackState s){refresh();}
                @Override public void onMetadataChanged(android.media.MediaMetadata metadata){notifyMedia();}
                @Override public void onSessionDestroyed(){callbacks.remove(controller);controller.unregisterCallback(this);refresh();}
            };controller.registerCallback(cb,main);callbacks.put(controller,cb);
        }
        refresh();
    }
    private void refresh(){
        boolean playing=false;MediaController selected=null;
        for(MediaController c:callbacks.keySet()){if(selected==null)selected=c;PlaybackState s=c.getPlaybackState();if(isPlaying(s)){selected=c;playing=true;break;}}
        media=selected;Pets.state.music=playing;Pets.signal(this);notifyMedia();
    }
    @Override public void onNotificationPosted(StatusBarNotification n){if(n.getPackageName().equals(getPackageName())||n.isOngoing())return;if(!getSharedPreferences(Pets.PREFS,0).getBoolean("notifications",true))return;Pets.state.notificationUntil=SystemClock.elapsedRealtime()+6000;Pets.signal(this);}
    @Override public void onListenerDisconnected(){available=false;if(manager!=null){try{manager.removeOnActiveSessionsChangedListener(sessions);}catch(RuntimeException ignored){}manager=null;}bind(Collections.emptyList());}
    @Override public void onDestroy(){onListenerDisconnected();super.onDestroy();}
}
