package org.flippets.app;

import android.app.Activity;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.*;
import rikka.shizuku.Shizuku;

/** Optional shell privilege bridge; the normal catalogue works without Shizuku. */
public final class ShizukuBridge {
    public static void guide(MainActivity a){new android.app.AlertDialog.Builder(a).setTitle("Shizuku · без root и без ПК").setMessage("1. Установи Shizuku из официального источника.\n2. Включи беспроводную отладку и выполни сопряжение по инструкции Shizuku.\n3. Запусти Shizuku и вернись в Flip Pets.\n4. Нажми «Включить через Shizuku» и разреши доступ.\n\nПосле перезагрузки Shizuku нужно запускать снова. Кабель и постоянный ПК не нужны. Для первого запуска может понадобиться Wi-Fi. Если HyperOS ограничит ADB, проверь отдельный пункт «Отладка по USB (настройки безопасности)».\n\nВ сложенном состоянии внешний экран и AOD остаются штатными. Режим проверен на MIX Flip с EEA HyperOS 3.0.303; другие прошивки могут отличаться.").setPositiveButton("Официальная инструкция",(d,w)->a.startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://shizuku.rikka.app/guide/setup/")))).setNeutralButton("Открыть Shizuku",(d,w)->{Intent i=a.getPackageManager().getLaunchIntentForPackage("moe.shizuku.privileged.api");if(i!=null)a.startActivity(i);else a.startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://shizuku.rikka.app/download/")));}).setNegativeButton("Готово",null).show();}
    public static void start(MainActivity a){try{java.io.File stop=new java.io.File(a.getExternalFilesDir(null),"controller-stop");if(stop.exists()&&!stop.delete())throw new java.io.IOException("Cannot clear stop request");}catch(Exception e){a.message(e.toString());return;}operation(a,1);}
    public static void stop(MainActivity a){if(pending!=null&&pending.code==1)pending.cancelled=true;CoverGuard.stop(a);try{Pets.write(a,"controller-stop","stop\n");PetActivity.closeCovers();}catch(Exception e){a.message(e.toString());return;}if(Shizuku.pingBinder())operation(a,2);else a.message("Запрос на остановку сохранён. Контроллер прочитает его, закроет свой экран и снимет режим. Если контроллер был завершён системой, доступен аварийный reset через ADB.");}
    public static void status(MainActivity a){operation(a,3);}
    public static void captureStatus(MainActivity a,Runnable next){try{if(pending==null&&Shizuku.pingBinder()&&Shizuku.getUid()==2000&&Shizuku.checkSelfPermission()==PackageManager.PERMISSION_GRANTED){ControlRequest r=new ControlRequest(a,3,next);pending=r;r.handler.postDelayed(r.timeout,25000);try{Shizuku.bindUserService(r.args,r);}catch(Exception e){r.finish(e.toString());}return;}}catch(Exception e){AppLog.error(a,"LOG_STATUS",e);}next.run();}
    static ControlRequest pending;
    static boolean waitingPermission;
    static int permissionCode;
    static void cancelPendingStart(){if(pending!=null&&pending.code==1)pending.cancelled=true;if(waitingPermission&&permissionCode==1)permissionCode=0;}
    static void operation(MainActivity a,int code){
        try{
            if(a.isFinishing()||a.isDestroyed())return;
            if(pending!=null){a.message("Команда уже выполняется. Подожди её завершения.");return;}
            if(!Shizuku.pingBinder()){guide(a);return;}
            if(Shizuku.getUid()!=2000){a.message("Запусти Shizuku через ADB / беспроводную отладку. Root-режим не используется.");return;}
            if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){
                permissionCode=code;if(waitingPermission)return;waitingPermission=true;
                Shizuku.OnRequestPermissionResultListener listener=new Shizuku.OnRequestPermissionResultListener(){public void onRequestPermissionResult(int request,int result){if(request!=41)return;Shizuku.removeRequestPermissionResultListener(this);waitingPermission=false;if(result==PackageManager.PERMISSION_GRANTED){if(permissionCode>0)operation(a,permissionCode);}else if(!a.isFinishing()&&!a.isDestroyed())a.message("Доступ не разрешён. Оформления и живые обои доступны без Shizuku.");}};
                Shizuku.addRequestPermissionResultListener(listener);Shizuku.requestPermission(41);return;
            }
            ControlRequest request=new ControlRequest(a,code);pending=request;request.handler.postDelayed(request.timeout,25000);
            try{Shizuku.bindUserService(request.args,request);}catch(Exception e){request.finish(e.toString());}
        }catch(Exception e){waitingPermission=false;a.message(e.toString());}
    }
    /** The privileged Java bridge exists only for one operation; nohup supervisor is independent. */
    static final class ControlRequest implements ServiceConnection {
        final MainActivity activity;final int code;final Runnable continuation;boolean done,cancelled;int controllerExit=-1;
        final Handler handler=new Handler(Looper.getMainLooper());
        final Shizuku.UserServiceArgs args;
        final Runnable timeout=()->finish("Shizuku не ответил за 25 секунд. Проверь его запуск и попробуй снова.");
        ControlRequest(MainActivity a,int c){this(a,c,null);}
        ControlRequest(MainActivity a,int c,Runnable next){activity=a;code=c;continuation=next;args=new Shizuku.UserServiceArgs(new ComponentName(a,ControllerService.class)).daemon(true).processNameSuffix("controller").version(11);}
        public void onServiceConnected(ComponentName name,IBinder binder){if(done)return;new Thread(()->{
            String message;Parcel in=Parcel.obtain(),out=Parcel.obtain();
            try{in.writeInterfaceToken(ControllerService.DESCRIPTOR);if(!binder.transact(code,in,out,0))throw new IllegalStateException("Unknown controller transaction");out.readException();int exit=out.readInt();controllerExit=exit;String detail=out.readString();AppLog.event(activity,"CONTROLLER_RAW op="+code,"exit="+exit+" "+detail);if(code==3)AppLog.storeStatus(activity,detail);
                message=exit==0?(code==1?"Контроллер включён. Он ждёт полностью раскрытый, разблокированный телефон. При складывании или сне вернётся штатный режим. ПК можно отключить.":code==2?"Контроллер выключен. Возвращён обычный режим Xiaomi.":"Состояние контроллера:")+(code==3?"\n\n"+detail:""):"Не удалось выполнить команду:\n"+detail;
            }catch(Exception e){message=e.toString();}finally{in.recycle();out.recycle();}
            final String result=message;handler.post(()->finish(result));
        },"shizuku-control").start();}
        public void onServiceDisconnected(ComponentName name){if(!done)finish("Соединение с Shizuku закрыто. Проверь его запуск.");}
        void finish(String message){if(done)return;done=true;handler.removeCallbacks(timeout);pending=null;AppLog.event(activity,"CONTROLLER op="+code,message);
            if(cancelled&&code==1){try{Pets.write(activity,"controller-stop","stop\n");}catch(Exception e){AppLog.error(activity,"GUARD_CANCEL_START",e);}CoverGuard.stop(activity);message="Запуск отменён. Контроллер получит запрос на остановку.";}
            else if(controllerExit==0){if(code==1)CoverGuard.activate(activity);else if(code==2)CoverGuard.stop(activity);}
            try{Shizuku.unbindUserService(args,this,true);}catch(Exception ignored){}
            if(continuation!=null)continuation.run();else if(!activity.isFinishing()&&!activity.isDestroyed())activity.message(message);
        }
    }
}
