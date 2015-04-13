import os
import sys
import subprocess
import logging

default_logger = logging.getLogger(name='aligner')

def _find_bash():
    """Originally from https://github.com/chapmanb/bcbio-nextgen/blob/master/bcbio/provenance/do.py"""

    try:
        which_bash = subprocess.check_output(["which", "bash"]).strip()
    except subprocess.CalledProcessError:
        which_bash = None
    for test_bash in [which_bash, "/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash"]:
        if test_bash and os.path.exists(test_bash):
            return test_bash
    raise IOError("Could not find bash in any standard location. Needed for unix pipes")

def _normalize_cmd_args(cmd):
    """Normalize subprocess arguments to handle list commands, string and pipes.
Piped commands set pipefail and require use of bash to help with debugging
intermediate errors.
Originally from https://github.com/chapmanb/bcbio-nextgen/blob/master/bcbio/provenance/do.py
"""
    if isinstance(cmd, basestring):
        # check for standard or anonymous named pipes
        if cmd.find(" | ") > 0 or cmd.find(">(") or cmd.find("<("):
            return "set -o pipefail; " + cmd, True, _find_bash()
        else:
            return cmd, True, None
    else:
        return cmd, False, None

def _do_run(cmd, output_file=None, input_file=None, logger=default_logger):
    """Perform running and check results, raising errors for issues.
Originally from https://github.com/chapmanb/bcbio-nextgen/blob/master/bcbio/provenance/do.py
"""
    cmd, shell_arg, executable_arg = _normalize_cmd_args(cmd)
    #error_msg = ""
    print cmd
    """
    if output_file is None:
        stdout_value = subprocess.PIPE
    else:
        stdout_value = output_file
    """
    logger.info('Starting: %s' % cmd)
    s= subprocess.Popen(cmd, shell=shell_arg, executable=executable_arg,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         stdin=input_file)
    stdoutdata, stderrdata = s.communicate()
    print stdoutdata, stderrdata
    exitcode = s.poll()
    if exitcode is not None and exitcode != 0:
        #error_msg += " ".join(cmd)
        #error_msg += " ".join(stdoutdata)
        #error_msg += " ".join(stderrdata)
        #s.communicate()
        #s.stdout.close()
        raise subprocess.CalledProcessError(exitcode, stderrdata)

    stdoutdata = stdoutdata.split("\n")
    for line in stdoutdata:
        logger.info(line)
    if(stderrdata != None):
        stderrdata = stderrdata.split("\n")
        for line in stderrdata:
            logger.info(line)

    """
    while True:
        stdout_line = stdoutdata.readline()
        if stdout_line:
            debug_stdout.append(stdout_line)

            logger.debug(stdout_line.rstrip())

        exitcode = s.poll()
                break
        sys.stdout.flush()

    s.communicate()
    s.stdout.close()
    """

    logger.info('Completed: %s' % cmd)
    return exitcode

