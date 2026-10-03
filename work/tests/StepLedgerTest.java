import org.flippets.app.StepLedger;
public class StepLedgerTest {
    static int checks;
    static void check(boolean yes,String name){checks++;if(!yes)throw new AssertionError(name);}
    public static void main(String[] args){
        StepLedger s=new StepLedger();
        check(s.step("2026-10-03",11,1000),"first step");
        check(!s.step("2026-10-03",11,1000),"two displays same event");
        check(!s.step("2026-10-03",11,999),"out of order");
        check(s.total==1&&s.hours[11]==1,"duplicates do not affect totals");
        check(s.step("2026-10-03",12,1001),"next hour");
        check(s.total==2&&s.hours[12]==1,"hour buckets");
        check(!s.step("2026-10-03",24,1002),"invalid hour");
        check(s.step("2026-10-04",0,1003),"midnight");
        check(s.total==1&&s.hours[11]==0&&s.hours[12]==0&&s.hours[0]==1,"daily reset");
        s.reboot();check(s.step("2026-10-04",1,1),"sensor timestamp restarts after reboot");
        check(s.total==2,"reboot preserves day total");
        s.date("2026-10-05");check(s.total==0,"midnight without events");
        System.out.println("PASS "+checks+" StepLedger checks");
    }
}
