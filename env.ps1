
$env:JAVA_HOME = "C:\Java\jdk-17"  # Path to your Java 17 installation
$env:Path = "$env:JAVA_HOME\bin;" + $env:Path

# This is critical for Maven
[Environment]::SetEnvironmentVariable("JAVA_HOME", $env:JAVA_HOME, "Process")

Write-Host "--- Java 17 Session Active ---" -ForegroundColor Cyan
java -version
mvn -v