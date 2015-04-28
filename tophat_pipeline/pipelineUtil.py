import os
import sys
import subprocess
import logging
import time

def run_command(cmd, logger=None):
    """ Run a subprocess command """

    print cmd
    stdoutdata, stderrdata = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()

    if logger != None:
        stdoutdata = stdoutdata.split("\n")
        for line in stdoutdata:
            logger.info(line)

        stderrdata = stderrdata.split("\n")
        for line in stderrdata:
            logger.info(line)

def log_function_time(fn, analysis_id, cmd, logger):
    """ Log the time taken by a command to the logger """

    start_time = time.time()
    run_command(cmd, logger)
    end_time = time.time()
    logger.info("%s_TIME\t%s\t%s" %(fn, analysis_id,  (end_time - start_time)/60.0))

def download_from_cleversafe(logger, bucket, remote_input, local_output):
    """ Download a file from cleversafe to a local folder """

    filename_on_cleversafe = os.path.join(bucket, remote_input)
    cmd = ['s3cmd', 'sync', filename_on_cleversafe, local_output]
    run_command(cmd, logger)

def upload_to_cleversafe(logger, bucket, local_input, remote_output=""):
    """ Upload a file to cleversafe to a folder """

    if remote_output != "":
        cmd = ['s3cmd', 'sync', local_input, '%s' % os.path.join(bucket, remote_output)]
    else:
        cmd = ['s3cmd', 'sync', local_input, bucket]
    run_command(cmd, logger)
