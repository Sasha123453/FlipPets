package org.flippets.app;

import android.content.Context;
import org.json.*;

/** Offline sampled asset bounds; stable across scenes, no decoder/frame scan at runtime. */
public final class PetEnvelopes {
    private static JSONObject catalog;
    private static JSONObject videos;
    private static final float[] FULL={0,0,1,1};
    private PetEnvelopes(){}
    public static boolean opaqueScenery(String id){return id.startsWith("sheep-")||id.startsWith("seal-");}
    public static synchronized float[] get(Context context,String id,String path){
        // NFC/payment effects are separate full-canvas artwork, not the pet's body.
        if(path.contains("nfc_")||path.contains("pin_show")||id.equals("system-effects"))return FULL;
        load(context);
        JSONArray bounds=catalog.optJSONArray(id);if(bounds==null||bounds.length()!=4)return FULL;
        return new float[]{(float)bounds.optDouble(0,0),(float)bounds.optDouble(1,0),(float)bounds.optDouble(2,1),(float)bounds.optDouble(3,1)};
    }
    private static void load(Context context){if(catalog==null)try(java.io.InputStream in=context.getAssets().open("pet-envelopes.json")){
        java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();byte[] data=new byte[4096];int n;while((n=in.read(data))!=-1)out.write(data,0,n);JSONObject root=new JSONObject(out.toString("UTF-8"));catalog=root.getJSONObject("pets");videos=root.optJSONObject("videos");
    }catch(Exception e){catalog=new JSONObject();AppLog.event(context,"ENVELOPE_FALLBACK",e.getClass().getSimpleName());}}
    public static synchronized int[] videoSize(Context context,String path){load(context);JSONArray size=videos==null?null:videos.optJSONArray(path);return size==null?new int[]{0,0}:new int[]{size.optInt(0),size.optInt(1)};}
}
