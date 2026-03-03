package org.example.dians.model;

import lombok.Getter;
import lombok.Setter;

@Getter
public class ScriptProgress {
    private String scriptName;
    @Setter
    private double percentage;
    @Setter
    private String currentItem;
    @Setter
    private int currentIndex;
    @Setter
    private int totalItems;
    @Setter
    private long elapsedSeconds;
    @Setter
    private String eta;
    @Setter
    private String message;
    @Setter
    private boolean complete;

    public ScriptProgress(String scriptName) {
        this.scriptName = scriptName;
        this.percentage = 0.0;
        this.currentItem = "";
        this.currentIndex = 0;
        this.totalItems = 0;
        this.elapsedSeconds = 0;
        this.eta = "00:00";
        this.message = "Waiting...";
        this.complete = false;
    }

}

