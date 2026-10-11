package org.flippets.app;

import android.app.AlertDialog;
import android.content.*;
import android.content.pm.PackageManager;
import android.os.*;
import rikka.shizuku.Shizuku;

/** Native saved pets are separate from the app catalogue and opened only by explicit user action. */
final class NativePetManager {
    static void show(MainActivity a){
        new AlertDialog.Builder(a).setTitle("Питомцы · штатная блокировка")
            .setMessage("Это набор Xiaomi на сложенном заблокированном экране. Выбор питомца в галерее Flip Pets меняет только раскрытый режим.\n\nXiaomi хранит до 3 питомцев и 9 оформлений. В штатном экране можно выбирать и удалять сохранённые оформления; удаление может сбросить их настройки. Встроенные питомцы остаются в каталоге.\n\nЗамена Charlie из приложения пока недоступна. Автоматическое восстановление прежнего оформления не проверено.")
            .setPositiveButton("Проверить набор",(d,w)->operation(a,1))
            .setNeutralButton("Управление Xiaomi",(d,w)->new AlertDialog.Builder(a).setTitle("Штатные оформления")
                .setItems(new String[]{"Сохранённые оформления","Встроенный каталог Xiaomi"},(dialog,index)->operation(a,index+2)).setNegativeButton("Отмена",null).show())
            .setNegativeButton("Закрыть",null).show();
    }
    static boolean busy;
    static void operation(MainActivity a,int code){
        if(a.isFinishing()||a.isDestroyed())return;
        try{
            if(busy){a.message("Проверка уже выполняется.");return;}
            if(!Shizuku.pingBinder()){ShizukuBridge.guide(a);return;}
            if(Shizuku.getUid()!=2000){a.message("Для этого экрана запусти Shizuku через ADB / беспроводную отладку.");return;}
            if(Shizuku.checkSelfPermission()!=PackageManager.PERMISSION_GRANTED){
                Shizuku.OnRequestPermissionResultListener listener=new Shizuku.OnRequestPermissionResultListener(){public void onRequestPermissionResult(int request,int result){if(request!=42)return;Shizuku.removeRequestPermissionResultListener(this);if(result==PackageManager.PERMISSION_GRANTED)operation(a,code);}};
                Shizuku.addRequestPermissionResultListener(listener);Shizuku.requestPermission(42);return;
            }
            Request request=new Request(a,code);busy=true;request.handler.postDelayed(request.timeout,40000);Shizuku.bindUserService(request.args,request);
        }catch(Exception e){busy=false;a.message("Не удалось связаться с Shizuku.");}
    }
    static final class Request implements ServiceConnection {
        final MainActivity a;final int code;boolean done;final Handler handler=new Handler(Looper.getMainLooper());final Shizuku.UserServiceArgs args;
        final Runnable timeout=()->finish("Штатный экран не ответил. Попробуй ещё раз.");
        Request(MainActivity activity,int op){a=activity;code=op;args=new Shizuku.UserServiceArgs(new ComponentName(a,NativePetService.class)).daemon(true).processNameSuffix("nativepets").version(1);}
        public void onServiceConnected(ComponentName name,IBinder service){if(done)return;new Thread(()->{
            Parcel in=Parcel.obtain(),out=Parcel.obtain();String result;
            try{in.writeInterfaceToken(NativePetService.DESCRIPTOR);if(!service.transact(code,in,out,0))throw new IllegalStateException();out.readException();result=out.readString();}
            catch(Exception e){result="Штатный экран недоступен или прошивка отличается от проверенной. Ничего не применено.";}
            finally{in.recycle();out.recycle();}String value=result;handler.post(()->finish(value));
        },"native-pets-operation").start();}
        public void onServiceDisconnected(ComponentName name){finish("Соединение с Shizuku закрыто.");}
        void finish(String result){if(done)return;done=true;busy=false;handler.removeCallbacks(timeout);try{Shizuku.unbindUserService(args,this,true);}catch(Exception ignored){}if(!a.isFinishing()&&!a.isDestroyed())a.message(result);}
    }
}
