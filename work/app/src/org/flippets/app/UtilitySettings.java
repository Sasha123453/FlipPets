package org.flippets.app;

import android.app.Activity;
import android.content.SharedPreferences;
import android.widget.LinearLayout;

/** Public entry point for the main settings panel; scene catalogue stays unchanged. */
public final class UtilitySettings {
    private UtilitySettings(){}
    private static void selectTimer(Activity a,PetStage preview,String mode){TimerState s=UtilityTimerStore.read(a);s.select(mode,android.os.SystemClock.elapsedRealtime());UtilityTimerStore.save(a,s);a.getSharedPreferences(Pets.PREFS,0).edit().putString("utilityCard","timer").apply();Pets.signal(a);preview.reload();}
    public static void populate(Activity a,LinearLayout panel,PetStage preview){
        SharedPreferences p=a.getSharedPreferences(Pets.PREFS,0);
        SceneControls.note(a,panel,"Одна дополнительная карточка поверх питомца или фотографии. По умолчанию выключена.");
        SceneControls.choose(a,panel,"Карточка на экране","utilityCard",new String[]{"Выключена","Батарея и заряд","Музыка","Визуальный таймер"},new String[]{"none","battery","media","timer"},p,preview);
        SceneControls.button(a,panel,"Режим: секундомер",()->selectTimer(a,preview,"stopwatch"));
        SceneControls.button(a,panel,"Режим: фокус 25 минут",()->selectTimer(a,preview,"focus"));
        SceneControls.note(a,panel,"Музыка использует разрешённый доступ к уведомлениям и кнопки, которые поддерживает плеер. Таймер — визуальный: без звука и фонового будильника; после перезагрузки приостанавливается на последнем сохранённом времени.");
    }
}
