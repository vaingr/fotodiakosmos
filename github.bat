@echo off
REM GitHub Application Management Menu

echo ========================================
echo      GitHub Application Manager
echo ========================================
echo.

:menu
echo Please select an option:
echo 1. First time app upload
echo 2. App update with code changes
echo 3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto confirm_first_upload
if "%choice%"=="2" goto confirm_app_update
if "%choice%"=="3" goto exit
echo Invalid choice. Please try again.
goto menu

:confirm_first_upload
echo.
echo Are you sure you want to perform first time app upload?
echo This will initialize a new Git repository and push to GitHub.
set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" goto first_upload
if /i "%confirm%"=="yes" goto first_upload
echo Operation cancelled.
pause
goto menu

:confirm_app_update
echo.
echo Are you sure you want to update the app with code changes?
echo This will add, commit, and push all changes to GitHub.
set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" goto app_update
if /i "%confirm%"=="yes" goto app_update
echo Operation cancelled.
pause
goto menu

:first_upload
echo.
set /p githubpath="Enter GitHub repository URL: "
echo.
echo Initializing Git repository...
git init
echo.
echo Adding all files...
git add .
echo.
echo Creating initial commit...
git commit -m "Initial commit"
echo.
echo Adding remote origin...
git remote add origin %githubpath%
echo.
echo Setting main branch...
git branch -M main
echo.
echo Pushing to GitHub...
git push -u origin main
echo.
echo First time upload completed!
pause
goto menu

:app_update
echo.
echo Adding all files....
git add .

set /p commitMessage=Describe changes for commit: 
git commit -m "%commitMessage%"

echo Pushing.....
git push origin main

echo End of process!
pause
goto menu

:exit
echo.
echo Thank you for using GitHub Application Manager!
echo.
exit
