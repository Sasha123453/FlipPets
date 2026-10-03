package org.flippets.app;

import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.graphics.*;
import android.media.MediaPlayer;
import android.view.*;

public final class PetVideo extends TextureView implements TextureView.SurfaceTextureListener {
    MediaPlayer player;Surface surface;String wanted="";boolean active,prepared;int videoW,videoH;
    public PetVideo(Context context){super(context);setOpaque(false);setSurfaceTextureListener(this);}
    public void load(String path){wanted=path;releasePlayer();if(surface==null||path.isEmpty())return;
        final MediaPlayer p=new MediaPlayer();player=p;
        try(AssetFileDescriptor fd=getContext().getAssets().openFd(path)){
            p.setDataSource(fd.getFileDescriptor(),fd.getStartOffset(),fd.getLength());p.setSurface(surface);p.setVolume(0,0);p.setLooping(true);
            p.setOnPreparedListener(m->{if(player!=m)return;prepared=true;videoW=m.getVideoWidth();videoH=m.getVideoHeight();fit();if(active)m.start();});
            p.setOnErrorListener((m,what,extra)->{AppLog.event(getContext(),"VIDEO_ERROR",what+"/"+extra+" "+path);return true;});p.prepareAsync();
        }catch(Exception e){AppLog.error(getContext(),"VIDEO_LOAD_ERROR "+path,e);releasePlayer();}
    }
    public void start(){active=true;if(prepared&&player!=null)player.start();}
    public void pause(){active=false;if(prepared&&player!=null&&player.isPlaying())player.pause();}
    void fit(){if(videoW<=0||videoH<=0||getWidth()==0||getHeight()==0)return;float scale=Math.min(getWidth()/(float)videoW,getHeight()/(float)videoH);Matrix matrix=new Matrix();matrix.setScale(videoW*scale/getWidth(),videoH*scale/getHeight(),getWidth()/2f,getHeight()/2f);setTransform(matrix);}
    void releasePlayer(){prepared=false;if(player!=null){player.release();player=null;}}
    public void destroy(){pause();releasePlayer();if(surface!=null){surface.release();surface=null;}}
    public void onSurfaceTextureAvailable(SurfaceTexture texture,int w,int h){surface=new Surface(texture);if(!wanted.isEmpty())load(wanted);}
    public void onSurfaceTextureSizeChanged(SurfaceTexture texture,int w,int h){fit();}
    public boolean onSurfaceTextureDestroyed(SurfaceTexture texture){releasePlayer();if(surface!=null){surface.release();surface=null;}return true;}
    public void onSurfaceTextureUpdated(SurfaceTexture texture){}
}
