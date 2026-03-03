@echo off
set JAVA_HOME=%~dp0java\jdk-21.0.10+7-jre
set PATH=%JAVA_HOME%\bin;%PATH%
java -jar "%~dp0topcat-full.jar" %*
