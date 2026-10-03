import org.flippets.app.SceneGeometry;
public class SceneGeometryTest {
    public static void main(String[] args){int checks=0;int[][] screens={{1392,1208},{1208,1392},{1224,2912},{400,400}};
        for(int[] screen:screens)for(float margin:new float[]{.34f,.55f}){
            float w=screen[0],h=screen[1],safe=w*margin,s=SceneGeometry.scale((int)w,(int)h,safe),x=SceneGeometry.x((int)w,s),y=SceneGeometry.y((int)h,s);
            if(x+332*s<safe-.01||x+976*s>w+.01||y<-.01||y+596*s>h+.01)throw new AssertionError("Foreground escapes safe area "+w+"x"+h);
            if(s<=0||Float.isNaN(s))throw new AssertionError("Invalid uniform scale");checks++;
        }
        System.out.println("PASS "+checks+" aspect and camera-margin checks");
    }
}
