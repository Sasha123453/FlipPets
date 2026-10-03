package org.flippets.app;
import android.service.notification.*;
import android.os.SystemClock;
import android.media.session.*;
import android.content.*;
import java.util.*;

public class PetNotifications extends NotificationListenerService {
    private MediaSessionManager manager;
    private final Map<MediaController,MediaController.Callback> callbacks=new HashMap<>();
    private final MediaSessionManager.OnActiveSessionsChangedListener sessions=this::bind;
    @Override public void onListenerConnected(){manager=(MediaSessionManager)getSystemService(MEDIA_SESSION_SERVICE);try{manager.addOnActiveSessionsChangedListener(sessions,new ComponentName(this,PetNotifications.class));bind(manager.getActiveSessions(new ComponentName(this,PetNotifications.class)));}catch(SecurityException ignored){}}
    private void bind(List<MediaController> list){for(Map.Entry<MediaController,MediaController.Callback> e:callbacks.entrySet()) e.getKey().unregisterCallback(e.getValue());callbacks.clear();if(list!=null)for(MediaController controller:list){MediaController.Callback cb=new MediaController.Callback(){@Override public void onPlaybackStateChanged(PlaybackState s){refresh();}};controller.registerCallback(cb);callbacks.put(controller,cb);}refresh();}
    private void refresh(){boolean playing=false;for(MediaController c:callbacks.keySet()){PlaybackState s=c.getPlaybackState();if(s!=null && s.getState()==PlaybackState.STATE_PLAYING)playing=true;}Pets.state.music=playing;Pets.signal(this);}
    @Override public void onNotificationPosted(StatusBarNotification n){if(n.getPackageName().equals(getPackageName())||n.isOngoing())return;if(!getSharedPreferences(Pets.PREFS,0).getBoolean("notifications",true))return;Pets.state.notificationUntil=SystemClock.elapsedRealtime()+6000;Pets.signal(this);}
    @Override public void onListenerDisconnected(){if(manager!=null)manager.removeOnActiveSessionsChangedListener(sessions);bind(Collections.emptyList());}
    @Override public void onDestroy(){onListenerDisconnected();super.onDestroy();}
}
