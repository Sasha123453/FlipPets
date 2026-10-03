package org.flippets.app;

/** Counts only sensor events observed by this app, deduplicated across displays. */
public final class StepLedger {
    public String day="";
    public int total;
    public final int[] hours=new int[24];
    public long lastEvent=-1;
    public void date(String today){if(!today.equals(day)){day=today;total=0;java.util.Arrays.fill(hours,0);}}
    public boolean step(String today,int hour,long timestamp){
        date(today);if(timestamp<=lastEvent||hour<0||hour>23)return false;
        lastEvent=timestamp;total++;hours[hour]++;return true;
    }
    public void reboot(){lastEvent=-1;}
}
