@ECHO OFF

SET CONDAENV=analysis

IF EXIST %USERPROFILE%\Anaconda3 (
  SET CONDAROOT=%USERPROFILE%\Anaconda3
) ELSE (
IF EXIST %USERPROFILE%\Miniconda3 (
  SET CONDAROOT=%USERPROFILE%\Miniconda3
IF EXIST C:\ProgramData\Anaconda3 (
  SET CONDAROOT=C:\ProgramData\Anaconda3
IF EXIST C:\ProgramData\Miniconda3 (
  SET CONDAROOT=C:\ProgramData\Miniconda3
) ELSE (
  ECHO ERROR: Could not find the conda root directory!
  PAUSE
  EXIT
))))

CALL "%CONDAROOT%\Scripts\activate" "%CONDAENV%"

CD "%~dp0..\.."

CMD
