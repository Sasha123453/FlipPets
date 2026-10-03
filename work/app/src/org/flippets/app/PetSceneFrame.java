package org.flippets.app;

import android.content.Context;
import android.graphics.*;
import android.view.View;
import android.widget.FrameLayout;

/** Hardware scene-edge blending. No CPU snapshots, bitmap filters or background frame loop. */
final class PetSceneFrame extends FrameLayout {
    final View content;final Paint mask=new Paint(Paint.ANTI_ALIAS_FLAG);float top=-1;boolean logged;
    PetSceneFrame(Context context,View content){super(context);this.content=content;addView(content,new LayoutParams(-1,-1));mask.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_IN));}
    void topFeather(float y){float next=y<0?-1:Math.max(0,y);if(top==next)return;top=next;logged=false;if(top>=0)mask.setShader(new LinearGradient(0,top,0,top+48,new int[]{0x00000000,0xff000000},null,Shader.TileMode.CLAMP));else mask.setShader(null);invalidate();}
    protected void dispatchDraw(Canvas canvas){if(top<0||content.getVisibility()!=VISIBLE){super.dispatchDraw(canvas);return;}if(!logged){logged=true;AppLog.event(getContext(),"SCENE_FEATHER","hardware="+canvas.isHardwareAccelerated()+" top="+top+" length=48");}int save=canvas.saveLayer(0,0,getWidth(),getHeight(),null);super.dispatchDraw(canvas);canvas.drawRect(0,0,getWidth(),getHeight(),mask);canvas.restoreToCount(save);}
}
