package org.example.dians.Scraping;

import org.example.dians.model.ScriptProgress;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ProgressLineParser {

    // Matches: PROGRESS|52.3|[5/129]: ALK - scraping | Elapsed: 34s | ETA: 14:03
    private static final Pattern PROGRESS_PATTERN = Pattern.compile(
            "^PROGRESS\\|([\\d.]+)\\|(.*)$"
    );

    // Matches: [5/129]: ALK
    private static final Pattern INDEX_PATTERN = Pattern.compile(
            "\\[(\\d+)/(\\d+)]:\\s*(\\S+)"
    );

    // Matches: Elapsed: 34s
    private static final Pattern ELAPSED_PATTERN = Pattern.compile(
            "Elapsed:\\s*(\\d+)s"
    );

    // Matches: ETA: 14:03
    private static final Pattern ETA_PATTERN = Pattern.compile(
            "ETA:\\s*(\\d{2}:\\d{2})"
    );

    // Matches: TOTAL|129
    private static final Pattern TOTAL_PATTERN = Pattern.compile(
            "^TOTAL\\|(\\d+)$"
    );

    // Matches: DONE|50|Completed in 123.45s
    private static final Pattern DONE_PATTERN = Pattern.compile(
            "^DONE\\|(\\d+)(.*)$"
    );

    /**
     * Parse a single stdout line and update the progress object.
     * Returns true if the line was recognized and parsed.
     */
    public static boolean parse(String line, ScriptProgress progress) {
        if (line == null || line.isBlank()) {
            return false;
        }

        String trimmed = line.trim();

        // --- TOTAL line ---
        Matcher totalMatcher = TOTAL_PATTERN.matcher(trimmed);
        if (totalMatcher.matches()) {
            progress.setTotalItems(Integer.parseInt(totalMatcher.group(1)));
            return true;
        }

        // --- DONE line ---
        Matcher doneMatcher = DONE_PATTERN.matcher(trimmed);
        if (doneMatcher.matches()) {
            progress.setPercentage(100.0);
            progress.setComplete(true);
            progress.setMessage("Complete — processed " + doneMatcher.group(1) + " items");
            progress.setEta("00:00");
            return true;
        }

        // --- PROGRESS line ---
        Matcher progressMatcher = PROGRESS_PATTERN.matcher(trimmed);
        if (progressMatcher.matches()) {
            double pct = Double.parseDouble(progressMatcher.group(1));
            String info = progressMatcher.group(2);

            progress.setPercentage(pct);
            progress.setMessage(info);

            // Extract [idx/total]: CODE
            Matcher indexMatcher = INDEX_PATTERN.matcher(info);
            if (indexMatcher.find()) {
                progress.setCurrentIndex(Integer.parseInt(indexMatcher.group(1)));
                progress.setTotalItems(Integer.parseInt(indexMatcher.group(2)));
                progress.setCurrentItem(indexMatcher.group(3));
            }

            // Extract Elapsed
            Matcher elapsedMatcher = ELAPSED_PATTERN.matcher(info);
            if (elapsedMatcher.find()) {
                progress.setElapsedSeconds(Long.parseLong(elapsedMatcher.group(1)));
            }

            // Extract ETA
            Matcher etaMatcher = ETA_PATTERN.matcher(info);
            if (etaMatcher.find()) {
                progress.setEta(etaMatcher.group(1));
            }

            return true;
        }

        return false;
    }
}

