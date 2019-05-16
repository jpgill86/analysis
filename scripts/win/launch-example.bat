@SET CONDAROOT=%USERPROFILE%\Miniconda3

@SET CONDAENV=analysis

@CALL "%CONDAROOT%\Scripts\activate" "%CONDAENV%"

jupyter notebook "%~dp0..\..\example\Data Explorer.ipynb"
