package org.flippets.app;

import android.content.Context;
import android.os.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.TimeUnit;

/** Private, bounded event journal. No frame logging, wakelock or background sampler. */
public final class AppLog {
    static final int LIMIT=65536;
    static final Map<String,Long> recent=new HashMap<>();
    static File file(Context c,String name){File d=new File(c.getFilesDir(),"diagnostics");d.mkdirs();return new File(d,name);}
    public static synchronized void event(Context c,String kind,String detail){
        try{
            if(detail==null)detail="";if(detail.length()>2048)detail=detail.substring(0,2048)+"…";
            String key=kind+"|"+detail;long now=SystemClock.elapsedRealtime();Long old=recent.get(key);if(old!=null&&now-old<60000)return;
            if(recent.size()>=32)recent.clear();recent.put(key,now);
            String line=String.format(Locale.ROOT,"%tFT%<tT uptime=%d pid=%d %s %s%n",new Date(),now,android.os.Process.myPid(),kind,detail);
            byte[] bytes=line.getBytes(StandardCharsets.UTF_8);File current=file(c,"recent.log"),previous=file(c,"previous.log");
            if(current.length()+bytes.length>LIMIT){if(previous.exists())previous.delete();if(!current.renameTo(previous))current.delete();}
            try(FileOutputStream out=new FileOutputStream(current,true)){out.write(bytes);}
            android.util.Log.i("FlipPets",kind+" "+detail);
        }catch(Exception ignored){}
    }
    public static void error(Context c,String kind,Throwable e){StringWriter s=new StringWriter();e.printStackTrace(new PrintWriter(s));event(c,kind,s.toString());}
    public static synchronized String saved(Context c){StringBuilder s=new StringBuilder();for(String name:new String[]{"previous.log","recent.log"}){s.append("\n--- ").append(name).append(" ---\n");File f=file(c,name);try(FileInputStream in=new FileInputStream(f)){byte[] b=new byte[LIMIT];int n=in.read(b);if(n>0)s.append(new String(b,0,n,StandardCharsets.UTF_8));}catch(Exception e){s.append("No saved entries.\n");}}return s.toString();}
    public static void storeStatus(Context c,String text){try{byte[] bytes=text.getBytes(StandardCharsets.UTF_8);android.util.AtomicFile f=new android.util.AtomicFile(file(c,"controller-status.txt"));FileOutputStream out=f.startWrite();try{out.write(bytes,0,Math.min(32768,bytes.length));f.finishWrite(out);}catch(Exception e){f.failWrite(out);}}catch(Exception ignored){}}
    public static String report(Context c){
        StringBuilder s=new StringBuilder("Flip Pets diagnostic report\n");
        try{s.append("App: ").append(c.getPackageManager().getPackageInfo(c.getPackageName(),0).versionName).append("\n");}catch(Exception ignored){}
        s.append("UID: ").append(android.os.Process.myUid()).append(" PID: ").append(android.os.Process.myPid()).append("\nBoot count: ").append(android.provider.Settings.Global.getInt(c.getContentResolver(),"boot_count",-1)).append('\n');
        s.append(Pets.displayReport(c)).append("\nSelected ID: ").append(Pets.current(c).optString("id")).append("\nFrame limit: ").append(FlipPetsApp.frameRate(c)).append("\nSoftware preference: ").append(c.getSharedPreferences(Pets.PREFS,0).getBoolean("softwareDecoder",false)).append("\n");
        try{s.append("Shizuku alive: ").append(rikka.shizuku.Shizuku.pingBinder());if(rikka.shizuku.Shizuku.pingBinder())s.append(" UID: ").append(rikka.shizuku.Shizuku.getUid());s.append('\n');}catch(Exception e){s.append(e).append('\n');}
        Debug.MemoryInfo memory=new Debug.MemoryInfo();Debug.getMemoryInfo(memory);s.append("App PSS KiB: ").append(memory.getTotalPss()).append("\nProcess CPU ms since start: ").append(android.os.Process.getElapsedCpuTime()).append('\n');
        try(FileInputStream in=new FileInputStream(file(c,"controller-status.txt"))){byte[] bytes=new byte[32768];int n=in.read(bytes);if(n>0)s.append("\n--- Latest shell controller/display status ---\n").append(new String(bytes,0,n,StandardCharsets.UTF_8));}catch(Exception ignored){}
        s.append(saved(c)).append("\n--- Android logcat: only this application's UID, bounded ---\n");
        try{
            java.lang.Process p=new ProcessBuilder("/system/bin/logcat","-d","--uid="+android.os.Process.myUid(),"-v","threadtime","-t","300").redirectErrorStream(true).start();
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();Thread reader=new Thread(()->{try(InputStream in=p.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1)if(bytes.size()<32768)bytes.write(b,0,Math.min(n,32768-bytes.size()));}catch(Exception ignored){}},"own-logcat");reader.start();
            if(!p.waitFor(3,TimeUnit.SECONDS))p.destroyForcibly();reader.join(1000);s.append(bytes.toString("UTF-8"));
        }catch(Exception e){s.append("Logcat unavailable: ").append(e).append('\n');}
        return s.toString();
    }
    public static void install(Context c){
        Thread.UncaughtExceptionHandler original=Thread.getDefaultUncaughtExceptionHandler();
        Thread.setDefaultUncaughtExceptionHandler((thread,e)->{error(c,"JAVA_CRASH "+thread.getName(),e);if(original!=null)original.uncaughtException(thread,e);else System.exit(1);});
    }
}
