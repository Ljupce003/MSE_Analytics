package org.example.dians.model;

public class Processed_text {
    private String rss_link;
    private String original_text;
    private String text;
    private String label;
    private Double score;

    public String getRss_link() {
        return rss_link;
    }

    public void setRss_link(String rss_link) {
        this.rss_link = rss_link;
    }

    public String getOriginal_text() {
        return original_text;
    }

    public void setOriginal_text(String original_text) {
        this.original_text = original_text;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }

    public String getLabel() {
        return label;
    }

    public void setLabel(String label) {
        this.label = label;
    }

    public Double getScore() {
        return score;
    }

    public void setScore(Double score) {
        this.score = score;
    }
}
