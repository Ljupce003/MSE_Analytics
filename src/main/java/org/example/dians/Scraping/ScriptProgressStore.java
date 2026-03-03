
package org.example.dians.Scraping;

import org.example.dians.model.ScriptProgress;
import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class ScriptProgressStore {

    private static final Map<String, ScriptProgress> progressMap = new ConcurrentHashMap<>();

    public static ScriptProgress getOrCreate(String scriptName) {
        return progressMap.computeIfAbsent(scriptName, ScriptProgress::new);
    }

    public static ScriptProgress get(String scriptName) {
        return progressMap.get(scriptName);
    }

    public static Map<String, ScriptProgress> getAll() {
        return Map.copyOf(progressMap);
    }

    public static void remove(String scriptName) {
        progressMap.remove(scriptName);
    }
}
