package org.flippets.app;

import android.os.*;
import android.view.View;
import org.json.*;

/** Exercise decoder/Canvas transitions in one activity on the emulator. */
public final class UiQa implements Runnable {
    final PetActivity activity;final Handler handler=new Handler(Looper.getMainLooper());
    final JSONArray results=new JSONArray();int cursor,failed;final int saved;
    final int[] sequence={0,19,15,24,6,25,1,28,16,23,26,22,27,29,0};
    UiQa(PetActivity a){activity=a;saved=a.getSharedPreferences(Pets.PREFS,0).getInt("pet",0);}
    public static void start(PetActivity a){new UiQa(a).run();}
    public void run(){if(activity.isDestroyed()||activity.isFinishing())return;
        if(cursor>=sequence.length){try{Pets.write(activity,"ui-switch-qa.json",new JSONObject().put("apkSha256",Qa.binarySha(activity)).put("tested",results.length()).put("failed",failed).put("results",results).toString(2));}catch(Exception ignored){}Pets.select(activity,saved);activity.stage.reload();return;}
        int index=sequence[cursor++];Pets.select(activity,index);Pets.scene=0;Pets.state.overrideUntil=0;activity.stage.reload();Pets.signal(activity);
        handler.postDelayed(()->{PetStage s=activity.stage;JSONObject pet=Pets.current(activity);String kind=pet.optString("kind");boolean ok=kind.equals("composition")?s.composition.getVisibility()==View.VISIBLE&&s.pag.getVisibility()==View.GONE&&s.video.getVisibility()==View.GONE:kind.equals("video")?s.video.getVisibility()==View.VISIBLE&&s.composition.getVisibility()==View.GONE:s.pag.getVisibility()==View.VISIBLE&&s.pag.getComposition()!=null&&s.composition.getVisibility()==View.GONE;
            try{results.put(new JSONObject().put("pet",pet.optString("name")).put("kind",kind).put("ok",ok));}catch(Exception ignored){}if(!ok)failed++;run();},1200);
    }
}
