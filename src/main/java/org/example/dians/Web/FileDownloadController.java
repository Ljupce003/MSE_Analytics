package org.example.dians.Web;

import org.example.dians.Component.PythonRunnerFlag;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.File;

@RestController
public class FileDownloadController {

    //private static final long MAX_WAIT_TIME = 10000;

    @GetMapping("/download/mega-data.csv")
    public ResponseEntity<FileSystemResource> downloadFile_csv() {
        if (PythonRunnerFlag.flag) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(null);
        }

        File file = new File("src/main/python/Smestuvanje/mega-data.csv");

        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=mega-data.csv");
        headers.add(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_OCTET_STREAM_VALUE);

        // Return the file as a download
        return ResponseEntity.ok()
                .headers(headers)
                .body(new FileSystemResource(file));
    }

    @GetMapping("/download/processed_lstm.csv")
    public ResponseEntity<FileSystemResource> downloadFile_lstm() {
        // Replace with the actual path to the generated CSV file
        File file = new File("src/main/python/Smestuvanje/processed_lstm.csv");
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }
        // Create the response headers
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=processed_lstm.csv");
        headers.add(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_OCTET_STREAM_VALUE);

        // Return the file as a download
        return ResponseEntity.ok()
                .headers(headers)
                .body(new FileSystemResource(file));
    }




    @GetMapping("/download/issuer_names.json")
    public ResponseEntity<FileSystemResource> downloadFile_json() {
        // Replace with the actual path to the generated CSV file
        File file = new File("src/main/python/Smestuvanje/issuer_names.json");
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }
        // Create the response headers
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=issuer_names.json");
        headers.add(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_OCTET_STREAM_VALUE);

        // Return the file as a download
        return ResponseEntity.ok()
                .headers(headers)
                .body(new FileSystemResource(file));
    }

    @GetMapping("/download/names.json")
    public ResponseEntity<FileSystemResource> downloadFile_names() {
        // Replace with the actual path to the generated CSV file
        File file = new File("src/main/python/Smestuvanje/names.json");
        if (!file.exists()) {
            return ResponseEntity.notFound().build();
        }
        // Create the response headers
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=names.json");
        headers.add(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_OCTET_STREAM_VALUE);

        // Return the file as a download
        return ResponseEntity.ok()
                .headers(headers)
                .body(new FileSystemResource(file));
    }
}
