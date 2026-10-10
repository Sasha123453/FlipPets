import android.graphics.*;
import android.media.MediaMetadataRetriever;
import android.media.MediaDataSource;
import org.json.*;
import java.io.*;
import java.util.Arrays;

/** Raw donor video frames through Android's real retriever; never phone UI. */
public final class MediaSourceProbe {
    public static void main(String[] args)throws Exception {
        if(!android.os.Build.HARDWARE.contains("ranchu"))throw new SecurityException("Emulator required");
        MediaMetadataRetriever media=new MediaMetadataRetriever();JSONArray frames=new JSONArray();
        // app_process has no Application context for Android16's fd conversion.
        // A real read-only MediaDataSource avoids that harness-only conversion.
        final RandomAccessFile source=new RandomAccessFile(args[0],"r");
        MediaDataSource data=new MediaDataSource(){public synchronized int readAt(long at,byte[] buffer,int offset,int size)throws IOException{if(at<0||at>=source.length())return -1;source.seek(at);return source.read(buffer,offset,size);}public long getSize()throws IOException{return source.length();}public void close()throws IOException{source.close();}};
        try{media.setDataSource(data);
            int sourceW=Integer.parseInt(media.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH));int sourceH=Integer.parseInt(media.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT));
            int scaledW=Math.max(1,Math.round(sourceW*Math.min(1,512f/Math.max(sourceW,sourceH)))),scaledH=Math.max(1,Math.round(sourceH*Math.min(1,512f/Math.max(sourceW,sourceH))));
            for(long time:new long[]{500000,1500000}){
                Bitmap b=media.getScaledFrameAtTime(time,MediaMetadataRetriever.OPTION_CLOSEST,scaledW,scaledH);if(b==null)throw new IllegalStateException("No video frame");
                if(b.getConfig()==Bitmap.Config.HARDWARE){Bitmap copy=b.copy(Bitmap.Config.ARGB_8888,false);b.recycle();b=copy;}
                int[] pixels=new int[b.getWidth()*b.getHeight()];b.getPixels(pixels,0,b.getWidth(),0,0,b.getWidth(),b.getHeight());
                try(FileOutputStream out=new FileOutputStream("/data/local/tmp/flip-vortex-"+time+".png")){b.compress(Bitmap.CompressFormat.PNG,100,out);}
                frames.put(new JSONObject().put("timeUs",time).put("width",b.getWidth()).put("height",b.getHeight()).put("pixelHash",Arrays.hashCode(pixels)));b.recycle();
            }
            System.out.println(new JSONObject().put("sourceWidth",sourceW).put("sourceHeight",sourceH).put("durationMs",media.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)).put("frames",frames).toString(2));
        }finally{media.release();data.close();}
        System.exit(0);
    }
}
