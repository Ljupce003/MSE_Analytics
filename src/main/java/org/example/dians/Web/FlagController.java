package org.example.dians.Web;

import org.example.dians.Component.PythonRunnerFlag;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class FlagController {
    @GetMapping("/flag-status")
    public ResponseEntity<Boolean> getFlagStatus() {
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CACHE_CONTROL, "no-cache, no-store, must-revalidate");
        headers.add(HttpHeaders.PRAGMA, "no-cache");
        headers.add(HttpHeaders.EXPIRES, "0");

        return ResponseEntity.ok()
                .headers(headers)
                .body(PythonRunnerFlag.flag); // return the flag status
    }
}
