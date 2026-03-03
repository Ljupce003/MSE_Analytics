package org.example.dians.Web;

import org.example.dians.Scraping.ScriptProgressStore;
import org.example.dians.model.ScriptProgress;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/progress")
public class ProgressApiController {

    @GetMapping("/{scriptName}")
    public ResponseEntity<ScriptProgress> getProgress(@PathVariable String scriptName) {
        ScriptProgress progress = ScriptProgressStore.get(scriptName);
        if (progress == null) return ResponseEntity.notFound().build();
        return ResponseEntity.ok(progress);
    }

    @GetMapping
    public ResponseEntity<Map<String, ScriptProgress>> getAll() {
        return ResponseEntity.ok(ScriptProgressStore.getAll());
    }
}
