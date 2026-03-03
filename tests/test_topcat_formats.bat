@echo off
set JAVA_HOME=%~dp0..\tools\java\jdk-21.0.10+7-jre
set PATH=%JAVA_HOME%\bin;%PATH%
set STILTS=%~dp0..\tools\stilts.jar

echo === CSV Format Test ===
java -jar %STILTS% tpipe in="%~dp0..\templates\star_catalog_template.csv" ifmt=csv omode=count

echo === FITS Format Test ===
java -jar %STILTS% tpipe in="%~dp0..\templates\star_catalog_template.fits" ifmt=fits omode=count

echo === VOTable Format Test ===
java -jar %STILTS% tpipe in="%~dp0..\templates\star_catalog_template.vot" ifmt=votable omode=count

echo === All format tests complete ===
