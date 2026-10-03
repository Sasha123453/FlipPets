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
    final MainActivity owner;final ArrayList<Integer> rows=new ArrayList<>();
    final Map<String,Bitmap> thumbs=new HashMap<>();final Adapter adapter=new Adapter();
    final TextView count;String category="Все",query="";
    int dp(float value){return Math.round(value*owner.getResources().getDisplayMetrics().density);}
    TextView label(String value,int size){TextView t=new TextView(owner);t.setText(value);t.setTextColor(Color.WHITE);t.setTextSize(size);return t;}
    public GalleryDialog(MainActivity a){
        super(a,android.R.style.Theme_Material_NoActionBar);owner=a;
        LinearLayout root=new LinearLayout(a);root.setOrientation(1);root.setPadding(dp(16),dp(20),dp(16),dp(12));root.setBackgroundColor(0xff111c28);setContentView(root);root.setOnApplyWindowInsetsListener((v,i)->{android.graphics.Insets bars=android.os.Build.VERSION.SDK_INT>=30?i.getInsets(android.view.WindowInsets.Type.systemBars()|android.view.WindowInsets.Type.displayCutout()):android.graphics.Insets.of(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());v.setPadding(dp(16)+bars.left,dp(20)+bars.top,dp(16)+bars.right,dp(12)+bars.bottom);return i;});
        LinearLayout top=new LinearLayout(a);TextView title=label("Оформление",25);top.addView(title,new LinearLayout.LayoutParams(0,-2,1));Button close=new Button(a);close.setText("Готово");close.setAllCaps(false);close.setOnClickListener(v->dismiss());top.addView(close);root.addView(top);
        EditText search=new EditText(a);search.setSingleLine(true);search.setTextColor(Color.WHITE);search.setHintTextColor(0xff9eb0bf);search.setHint("Найти оформление");root.addView(search);search.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int start,int count,int after){}public void onTextChanged(CharSequence s,int start,int before,int count){query=s.toString();filter();}public void afterTextChanged(Editable e){}});
        HorizontalScrollView scroll=new HorizontalScrollView(a);scroll.setHorizontalScrollBarEnabled(false);LinearLayout tabs=new LinearLayout(a);scroll.addView(tabs);root.addView(scroll);
        for(String name:new String[]{"Все","Избранное","Питомцы","Часы и виджеты","Фото и текст","Видео","Эффекты"}){Button b=new Button(a);b.setText(name);b.setAllCaps(false);b.setOnClickListener(v->{category=name;filter();for(int i=0;i<tabs.getChildCount();i++)((Button)tabs.getChildAt(i)).setTextColor(tabs.getChildAt(i)==b?0xff91b947:0xff182432);});tabs.addView(b);}
        count=label("",13);count.setPadding(0,dp(8),0,dp(8));root.addView(count);
        GridView grid=new GridView(a);grid.setNumColumns(2);grid.setHorizontalSpacing(dp(10));grid.setVerticalSpacing(dp(10));grid.setAdapter(adapter);root.addView(grid,new LinearLayout.LayoutParams(-1,0,1));
        filter();setOnDismissListener(v->{for(Bitmap image:thumbs.values())if(image!=null)image.recycle();thumbs.clear();if(!owner.isFinishing()&&!owner.isDestroyed())owner.preview.start();});
    }
    public void show(){owner.preview.stop();super.show();getWindow().setLayout(-1,-1);getWindow().setStatusBarColor(0xff111c28);getWindow().setNavigationBarColor(0xff111c28);getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);}
    static String group(JSONObject pet){String type=pet.optString("renderer"),kind=pet.optString("kind"),name=pet.optString("name");if(kind.equals("composition"))return type.equals("analog")||type.equals("dragon")||type.equals("stretch")||type.equals("steps")?"Часы и виджеты":"Фото и текст";if(kind.equals("video"))return "Видео";if(name.equals("Flowing glitter")||name.equals("Системные эффекты")||name.equals("Butterfly carp"))return "Эффекты";return "Питомцы";}
    Set<String> favorites(){return new HashSet<>(owner.getSharedPreferences(Pets.PREFS,0).getStringSet("favorites",Collections.emptySet()));}
    void filter(){rows.clear();Set<String> stars=favorites();JSONArray cat=Pets.catalog(owner);for(int i=0;i<cat.length();i++){JSONObject p=cat.optJSONObject(i);if(!p.optString("name").toLowerCase(Locale.ROOT).contains(query.toLowerCase(Locale.ROOT)))continue;if(category.equals("Избранное")&&!stars.contains(p.optString("id")))continue;if(!category.equals("Все")&&!category.equals("Избранное")&&!category.equals(group(p)))continue;rows.add(i);}count.setText(rows.size()==0?"Пока пусто. Добавь оформление в избранное кнопкой ☆.":"Найдено: "+rows.size()+" · "+category);adapter.notifyDataSetChanged();}
    Bitmap thumb(String id){if(!thumbs.containsKey(id)){Bitmap b=null;try(java.io.InputStream s=owner.getAssets().open("thumbs/"+id+".webp")){b=BitmapFactory.decodeStream(s);}catch(Exception ignored){}thumbs.put(id,b);}return thumbs.get(id);}
    class Adapter extends BaseAdapter {
        public int getCount(){return rows.size();}public Object getItem(int position){return rows.get(position);}public long getItemId(int position){return rows.get(position);}
        public View getView(int position,View convert,ViewGroup parent){int index=rows.get(position);JSONObject pet=Pets.catalog(owner).optJSONObject(index);String id=pet.optString("id");LinearLayout card=new LinearLayout(owner);card.setOrientation(1);card.setPadding(dp(10),dp(8),dp(10),dp(6));GradientDrawable bg=new GradientDrawable();bg.setColor(0xff203143);bg.setCornerRadius(dp(16));bg.setStroke(dp(Pets.current(owner).optString("id").equals(id)?2:0),0xffc3ec79);card.setBackground(bg);
            ImageView image=new ImageView(owner);image.setImageBitmap(thumb(id));image.setScaleType(ImageView.ScaleType.FIT_CENTER);card.addView(image,new LinearLayout.LayoutParams(-1,dp(145)));
            TextView name=label(pet.optString("name"),15);name.setMaxLines(2);name.setMinHeight(dp(44));card.addView(name);
            LinearLayout foot=new LinearLayout(owner);TextView kind=label(group(pet),11);kind.setTextColor(0xffb9cbd6);foot.addView(kind,new LinearLayout.LayoutParams(0,-2,1));Button star=new Button(owner);boolean favorite=favorites().contains(id);star.setText(favorite?"★":"☆");star.setTextSize(22);star.setPadding(0,0,0,0);star.setMinWidth(0);star.setMinimumWidth(0);star.setContentDescription((favorite?"Убрать из избранного: ":"В избранное: ")+pet.optString("name"));foot.addView(star,new LinearLayout.LayoutParams(dp(44),dp(44)));card.addView(foot);
            star.setOnClickListener(v->{Set<String> set=favorites();if(!set.remove(id))set.add(id);owner.getSharedPreferences(Pets.PREFS,0).edit().putStringSet("favorites",set).apply();filter();});card.setContentDescription("Выбрать "+pet.optString("name"));card.setOnClickListener(v->{owner.select(index);dismiss();});return card;
        }
    }
}
