package org.flippets.app;

import android.content.Context;
import org.json.*;

/** The same source transform used by prepared native AI compositions and app previews. */
final class NativePetGeometry {
    private static JSONObject layouts;
    private NativePetGeometry(){}
    private static synchronized void load(Context context){
        if(layouts==null)try(java.io.InputStream in=context.getAssets().open("native-pet-layout.json")){
            java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();byte[] bytes=new byte[4096];int n;
            while((n=in.read(bytes))!=-1)out.write(bytes,0,n);
            JSONObject root=new JSONObject(out.toString("UTF-8"));
            if(root.getInt("schemaVersion")!=1||root.getJSONArray("canvas").getInt(0)!=1208||root.getJSONArray("canvas").getInt(1)!=1392)throw new JSONException("Native canvas");
            layouts=root.getJSONObject("layouts");
        }catch(Exception e){layouts=new JSONObject();AppLog.error(context,"NATIVE_GEOMETRY",e);}
    }
    static boolean shared(Context context,String id){load(context);return layouts.has(id);}
    static CoverGeometry.Placement placement(Context context,int width,int height,int sourceWidth,int sourceHeight,String id,PetLayoutProfile profile){
        load(context);JSONObject value=layouts.optJSONObject(id);if(value==null)return null;
        try{
            JSONArray source=value.getJSONArray("sourceCanvas");
            if(sourceWidth!=source.getInt(0)||sourceHeight!=source.getInt(1))return null;
            return CoverGeometry.calibrated(width,height,(float)value.getDouble("scale"),(float)value.getDouble("x"),(float)value.getDouble("y"),
                (float)value.getDouble("subjectRight"),(float)value.getDouble("subjectBottom"),profile);
        }catch(JSONException e){AppLog.error(context,"NATIVE_GEOMETRY",e);return null;}
    }
}
