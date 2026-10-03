import org.flippets.app.PlaybackPolicy;

/** Contrasting native state policies: finite pets, continuous state, finite reactions. */
public class PlaybackPolicyTest {
    static void check(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] args){
        for(String id:new String[]{"bird-pandora","seal-pandora","sheep-archived-presets","capybara-archived-presets","otter-archived-presets"}){
            check(!PlaybackPolicy.repeats(id,"ambient",0,false));
        }
        for(int scene=0;scene<8;scene++){
            check(PlaybackPolicy.repeats("koala-archived-presets","reactive",scene,false));
            check(!PlaybackPolicy.repeats("koala-archived-presets","reactive",scene,true));
        }
        for(int scene=8;scene<17;scene++)check(!PlaybackPolicy.repeats("roedeer-archived-presets","reactive",scene,false));
        check(PlaybackPolicy.repeats("q_carp-pandora","ambient",0,false));
        System.out.println("Playback policy: 31 assertions passed");
    }
}
