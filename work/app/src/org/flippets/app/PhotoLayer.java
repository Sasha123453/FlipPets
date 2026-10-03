package org.flippets.app;
import android.content.*;
import android.graphics.*;
import android.view.View;

/** User image layers surrounding the original glitter PAG. */
public final class PhotoLayer extends View {
    final boolean foreground;String id="";long revision=-1;Bitmap image;
    public PhotoLayer(Context c,boolean front){super(c);foreground=front;setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);}
    protected void onDraw(Canvas c){String next=Pets.current(getContext()).optString("id");SharedPreferences p=SceneSettings.prefs(getContext(),next);long v=p.getLong("imageRevision",0);if(!next.equals(id)||v!=revision){release();id=next;revision=v;image=SceneSettings.image(getContext(),id,foreground);}if(image!=null){c.save();if(p.getBoolean("gravity",true))c.translate(Pets.tiltX*getWidth()*.012f,Pets.tiltY*getHeight()*.012f);CompositionRenderer.drawPhoto(c,image,getWidth(),getHeight(),p.getFloat("zoom",1),p.getFloat("panX",.5f),p.getFloat("panY",.5f));c.restore();}}
    void release(){if(image!=null)image.recycle();image=null;id="";revision=-1;}
}
