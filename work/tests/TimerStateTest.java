import org.flippets.app.TimerState;

/** Tests persistence boundaries and asleep time, independent of Android scheduling. */
public final class TimerStateTest {
    static int assertions;
    static void eq(long expected,long actual,String scenario){assertions++;if(expected!=actual)throw new AssertionError(scenario+": "+actual+" != "+expected);}
    static void yes(boolean condition,String scenario){assertions++;if(!condition)throw new AssertionError(scenario);}
    public static void main(String[] args){
        TimerState s=new TimerState("stopwatch",false,0,0,7,1000,7);s.toggle(1000);
        eq(60000,s.elapsed(61000),"sleep does not lose elapsed time");s.toggle(61000);eq(60000,s.elapsed(100000),"paused time does not advance");
        s.toggle(100000);eq(61000,s.elapsed(101000),"resume keeps accumulated time");s.checkpoint(101000);
        TimerState restored=new TimerState(s.mode,s.running,s.accumulated,s.started,s.boot,106000,7);eq(66000,restored.elapsed(106000),"same boot restores running timer");
        TimerState rebooted=new TimerState(s.mode,s.running,s.accumulated,s.started,s.boot,5000,8);yes(!rebooted.running,"new boot pauses");eq(61000,rebooted.elapsed(20000),"new boot keeps last checkpoint");
        TimerState unknown=new TimerState(s.mode,true,1234,500,7,1000,-1);yes(!unknown.running,"unknown boot fails closed");
        TimerState future=new TimerState("stopwatch",true,333,20000,7,1000,7);yes(!future.running,"future monotonic timestamp pauses");
        s.select("focus",110000);eq(TimerState.FOCUS_MS,s.displayed(110000),"focus starts at 25 minutes");yes(!s.running,"changing mode does not silently start");s.toggle(110000);
        eq(1000,s.displayed(110000+TimerState.FOCUS_MS-1000),"remaining time before deadline");yes(!s.finishIfNeeded(110000+TimerState.FOCUS_MS-1),"not complete early");
        yes(s.finishIfNeeded(110000+TimerState.FOCUS_MS),"deadline completes exactly");yes(!s.running,"completion pauses");eq(0,s.displayed(99999999),"completed remaining never negative");yes(!s.finishIfNeeded(99999999),"completion emitted once");
        s.toggle(99999999);yes(s.running,"start after completion restarts");eq(TimerState.FOCUS_MS,s.displayed(99999999),"restart full duration");s.reset(100000000);yes(!s.running,"reset pauses");eq(0,s.elapsed(100000000),"reset clears elapsed");
        s.select("stopwatch",100000000);eq(0,s.displayed(100000000),"stopwatch display counts up");s.toggle(100000000);yes(!s.finishIfNeeded(100000000+TimerState.FOCUS_MS*2),"stopwatch has no deadline");
        TimerState bad=new TimerState("unknown",false,-40,0,7,1000,7);eq(0,bad.elapsed(1000),"negative saved time bounded");yes(bad.mode.equals("stopwatch"),"unknown mode fallback");
        System.out.println("TimerState: "+assertions+" assertions passed");
    }
}