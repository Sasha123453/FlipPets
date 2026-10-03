package org.flippets.app;

import android.app.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.text.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.util.*;

/** A searchable visual catalogue; IDs keep favorites stable across app updates. */
public final class GalleryDialog extends Dialog {
    final MainActivity owner;final UiTheme ui;final ArrayList<Integer> rows=new ArrayList<>();
    final Map<String,Bitmap> thumbs=new HashMap<>();final Adapter adapter=new Adapter();
    final TextView count;final LinearLayout tabs;String category="Все",query="";
    int dp(float value){return Math.round(value*owner.getResources().getDisplayMetrics().density);}
    TextView label(String value,int size){return ui.label(value,size,false);}
    public GalleryDialog(MainActivity a){
        super(a,(a.getResources().getConfiguration().uiMode&android.content.res.Configuration.UI_MODE_NIGHT_MASK)==android.content.res.Configuration.UI_MODE_NIGHT_YES?android.R.style.Theme_Material_NoActionBar:android.R.style.Theme_Material_Light_NoActionBar);owner=a;ui=new UiTheme(a);
        LinearLayout root=new LinearLayout(a);root.setOrientation(1);root.setPadding(dp(20),dp(16),dp(20),dp(12));root.setBackgroundColor(ui.background);setContentView(root);
        root.setOnApplyWindowInsetsListener((v,i)->{android.graphics.Insets bars=android.os.Build.VERSION.SDK_INT>=30?i.getInsets(android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.displayCutout()|android.view.WindowInsets.Type.ime()):android.graphics.Insets.of(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());v.setPadding(dp(20)+bars.left,dp(16)+bars.top,dp(20)+bars.right,dp(12)+bars.bottom);return i;});
        LinearLayout top=new LinearLayout(a);top.setGravity(Gravity.CENTER_VERTICAL);TextView title=label("Оформление",25);title.setTypeface(Typeface.create("sans-serif-medium",0));top.addView(title,new LinearLayout.LayoutParams(0,-2,1));Button close=ui.button("Готово",false,v->dismiss());top.addView(close);root.addView(top);
        EditText search=new EditText(a);search.setSingleLine(true);search.setHint("Найти оформление");search.setContentDescription("Поиск по названию оформления");search.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);ui.field(search);LinearLayout.LayoutParams searchParams=ui.spaced();searchParams.topMargin=dp(16);root.addView(search,searchParams);search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int start,int count,int after){}public void onTextChanged(CharSequence s,int start,int before,int count){query=s.toString();filter();}public void afterTextChanged(Editable e){}});
        HorizontalScrollView scroll=new HorizontalScrollView(a);scroll.setHorizontalScrollBarEnabled(false);tabs=new LinearLayout(a);scroll.addView(tabs);root.addView(scroll,ui.spaced());
        for(String name:new String[]{"Все","Избранное","Питомцы","Часы и виджеты","Фото и текст","Видео","Эффекты"}){Button b=ui.button(name,false,v->{category=name;filter();refreshTabs();});ui.chip(b,name.equals(category));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-2,-2);p.rightMargin=dp(8);tabs.addView(b,p);}
        count=ui.label("",13,true);count.setPadding(0,dp(12),0,dp(12));count.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);root.addView(count);
        GridView grid=new GridView(a){protected void onSizeChanged(int w,int h,int oldw,int oldh){super.onSizeChanged(w,h,oldw,oldh);float scale=a.getResources().getConfiguration().fontScale;setNumColumns(Math.max(1,Math.min(3,w/(dp(148*Math.max(1,scale))+dp(12)))));}};
        grid.setNumColumns(2);grid.setHorizontalSpacing(dp(12));grid.setVerticalSpacing(dp(12));grid.setClipToPadding(false);grid.setPadding(0,0,0,dp(12));grid.setAdapter(adapter);root.addView(grid,new LinearLayout.LayoutParams(-1,0,1));
        root.setFocusableInTouchMode(true);root.requestFocus();filter();setOnDismissListener(v->{for(Bitmap image:thumbs.values())if(image!=null)image.recycle();thumbs.clear();if(!owner.isFinishing()&&!owner.isDestroyed())owner.preview.start();});
    }
    void refreshTabs(){for(int i=0;i<tabs.getChildCount();i++){Button b=(Button)tabs.getChildAt(i);ui.chip(b,b.getText().toString().equals(category));}}
    public void show(){owner.preview.stop();super.show();getWindow().setLayout(-1,-1);ui.window(getWindow());getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE|WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);}
    static String group(JSONObject pet){String type=pet.optString("renderer"),kind=pet.optString("kind"),name=pet.optString("name");if(kind.equals("composition"))return type.equals("analog")||type.equals("dragon")||type.equals("stretch")||type.equals("steps")?"Часы и виджеты":"Фото и текст";if(kind.equals("video"))return "Видео";if(name.equals("Flowing glitter")||name.equals("Системные эффекты")||name.equals("Butterfly carp"))return "Эффекты";return "Питомцы";}
    Set<String> favorites(){return new HashSet<>(owner.getSharedPreferences(Pets.PREFS,0).getStringSet("favorites",Collections.emptySet()));}
    void filter(){rows.clear();Set<String> stars=favorites();JSONArray cat=Pets.catalog(owner);for(int i=0;i<cat.length();i++){JSONObject p=cat.optJSONObject(i);if(!p.optString("name").toLowerCase(Locale.ROOT).contains(query.trim().toLowerCase(Locale.ROOT)))continue;if(category.equals("Избранное")&&!stars.contains(p.optString("id")))continue;if(!category.equals("Все")&&!category.equals("Избранное")&&!category.equals(group(p)))continue;rows.add(i);}count.setText(rows.size()==0?(query.trim().isEmpty()?"Здесь пока пусто. Добавь оформление кнопкой ☆.":"Ничего не найдено. Попробуй другое название."):"Найдено: "+rows.size()+" · "+category);adapter.notifyDataSetChanged();}
    Bitmap thumb(String id){if(!thumbs.containsKey(id)){Bitmap b=null;try(java.io.InputStream s=owner.getAssets().open("thumbs/"+id+".webp")){b=BitmapFactory.decodeStream(s);}catch(Exception ignored){}thumbs.put(id,b);}return thumbs.get(id);}
    class Adapter extends BaseAdapter {
        public int getCount(){return rows.size();}public Object getItem(int position){return rows.get(position);}public long getItemId(int position){return rows.get(position);}
        public View getView(int position,View convert,ViewGroup parent){int index=rows.get(position);JSONObject pet=Pets.catalog(owner).optJSONObject(index);String id=pet.optString("id");boolean selected=Pets.current(owner).optString("id").equals(id);LinearLayout card=new LinearLayout(owner);card.setOrientation(1);card.setPadding(dp(12),dp(12),dp(12),dp(8));GradientDrawable bg=ui.shape(ui.surface,24);if(selected)bg.setStroke(dp(2),ui.primary);card.setBackground(bg);card.setClipToOutline(true);
            ImageView image=new ImageView(owner);image.setImageBitmap(thumb(id));image.setScaleType(ImageView.ScaleType.FIT_CENTER);image.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO);ui.card(image,ui.container,18);card.addView(image,new LinearLayout.LayoutParams(-1,dp(145)));
            TextView name=label(pet.optString("name"),16);name.setTypeface(Typeface.create("sans-serif-medium",0));name.setPadding(0,dp(12),0,dp(4));name.setMaxLines(2);name.setEllipsize(TextUtils.TruncateAt.END);name.setMinHeight(dp(54));card.addView(name);
            LinearLayout foot=new LinearLayout(owner);foot.setGravity(Gravity.CENTER_VERTICAL);TextView kind=ui.label(selected?"Выбрано":group(pet),12,true);if(selected)kind.setTextColor(ui.primary);foot.addView(kind,new LinearLayout.LayoutParams(0,-2,1));Button star=ui.button("",false,null);boolean favorite=favorites().contains(id);star.setText(favorite?"★":"☆");star.setTextSize(24);star.setPadding(0,0,0,0);star.setMinHeight(dp(48));star.setMinimumHeight(dp(48));star.setMinWidth(0);star.setMinimumWidth(0);star.setContentDescription((favorite?"Убрать из избранного: ":"В избранное: ")+pet.optString("name"));foot.addView(star,new LinearLayout.LayoutParams(dp(48),dp(48)));card.addView(foot);
            star.setOnClickListener(v->{Set<String> set=favorites();if(!set.remove(id))set.add(id);owner.getSharedPreferences(Pets.PREFS,0).edit().putStringSet("favorites",set).apply();filter();});card.setContentDescription((selected?"Выбрано. ":"Выбрать ")+pet.optString("name"));card.setFocusable(true);card.setOnClickListener(v->{owner.select(index);dismiss();});return card;
        }
    }
}
