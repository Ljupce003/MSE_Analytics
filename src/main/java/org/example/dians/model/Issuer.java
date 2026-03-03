package org.example.dians.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public class Issuer {
    private String title;
    private String link;
    private String code;
    private String result;
    private Double score;
    private String last_date;

    @JsonProperty("rss_items")
    private List<RssItem> rss_items;

    @JsonProperty("model_processed_texts")
    private List<Processed_text> model_processed_texts;


    public String getTitle() {
        return title;
    }

    public String getResult() {
        return result;
    }

    public void setResult(String result) {
        this.result = result;
    }

    public Double getScore() {
        return score;
    }

    public void setScore(Double score) {
        this.score = score;
    }

    public String getLast_date() {
        return last_date;
    }

    public void setLast_date(String last_date) {
        this.last_date = last_date;
    }

    public List<Processed_text> getModel_processed_texts() {
        return model_processed_texts;
    }

    public void setModel_processed_texts(List<Processed_text> model_processed_texts) {
        this.model_processed_texts = model_processed_texts;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getLink() {
        return link;
    }

    public void setLink(String link) {
        this.link = link;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public List<RssItem> getRss_items() {
        return rss_items;
    }

    public void setRss_items(List<RssItem> rss_items) {
        this.rss_items = rss_items;
    }
}


