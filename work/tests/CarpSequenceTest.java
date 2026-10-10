import org.flippets.app.CarpSequence;
import java.util.*;

/** Pure source-backed thresholds, load acknowledgement, timing, interruption and isolation. */
public final class CarpSequenceTest {
    static int assertions;
    static void yes(boolean value,String label){assertions++;if(!value)throw new AssertionError(label);}
    static void near(double wanted,double got,double tolerance,String label){yes(Math.abs(wanted-got)<=tolerance,label+": "+wanted+" != "+got);}
    static void rejects(Runnable call,String label){try{call.run();throw new AssertionError(label);}catch(IllegalArgumentException|IllegalStateException expected){assertions++;}}
    static CarpSequence pending(int scene,long start){CarpSequence s=new CarpSequence();s.start(scene,start);s.progress(start,1);s.alpha(start+500);return s;}
    public static void main(String[] args){
        double[] nativeThresholds={689d/719,689d/719,570d/600,566d/596};
        for(int scene=0;scene<4;scene++){
            CarpSequence s=new CarpSequence();near(nativeThresholds[scene],s.threshold(scene),0,"exact MAML threshold");s.start(scene,1000);
            s.progress(1100,nativeThresholds[scene]);yes(s.phase()==CarpSequence.Phase.PLAYING,"source threshold is strictly greater, not equal");near(1,s.alpha(1100),0,"opaque before threshold");
            s.progress(1101,Math.nextUp(nativeThresholds[scene]));yes(s.phase()==CarpSequence.Phase.FADING_OUT,"progress starts one fade");near(1,s.alpha(1101),0,"fade begins opaque");
            s.progress(1151,1);near(.9,s.alpha(1151),.00001,"extra renderer callback does not restart fade");near(.5,s.alpha(1351),.00001,"500ms fade-out midpoint");near(.02,s.alpha(1591),.00001,"500ms fade-out near end");
            near(.02,s.alpha(1200),.00001,"backwards time cannot reverse opacity");near(0,s.alpha(1601),0,"500ms fade reaches zero");yes(s.needsNextScene(),"scene load requested only when invisible");yes(s.scene()==scene,"pending state still owns old scene");
            Set<Integer> alternatives=new HashSet<>();for(int choice=0;choice<3;choice++){int next=s.nextScene(choice);yes(next!=scene&&next>=0&&next<4,"bounded next scene excludes current");alternatives.add(next);}yes(alternatives.size()==3,"all three different choices represented");
            near(0,s.alpha(10000),0,"late loader does not start fade-in without actual acknowledgement");yes(s.needsNextScene(),"pending load persists through late clock jump");int repeatedScene=scene;rejects(()->s.loaded(repeatedScene,10000),"same scene cannot acknowledge transition");
            int next=s.nextScene(2);s.loaded(next,10000);yes(s.scene()==next&&s.phase()==CarpSequence.Phase.HIDDEN_DELAY,"load acknowledgement updates scene at alpha0");yes(s.phaseStartedAt()==10000,"delay starts at actual late-load acknowledgement");near(0,s.alpha(10099),0,"100ms hidden delay");near(0,s.alpha(10100),0,"fade-in begins after exact delay");yes(s.phase()==CarpSequence.Phase.FADING_IN,"fade-in phase after delay");yes(s.phaseStartedAt()==10100,"fade origin includes the full acknowledged100ms delay");
            near(.5,s.alpha(10250),.00001,"300ms fade-in midpoint");near(1,s.alpha(10400),0,"new clip fully visible at delay+300ms");yes(s.phase()==CarpSequence.Phase.PLAYING&&!s.transitioning(),"short transition ends; no permanent frame loop required");
            s.progress(10401,nativeThresholds[next]-.001);yes(s.phase()==CarpSequence.Phase.PLAYING,"new scene threshold independent of previous scene");
            s.progress(10500,1);near(.5,s.alpha(10750),.00001,"next native transition works after first");s.start(scene,10750);near(1,s.alpha(10750),0,"manual selection cancels fade and restores opacity");yes(!s.needsNextScene()&&s.scene()==scene,"manual selection resets pending scene state");
            s.progress(10760,.25);near(1,s.alpha(20000),0,"old transition cannot fire after manual restart");s.stop();near(1,s.alpha(50000),0,"hidden stop restores opacity");yes(s.phase()==CarpSequence.Phase.STOPPED&&!s.transitioning()&&!s.needsNextScene(),"stopped sequence schedules nothing");s.progress(50001,1);yes(s.phase()==CarpSequence.Phase.STOPPED,"late callback cannot revive stopped player");
        }
        CarpSequence noLoad=new CarpSequence();rejects(()->noLoad.nextScene(0),"next requires request");rejects(()->noLoad.loaded(1,0),"load requires pending fade");rejects(()->noLoad.start(-1,0),"negative scene");rejects(()->noLoad.start(4,0),"oversized scene");
        CarpSequence choices=pending(0,0);rejects(()->choices.nextScene(-1),"negative choice");rejects(()->choices.nextScene(3),"oversized choice");
        noLoad.start(0,0);for(double invalid:new double[]{Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY,-1}){noLoad.progress(5,invalid);yes(noLoad.phase()==CarpSequence.Phase.PLAYING,"malformed renderer progress cannot trigger transition");}
        double[] mutable=CarpSequence.defaultThresholds();CarpSequence frozen=new CarpSequence(mutable,500,100,300);mutable[0]=.1;near(689d/719,frozen.threshold(0),0,"constructor defensively copies threshold array");near(689d/719,new CarpSequence().threshold(0),0,"default thresholds cannot be externally changed");
        rejects(()->new CarpSequence(null,500,100,300),"missing thresholds");rejects(()->new CarpSequence(new double[]{.5},500,100,300),"wrong threshold count");for(double invalid:new double[]{Double.NaN,Double.POSITIVE_INFINITY,-.1,1})rejects(()->new CarpSequence(new double[]{invalid,.5,.5,.5},500,100,300),"invalid threshold");
        rejects(()->new CarpSequence(nativeThresholds,-1,100,300),"negative fade-out");rejects(()->new CarpSequence(nativeThresholds,500,-1,300),"negative delay");rejects(()->new CarpSequence(nativeThresholds,500,100,-1),"negative fade-in");
        CarpSequence zero=new CarpSequence(nativeThresholds,0,0,0);zero.start(0,0);zero.progress(0,1);near(0,zero.alpha(0),0,"zero duration never divides by zero");yes(zero.needsNextScene(),"zero fade requires load acknowledgement");zero.loaded(1,0);near(1,zero.alpha(0),0,"zero duration load finishes immediately");
        CarpSequence preview=new CarpSequence(),cover=new CarpSequence();preview.start(0,0);cover.start(2,0);preview.progress(1,1);preview.alpha(501);preview.loaded(3,501);yes(cover.scene()==2&&!cover.transitioning(),"independent renderer state does not change global scene");near(1,cover.alpha(100000),0,"other renderer opacity remains unchanged");
        Random random=new Random(37);CarpSequence many=new CarpSequence();many.start(0,0);long time=0;int[] reached=new int[4];for(int n=0;n<100;n++){int old=many.scene();many.progress(time+1,1);near(0,many.alpha(time+501),0,"repeated scene fades to zero");int next=many.nextScene(random.nextInt(3));yes(next!=old,"repeated random choice never repeats current");many.loaded(next,time+501);near(1,many.alpha(time+901),0,"repeated transition completes");reached[next]++;time+=1000;}for(int count:reached)yes(count>0,"bounded seeded choices reach every scene");
        System.out.println("CarpSequence: "+assertions+" assertions passed");
    }
}
