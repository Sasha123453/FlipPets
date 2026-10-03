package org.flippets.app;

import android.app.*;
import android.os.*;
import android.view.*;

public class PetActivity extends Activity {
    PetStage stage;
    HingeFade hinge;
    static final java.util.Set<PetActivity> covers=java.util.Collections.newSetFromMap(new java.util.WeakHashMap<PetActivity,Boolean>());
    public static void closeCovers(){for(PetActivity activity:new java.util.ArrayList<>(covers)){activity.getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);activity.finishAndRemoveTask();}covers.clear();}
    protected void onCreate(Bundle saved){super.onCreate(saved);AppLog.event(this,"ACTIVITY_CREATE","display="+getWindowManager().getDefaultDisplay().getDisplayId()+" coverSession="+getIntent().getBooleanExtra("coverSession",false));if(getIntent().getBooleanExtra("coverSession",false))covers.add(this);else getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);if(Build.VERSION.SDK_INT>=30){WindowManager.LayoutParams params=getWindow().getAttributes();params.layoutInDisplayCutoutMode=WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS;getWindow().setAttributes(params);}getWindow().getDecorView().setSystemUiVisibility(5894);
        boolean emulator=Build.HARDWARE.contains("ranchu")||Build.HARDWARE.contains("goldfish");
        if(emulator&&getIntent().hasExtra("qaPet")){int index=getIntent().getIntExtra("qaPet",0);if(index>=0&&index<Pets.catalog(this).length())Pets.select(this,index);Pets.scene=0;Pets.state.overrideUntil=0;}
        stage=new PetStage(this,true);setContentView(stage);getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(android.graphics.Color.BLACK));
        if(getIntent().getBooleanExtra("coverSession",false)&&!(emulator&&getIntent().hasExtra("qaHingeAngle")))hinge=new HingeFade(this,stage);
        if(emulator&&getIntent().getBooleanExtra("qaSwitch",false))stage.postDelayed(()->UiQa.start(this),1200);
        if(emulator&&getIntent().getBooleanExtra("qaUtilities",false))stage.postDelayed(()->UtilityQa.start(this),1200);
        if(emulator&&getIntent().getBooleanExtra("qaComposition",false))new Thread(()->CompositionQa.run(this),"composition-qa").start();
        if(emulator&&getIntent().getBooleanExtra("qa",false))new Thread(()->Qa.run(this),"pag-qa").start();
    }
    protected void onStart(){super.onStart();if(getIntent().getBooleanExtra("coverSession",false)){if(getWindowManager().getDefaultDisplay().getDisplayId()!=Display.DEFAULT_DISPLAY)CoverGuard.activate(this);else CoverGuard.ensureStarted(this);}stage.start();if(hinge!=null)hinge.start();boolean emulator=Build.HARDWARE.contains("ranchu")||Build.HARDWARE.contains("goldfish");if(emulator&&getIntent().hasExtra("qaHingeAngle"))stage.setAlpha(HingeOpacity.degrees(getIntent().getFloatExtra("qaHingeAngle",180)));if(emulator&&getIntent().getBooleanExtra("qaGuard",false))CoverGuard.activate(this);}
    protected void onResume(){super.onResume();if(getIntent().getBooleanExtra("coverSession",false)&&getWindowManager().getDefaultDisplay().getDisplayId()!=Display.DEFAULT_DISPLAY)CoverGuard.ensureStarted(this);}
    public void onConfigurationChanged(android.content.res.Configuration config){super.onConfigurationChanged(config);getWindow().getDecorView().setSystemUiVisibility(5894);stage.requestApplyInsets();stage.requestLayout();AppLog.event(this,"CONFIGURATION","display="+getWindowManager().getDefaultDisplay().getDisplayId()+" orientation="+config.orientation);}
    protected void onStop(){if(hinge!=null)hinge.stop();stage.stop();super.onStop();}
    protected void onDestroy(){covers.remove(this);stage.destroy();super.onDestroy();}
}
