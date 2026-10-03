package org.flippets.app;

import android.content.Context;
import android.os.*;
import java.io.*;
import java.util.concurrent.TimeUnit;

/** Shizuku UserService: fixed operations at shell UID; no arbitrary command API. */
public final class ControllerService extends Binder {
    static final String DESCRIPTOR="org.flippets.app.Controller";
    final Context context;final int ownerUid;
    public ControllerService(Context c){context=c;ownerUid=c.getApplicationInfo().uid;attachInterface(null,DESCRIPTOR);}
    protected boolean onTransact(int code,Parcel in,Parcel out,int flags)throws RemoteException{
        if(code==INTERFACE_TRANSACTION){out.writeString(DESCRIPTOR);return true;}
        if(code==16777115){if(Binder.getCallingUid()!=ownerUid&&Binder.getCallingUid()!=2000)throw new SecurityException("Not this service owner");System.exit(0);return true;}
        in.enforceInterface(DESCRIPTOR);if(Binder.getCallingUid()!=ownerUid)throw new SecurityException("Only the owning app may control this service");
        if(android.os.Process.myUid()!=2000)throw new SecurityException("This edition uses ADB shell UID only");
        String action=code==1?"supervise":code==2?"disable":code==3?"status":null;if(action==null)return false;
        try{
            File script=new File("/data/local/tmp/flip-pets-control.sh");android.util.AtomicFile file=new android.util.AtomicFile(script);FileOutputStream stream=null;
            try{stream=file.startWrite();try(InputStream asset=context.getAssets().open("controller.sh")){byte[] bytes=new byte[8192];int n;while((n=asset.read(bytes))!=-1)stream.write(bytes,0,n);}file.finishWrite(stream);}catch(Exception e){if(stream!=null)file.failWrite(stream);throw e;}
            // Output drains on a separate thread so a full pipe cannot deadlock the timeout.
            java.lang.Process job=new ProcessBuilder("/system/bin/sh",script.getPath(),action).redirectErrorStream(true).start();ByteArrayOutputStream text=new ByteArrayOutputStream();Thread reader=new Thread(()->{try(InputStream input=job.getInputStream()){byte[] b=new byte[4096];int n;while((n=input.read(b))!=-1){if(text.size()<65536)text.write(b,0,Math.min(n,65536-text.size()));}}catch(Exception ignored){}},"controller-output");reader.start();
            if(!job.waitFor(15,TimeUnit.SECONDS)){job.destroyForcibly();throw new IOException("Controller did not respond within 15 seconds");}reader.join(1000);
            String result="UID="+android.os.Process.myUid()+"\n"+text.toString("UTF-8");out.writeNoException();out.writeInt(job.exitValue());out.writeString(result);return true;
        }catch(Exception e){out.writeException(new IllegalStateException(e.toString()));return true;}
    }
}
