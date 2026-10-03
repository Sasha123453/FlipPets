import org.flippets.app.HingeOpacity;
public class HingeOpacityTest {
    static void check(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] args){
        check(HingeOpacity.degrees(0)==0);check(HingeOpacity.degrees(180)==1);
        float previous=0;for(int angle=0;angle<=180;angle++){float a=HingeOpacity.degrees(angle);check(a>=0&&a<=1&&a>=previous);previous=a;}
        check(Math.abs(HingeOpacity.degrees(90)-.5f)<.0001f);
        check(HingeOpacity.degrees(Float.NaN)==1);check(HingeOpacity.degrees(Float.POSITIVE_INFINITY)==1);
        check(HingeOpacity.status(0)==0&&HingeOpacity.status(1)<HingeOpacity.status(2)&&HingeOpacity.status(3)==1);
        System.out.println("Hinge opacity: endpoints, monotonic range, midpoint and invalid-sample fallback passed");
    }
}
