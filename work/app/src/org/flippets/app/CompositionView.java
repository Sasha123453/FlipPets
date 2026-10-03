package org.flippets.app;

import android.content.Context;
import android.graphics.Canvas;
import android.os.SystemClock;
import android.view.*;

public final class CompositionView extends View {
    final CompositionRenderer renderer;
    public CompositionView(Context c){super(c);renderer=new CompositionRenderer(c);setContentDescription("Часы и композиция Xiaomi. Коснись для реакции.");}
    protected void onDraw(Canvas c){renderer.draw(c,getWidth(),getHeight(),Pets.current(getContext()),System.currentTimeMillis(),SystemClock.elapsedRealtime());}
    long nextDelay(){String type=Pets.current(getContext()).optString("renderer");if(type.equals("analog")||type.equals("dragon")||type.equals("steps"))return 1000/Math.min(15,FlipPetsApp.frameRate(getContext()));if(type.equals("stretch")&&SystemClock.elapsedRealtime()-renderer.touchTime<2200)return 1000/Math.min(20,FlipPetsApp.frameRate(getContext()));return 1000;}
    public boolean onTouchEvent(MotionEvent e){if(e.getAction()==MotionEvent.ACTION_DOWN||e.getAction()==MotionEvent.ACTION_MOVE){renderer.touch(e.getX()/Math.max(1,getWidth()),e.getY()/Math.max(1,getHeight()),SystemClock.elapsedRealtime());invalidate();}if(e.getAction()==MotionEvent.ACTION_UP)performClick();return true;}
    public boolean performClick(){super.performClick();return true;}
}
