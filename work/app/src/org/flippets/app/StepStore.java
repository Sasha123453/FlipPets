package org.flippets.app;

import android.content.*;
import java.text.SimpleDateFormat;
import java.util.*;

public final class StepStore {
    static StepLedger ledger;
    static String day(){return new SimpleDateFormat("yyyy-MM-dd",Locale.US).format(new Date());}
    public static synchronized StepLedger get(Context c){
        if(ledger==null){ledger=new StepLedger();SharedPreferences p=c.getSharedPreferences("steps",0);
            ledger.day=p.getString("day","");ledger.total=p.getInt("total",0);for(int i=0;i<24;i++)ledger.hours[i]=p.getInt("hour"+i,0);
            int boot=android.provider.Settings.Global.getInt(c.getContentResolver(),"boot_count",-1);
            if(boot==p.getInt("boot",-2))ledger.lastEvent=p.getLong("last",-1);
        }
        ledger.date(day());return ledger;
    }
    public static synchronized void step(Context c,long timestamp){
        StepLedger s=get(c);if(!s.step(day(),Calendar.getInstance().get(Calendar.HOUR_OF_DAY),timestamp))return;
        SharedPreferences.Editor p=c.getSharedPreferences("steps",0).edit().putString("day",s.day).putInt("total",s.total).putLong("last",s.lastEvent).putInt("boot",android.provider.Settings.Global.getInt(c.getContentResolver(),"boot_count",-1));
        for(int i=0;i<24;i++)p.putInt("hour"+i,s.hours[i]);p.apply();
    }
}
