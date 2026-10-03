package org.flippets.app;

/** Monotonic timer model. No Android clocks or persistence in this class. */
public final class TimerState {
    public static final long FOCUS_MS=25L*60*1000;
    public String mode;
    public boolean running;
    public long accumulated, started;
    public int boot;
    public TimerState(String mode,boolean running,long accumulated,long started,int boot,long now,int currentBoot){
        this.mode="focus".equals(mode)?"focus":"stopwatch";
        this.accumulated=Math.max(0,accumulated);
        this.started=started;this.boot=currentBoot;
        this.running=running&&boot>=0&&currentBoot==boot&&started>=0&&started<=now;
        if("focus".equals(this.mode))this.accumulated=Math.min(FOCUS_MS,this.accumulated);
    }
    public long elapsed(long now){long value=accumulated+(running?Math.max(0,now-started):0);return "focus".equals(mode)?Math.min(FOCUS_MS,value):value;}
    public long displayed(long now){return "focus".equals(mode)?Math.max(0,FOCUS_MS-elapsed(now)):elapsed(now);}
    public void checkpoint(long now){accumulated=elapsed(now);started=now;}
    public void toggle(long now){checkpoint(now);if(!running&&"focus".equals(mode)&&accumulated>=FOCUS_MS)accumulated=0;running=!running;}
    public void reset(long now){accumulated=0;started=now;running=false;}
    public void select(String selected,long now){mode="focus".equals(selected)?"focus":"stopwatch";reset(now);}
    public boolean finishIfNeeded(long now){if(running&&"focus".equals(mode)&&elapsed(now)>=FOCUS_MS){accumulated=FOCUS_MS;started=now;running=false;return true;}return false;}
}
