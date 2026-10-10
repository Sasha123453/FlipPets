package org.flippets.app;

/** Source-backed awake carp scene sequence; linear timing adapts Folme ease=1. */
public final class CarpSequence {
    public enum Phase { STOPPED, PLAYING, FADING_OUT, AWAITING_LOAD, HIDDEN_DELAY, FADING_IN }
    private static final double[] DEFAULT_THRESHOLDS={689d/719,689d/719,570d/600,566d/596};
    private final double[] thresholds;
    private final long fadeOutMs,fadeDelayMs,fadeInMs;
    private Phase phase=Phase.STOPPED;
    private int scene;
    private long phaseStarted,lastNow;
    public CarpSequence(){this(DEFAULT_THRESHOLDS,500,100,300);}
    public static double[] defaultThresholds(){return DEFAULT_THRESHOLDS.clone();}
    public CarpSequence(double[] thresholds,long fadeOutMs,long fadeDelayMs,long fadeInMs){
        if(thresholds==null||thresholds.length!=4)throw new IllegalArgumentException("Four scene thresholds required");
        this.thresholds=thresholds.clone();for(double t:this.thresholds)if(Double.isNaN(t)||Double.isInfinite(t)||t<0||t>=1)throw new IllegalArgumentException("Threshold must be finite in [0,1)");
        if(fadeOutMs<0||fadeDelayMs<0||fadeInMs<0)throw new IllegalArgumentException("Negative transition time");
        this.fadeOutMs=fadeOutMs;this.fadeDelayMs=fadeDelayMs;this.fadeInMs=fadeInMs;
    }
    public void start(int scene,long now){validScene(scene);this.scene=scene;lastNow=Math.max(0,now);phaseStarted=lastNow;phase=Phase.PLAYING;}
    /** Actual renderer progress, not wall-clock prediction of the video duration. */
    public void progress(long now,double actualProgress){long time=advance(now);if(phase==Phase.PLAYING&&!Double.isNaN(actualProgress)&&!Double.isInfinite(actualProgress)&&actualProgress>thresholds[scene]){phase=Phase.FADING_OUT;phaseStarted=time;advance(time);}}
    public float alpha(long now){long time=advance(now);switch(phase){case FADING_OUT:return 1-(time-phaseStarted)/(float)fadeOutMs;case AWAITING_LOAD:case HIDDEN_DELAY:return 0;case FADING_IN:return (time-phaseStarted)/(float)fadeInMs;default:return 1;}}
    public boolean needsNextScene(){return phase==Phase.AWAITING_LOAD;}
    /** Uniform choice among the three different scenes; no unbounded random retry. */
    public int nextScene(int choice){if(!needsNextScene())throw new IllegalStateException("No pending scene load");if(choice<0||choice>=3)throw new IllegalArgumentException("Choice must be 0..2");return (scene+1+choice)%4;}
    /** The renderer must acknowledge the load before the hidden delay can begin. */
    public void loaded(int next,long now){validScene(next);if(!needsNextScene()||next==scene)throw new IllegalStateException("Different pending scene required");long time=advance(now);scene=next;phase=Phase.HIDDEN_DELAY;phaseStarted=time;advance(time);}
    public void stop(){phase=Phase.STOPPED;lastNow=phaseStarted=0;}
    public int scene(){return scene;}
    public Phase phase(){return phase;}
    /** Monotonic start of the current phase; observes the actual load acknowledgement. */
    public long phaseStartedAt(){return phaseStarted;}
    public boolean transitioning(){return phase==Phase.FADING_OUT||phase==Phase.AWAITING_LOAD||phase==Phase.HIDDEN_DELAY||phase==Phase.FADING_IN;}
    public double threshold(int scene){validScene(scene);return thresholds[scene];}
    private static void validScene(int scene){if(scene<0||scene>=4)throw new IllegalArgumentException("Scene must be 0..3");}
    private long advance(long now){long time=Math.max(lastNow,Math.max(0,now));lastNow=time;
        if(phase==Phase.FADING_OUT&&time-phaseStarted>=fadeOutMs){phase=Phase.AWAITING_LOAD;}
        if(phase==Phase.HIDDEN_DELAY&&time-phaseStarted>=fadeDelayMs){phase=Phase.FADING_IN;phaseStarted+=fadeDelayMs;}
        if(phase==Phase.FADING_IN&&time-phaseStarted>=fadeInMs){phase=Phase.PLAYING;phaseStarted=time;}
        return time;
    }
}
