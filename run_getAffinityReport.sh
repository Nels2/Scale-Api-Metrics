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
# Check if session file exists
if [ -f "$SESSION_FILE" ]; then
    # Get the last modified time of the session file
    last_mod_time=$(stat -c %Y "$SESSION_FILE")
    current_time=$(date +%s)
    age=$((current_time - last_mod_time))
    
    if [ "$age" -ge 43200 ]; then
        echo "$date :: Session file is older than 12 hours, killing this old session."
        $python_executable kill_sessionID4Dev.py
        echo "$date :: Regenerating session..."
        $python_executable gen_sessionID4Dev.py
    else
        echo "$date :: Using existing session file from $last_mod_time - currently it is $current_time"
    fi
else
    echo "$date :: Session file does not exist, generating a new session."
    touch $SESSION_FILE
    $python_executable gen_sessionID4Dev.py

fi

script2use="get_SnapshotReport.py"
#pip install -r requirements.txt
echo "$date :: Running $script2use ..."
#authbind --deep $python_executable $projectpath
$python_executable $script2use
deactivate
echo "$date :: END JOB."
