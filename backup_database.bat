@echo off
REM Database Backup Script for SGP Costura
REM This script creates a backup of the PostgreSQL database

setlocal
set BACKUP_DIR=backups
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_FILE=%BACKUP_DIR%\sgp_costura_backup_%TIMESTAMP%.sql

REM Create backups directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo ========================================
echo SGP Costura - Database Backup
echo ========================================
echo.
echo Creating backup: %BACKUP_FILE%
echo.

REM Execute pg_dump inside the database container
docker-compose exec -T db pg_dump -U postgres sgp_costura > "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Backup created successfully!
    echo File: %BACKUP_FILE%
    echo.
    
    REM Show backup file size
    for %%A in ("%BACKUP_FILE%") do echo Size: %%~zA bytes
    echo.
) else (
    echo.
    echo ❌ Backup failed!
    echo.
)

REM Keep only last 7 backups
echo Cleaning old backups (keeping last 7)...
for /f "skip=7 delims=" %%F in ('dir /b /o-d "%BACKUP_DIR%\sgp_costura_backup_*.sql" 2^>nul') do (
    echo Deleting old backup: %%F
    del "%BACKUP_DIR%\%%F"
)

echo.
echo Done!
pause
