package org.example.dians.Scraping;

import org.example.dians.Component.PythonRunnerFlag;
import org.example.dians.model.ScriptProgress;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.CompletableFuture;

public class PythonScriptRunner {

    private static String getPythonExecutable() {
        String osName = System.getProperty("os.name").toLowerCase();
        String venvPath = System.getProperty("user.dir") + "/venv";

        if (osName.contains("win")) {
            File pythonExe = new File(venvPath, "Scripts/python.exe");
            if (pythonExe.exists()) {
                return pythonExe.getAbsolutePath();
            }
        } else {
            File pythonBin = new File(venvPath, "bin/python");
            if (pythonBin.exists()) {
                return pythonBin.getAbsolutePath();
            }
        }

        return "python";
    }

    private static void runScript(String scriptName) {
        System.out.println("Starting Python script: " + scriptName);

        // Initialize progress tracking
        ScriptProgress progress = ScriptProgressStore.getOrCreate(scriptName);
        progress.setPercentage(0);
        progress.setComplete(false);
        progress.setMessage("Starting...");

        File workingDirectory = new File(System.getProperty("user.dir"), "src/main/python");

        if (!workingDirectory.exists() || !workingDirectory.isDirectory()) {
            progress.setMessage("Invalid directory: " + workingDirectory.getAbsolutePath());
            progress.setComplete(true);
            throw new RuntimeException("Invalid directory: " + workingDirectory.getAbsolutePath());
        }

        String pythonPath = getPythonExecutable();
        File scriptFile = new File(workingDirectory, scriptName);

        if (!scriptFile.exists()) {
            progress.setMessage("Script not found: " + scriptFile.getAbsolutePath());
            progress.setComplete(true);
            throw new RuntimeException("Python script not found: " + scriptFile.getAbsolutePath());
        }

        ProcessBuilder processBuilder = new ProcessBuilder(pythonPath, scriptFile.getAbsolutePath());
        processBuilder.environment().put("PYTHONIOENCODING", "utf-8");
        processBuilder.directory(workingDirectory);
        processBuilder.redirectErrorStream(false);

        new Thread(() -> {
            try {
                Process process = processBuilder.start();

                CompletableFuture<Void> stdoutFuture = CompletableFuture.runAsync(() -> {
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            handleOutputLine(scriptName, line);
                        }
                    } catch (IOException e) {
                        System.err.println("Error reading stdout from '" + scriptName + "': " + e.getMessage());
                    }
                });

                CompletableFuture<Void> stderrFuture = CompletableFuture.runAsync(() -> {
                    try (BufferedReader errorReader = new BufferedReader(
                            new InputStreamReader(process.getErrorStream(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = errorReader.readLine()) != null) {
                            // silently consume stderr
                        }
                    } catch (IOException e) {
                        System.err.println("Error reading stderr from '" + scriptName + "': " + e.getMessage());
                    }
                });

                stdoutFuture.join();
                stderrFuture.join();

                int exitCode = process.waitFor();
                if (exitCode == 0) {
                    System.out.println("Python script '" + scriptName + "' finished successfully.");
                } else {
                    System.err.println("Python script '" + scriptName + "' exited with code " + exitCode);
                    progress.setMessage("Exited with code " + exitCode);
                }

                // Mark progress complete if DONE line wasn't received
                if (!progress.isComplete()) {
                    progress.setPercentage(100.0);
                    progress.setComplete(true);
                }

                switch (scriptName) {
                    case "Main.py" -> PythonRunnerFlag.flag = false;
                    case "Fundamental_processing.py" -> PythonRunnerFlag.analysis_flag = false;
                    case "LSTM.py" -> PythonRunnerFlag.lstm_flag = false;
                }
            } catch (InterruptedException e) {
                System.err.println("Error while waiting for '" + scriptName + "': " + e.getMessage());
                progress.setMessage("Interrupted: " + e.getMessage());
                progress.setComplete(true);
                Thread.currentThread().interrupt();
            } catch (IOException e) {
                progress.setMessage("IO Error: " + e.getMessage());
                progress.setComplete(true);
                throw new RuntimeException(e);
            }
        }).start();

        System.out.println("Python script '" + scriptName + "' is running in the background...");
    }

    private static void handleOutputLine(String scriptName, String line) {
        ScriptProgress progress = ScriptProgressStore.getOrCreate(scriptName);

        // Try to parse as a progress/total/done line
        boolean parsed = ProgressLineParser.parse(line, progress);

        if (parsed) {
            // Log parsed progress lines concisely
            System.out.printf("[%s] %.1f%% — %s%n", scriptName, progress.getPercentage(), progress.getMessage());
        } else {
            // Log unrecognized lines as-is (e.g. DEVICE|, issuer OK/ERROR lines)
            System.out.println("[" + scriptName + "] " + line);
        }
    }

    public static void runPythonScript() {
        PythonRunnerFlag.flag = true;
        runScript("Main.py");
    }

    public static void runPythonScriptFundamentalAnalysis() {
        PythonRunnerFlag.analysis_flag = true;
        runScript("Fundamental_processing.py");
    }

    public static void runPythonScriptLSTM() {
        PythonRunnerFlag.lstm_flag = true;
        runScript("LSTM.py");
    }
}
