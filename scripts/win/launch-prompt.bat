@SET CONDAROOT=%USERPROFILE%\Miniconda3

@SET CONDAENV=analysis

@CALL "%CONDAROOT%\Scripts\activate" "%CONDAENV%"

@cd "%~dp0..\.."

@cmd
