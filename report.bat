@echo off
setlocal enabledelayedexpansion
::
:: ::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: BATCH File to Call IVR script on windows
::
:: allows for --tag to be entered to change docker hub image
:: use --pull to pull the current image down from docker hub
::
:: ::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Define default variables
::

set "image_name=ironbow/ucreport"
set "tag_name=latest"
set "script_name=clickreport.py"
::
set "current_dir=%cd%"
set "input_dir=input"
set "output_dir=output"
set "log_dir=logs"
set "docker_args="
set "pull_request=false"
::set "all_args=%*"

::
:: ::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Parse through parameters and pull out what is needed for this script
:: Pass on variables needed by docker
::
:parse_args
if "%~1"=="" goto endparse

:: process parameters that are only for this script (do not send to docker)

if "%~1"=="--tag" (
  set "tag_name=%~2"
  shift
  shift
  goto parse_args
)

if "%~1"=="--pull" (
  set "pull_request=true"
  shift
  goto parse_args
)

:: then parse parameters for this script that should also go to docker

if "%~1"=="--indir" (
    set "input_dir=%~2"
    set "docker_args=!docker_args! %~1 %~2"
    shift
    shift
    goto parse_args
)

if "%~1"=="--outdir" (
    set "output_dir=%~2"
    set "docker_args=!docker_args! %~1 %~2"
    shift
    shift
    goto parse_args
)

if "%~1"=="--logdir" (
    set "log_dir=%~2"
    set "docker_args=!docker_args! %~1 %~2"
    shift
    shift
    goto parse_args
)
:: Assuming anything else should go to docker

set "docker_args=!docker_args! %~1"
shift
goto parse_args

:endparse

::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Final Variable construction before calling docker
::

:: construct docker image name
if %tag_name% == "" (
	set "full_image_name=%image_name%"
) else (
	set "full_image_name=%image_name%:%tag_name%"
)

set "input_path=%current_dir%\%input_dir%"
set "output_path=%current_dir%\%output_dir%"
set "log_path=%current_dir%\%log_dir%"

::echo input_path:  %input_path%
::echo output_path: %output_path%
::echo log_path:    %log_path%
::echo full_image:  %full_image_name%
::echo docker_args: %docker_args%
::echo all_args:    %all_args%

::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Re-Pull current version of image if request from docker hub
::
if %pull_request% == "True" (
    echo Attempting to pull %full_image_name% down from Docker hub...
    echo.
    docker pull %full_image_name
    echo.
    echo If authentication is required, login by running: docker login
    echo.
    echo Check your current local images by running: docker images
    exit /b 0
)
::
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Construct and execute the docker run command
::

set "docker_command=docker run -v "%input_path%:/app/%input_dir%" -v "%output_path%:/app/%output_dir%" -v "%log_path%:/app/%log_dir%" -it --rm %full_image_name% python %script_name% %docker_args%"

::echo %docker_command%
call %docker_command%

endlocal