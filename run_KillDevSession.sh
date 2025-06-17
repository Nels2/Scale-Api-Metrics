#!/bin/bash
date=$(date '+%Y-%m-%d__%H%M')
echo "$date :: BEGIN JOB."
source /Projects/scale_metrics/vfx/bin/activate #launch the venv version
#pip list         #list the items installed in VENV
#echo "$date :: pip_list has been omitted! not showing list.."
python_executable="/Projects/scale_metrics/vfx/bin/python"
bash_executable="/bin/bash"
cd "/Projects/scale_metrics"
echo "$date :: Currently within directory - $(pwd)"

# Path to session file
SESSION_FILE="session/devcall_sessionLogin.p"
echo "$date :: No check was made to session file, continuing killing this old session."
$python_executable kill_sessionID4Dev.py
echo "$date :: Session killed!"
echo "$date :: END JOB."
