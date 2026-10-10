package org.flippets.app;
import android.app.*;
import android.view.*;
import android.widget.*;
/** Preview has storage disabled; only Apply selects the live card. */
final class MiniAppsDialog {
    static AlertDialog show(MainActivity a){return show(a,MiniAppStore.selected(a));}
    static AlertDialog show(MainActivity a,String initial){boolean resume=a.preview.running;a.preview.stop();UiTheme ui=new UiTheme(a);String[] draft={initial};if(!MiniAppStore.valid(draft[0]))draft[0]="focus";ScrollView scroll=new ScrollView(a);LinearLayout body=new LinearLayout(a);body.setOrientation(1);body.setPadding(ui.dp(16),ui.dp(8),ui.dp(16),ui.dp(20));scroll.addView(body);body.setBackgroundColor(ui.background);
        body.addView(ui.label("Оригинальные демонстрационные карточки из публичного каталога Xiaomi. Графика и китайский интерфейс сохранены. Работают офлайн.",14,true));MiniAppView preview=new MiniAppView(a,false,id->{});preview.show(draft[0]);LinearLayout.LayoutParams pp=new LinearLayout.LayoutParams(-1,-2);pp.topMargin=ui.dp(12);body.addView(preview,pp);preview.start();
        LinearLayout choices=new LinearLayout(a);String[] ids={"focus","water","words"},names={"Фокус","Вода","Слова"};Button[] buttons=new Button[3];for(int i=0;i<ids.length;i++){final int n=i;buttons[i]=ui.button(names[i],false,v->{draft[0]=ids[n];preview.show(draft[0]);for(int j=0;j<3;j++)ui.chip(buttons[j],ids[j].equals(draft[0]));});ui.chip(buttons[i],ids[i].equals(draft[0]));LinearLayout.LayoutParams bp=new LinearLayout.LayoutParams(0,-2,1);if(i>0)bp.leftMargin=ui.dp(4);choices.addView(buttons[i],bp);}body.addView(choices,ui.spaced());
        body.addView(ui.label("Вода:8 стаканов. Слова: оригинальный английско-китайский словарь. Pomodoro:25мин фокуса /5мин отдыха. Состояние сохраняется только у применённой карточки. При складывании, блокировке и сне возвращается штатный экран Xiaomi.",12,true),ui.spaced());AlertDialog dialog=new AlertDialog.Builder(a).setTitle("Карточки Xiaomi").setView(scroll).setPositiveButton("На внешний экран",(d,w)->{MiniAppStore.select(a,draft[0]);a.preview.reload();a.refreshSelection();}).setNegativeButton("Отмена",null).setNeutralButton("Вернуть питомца",(d,w)->{MiniAppStore.select(a,"none");a.preview.reload();a.refreshSelection();}).create();dialog.setOnDismissListener(d->{preview.stop();if(resume&&a.mainStarted&&!a.isFinishing())a.preview.start();});dialog.show();return dialog;
    }
}
