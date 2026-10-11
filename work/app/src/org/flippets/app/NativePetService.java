package org.flippets.app;

import android.content.Context;
import android.os.*;
import java.io.*;
import java.security.MessageDigest;
import java.util.concurrent.TimeUnit;

/** Three fixed shell-UID operations. No settings writes, deletes, resource import or arbitrary commands. */
public final class NativePetService extends Binder {
    static final String DESCRIPTOR="org.flippets.app.NativePets";
    final Context context;final int ownerUid;
    public NativePetService(Context c){context=c;ownerUid=c.getApplicationInfo().uid;attachInterface(null,DESCRIPTOR);}
    void profile()throws Exception {
        if(!"ruyi".equals(Build.DEVICE)||!NativeCoverRoute.EEA_BUILD.equals(Build.VERSION.INCREMENTAL)||!"0".equals(command(128,"/system/bin/am","get-current-user").trim()))throw new IOException("Unsupported native profile");
        String[] packages={"com.miui.aod","com.android.systemui"};String[] hashes={"31c6dd09226e24f13f519822425a0b3f2a6d4fb8d6bf565bbd3a0568ee494d5d","bbb73370372d95707caa07bc00a6b2674afc5f433e5b074c4f8d6837b74ba757"};
        for(int i=0;i<packages.length;i++){
            android.content.pm.ApplicationInfo info=context.getPackageManager().getApplicationInfo(packages[i],0);
            MessageDigest digest=MessageDigest.getInstance("SHA-256");long size=0;
            try(InputStream in=new FileInputStream(info.sourceDir)){byte[] bytes=new byte[65536];int n;while((n=in.read(bytes))!=-1){size+=n;if(size>1024L*1024*1024)throw new IOException("Native APK size");digest.update(bytes,0,n);}}
            if(!Qa.hex(digest.digest()).equals(hashes[i]))throw new IOException("Native APK profile changed");
        }
    }
    static String command(int bound,String... args)throws Exception {
        java.lang.Process job=new ProcessBuilder(args).redirectErrorStream(true).start();ByteArrayOutputStream bytes=new ByteArrayOutputStream();boolean[] overflow={false};
        Thread reader=new Thread(()->{try(InputStream in=job.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(bytes.size()+n>bound){overflow[0]=true;job.destroyForcibly();break;}bytes.write(b,0,n);}}catch(Exception e){overflow[0]=true;}},"native-pets-read");reader.start();
        if(!job.waitFor(10,TimeUnit.SECONDS)){job.destroyForcibly();throw new IOException("Native operation timeout");}reader.join(1000);
        if(reader.isAlive()||overflow[0]||job.exitValue()!=0)throw new IOException("Native operation failed");return bytes.toString("UTF-8");
    }
    String read(String key)throws Exception{return command(NativePetState.MAX_JSON,"/system/bin/settings","--user","0","get","secure",key);}
    protected boolean onTransact(int code,Parcel in,Parcel out,int flags)throws RemoteException {
        if(code==INTERFACE_TRANSACTION){out.writeString(DESCRIPTOR);return true;}
        if(code==16777115){if(Binder.getCallingUid()!=ownerUid&&Binder.getCallingUid()!=2000)throw new SecurityException("Service owner required");System.exit(0);return true;}
        in.enforceInterface(DESCRIPTOR);if(Binder.getCallingUid()!=ownerUid||android.os.Process.myUid()!=2000)throw new SecurityException("Owning app and shell UID required");
        if(code<1||code>3)return false;
        try{
            profile();String result;
            if(code==1){String current=read("current_tiny_keyguard_info"),all=read("all_tiny_keyguard_info");if(!current.equals(read("current_tiny_keyguard_info"))||!all.equals(read("all_tiny_keyguard_info")))throw new IOException("Native selection changed");result=NativePetState.summarize(current,all);}
            else {String activity=code==2?"history.HistoryActivity":"HomepageActivity";
                String reply=command(8192,"/system/bin/am","start","-W","-n","com.miui.aod/com.miui.tinykeyguard.editor."+activity);
                if(!reply.contains("Status: ok")||reply.contains("Error:")||reply.contains("Exception"))throw new IOException("OEM screen unavailable");result="Открыт штатный экран Xiaomi.";}
            out.writeNoException();out.writeString(result);
        }catch(Exception e){out.writeException(new IllegalStateException("Штатный экран недоступен или его версия отличается от проверенной. Ничего не применено."));}
        return true;
    }
}
