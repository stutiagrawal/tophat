import runBashCmd
import logging
import argparse
import os
import setupLog
import time
import multiprocessing
import subprocess
import glob
import re

def retrieve_fastq_files(analysis_id, cghub_key, output_dir):
    if not os.path.isdir(os.path.join(output_dir, analysis_id)):
        os.system("gtdownload -v -c %s -p %s %s" %(cghub_key, output_dir, analysis_id))

def scan_workdir_helper(dirname, extension):
    fastq_files = glob.glob(os.path.join(dirname, "*_[12].%s"%(extension)))
    all_read_groups = list()
    read_group_set = dict()
    if not (fastq_files == []):
        for filename in fastq_files:
            rg_id = re.sub(r'_[12].%s$'%(extension), '', filename)
            read_group_set[rg_id] = read_group_set.get(rg_id, 0) + 1
        if not all(i == 2 for i in read_group_set.values()):
            raise Exception("Missing Pair")
        print read_group_set
        for rg_id in read_group_set.keys():
            reads_1 = "%s_1.%s" %(rg_id, extension)
            reads_2 = "%s_2.%s" %(rg_id, extension)
            read_pair = (os.path.basename(rg_id), reads_1, reads_2)
            all_read_groups.append(read_pair)

    return all_read_groups
def scan_workdir(dirname):
    """ Select the unpacked fastq files """

    print dirname
    fastq_files = scan_workdir_helper(dirname, "fastq")
    if fastq_files == []:
        fastq_files = scan_workdir_helper(dirname, "fastq.gz")
        if fastq_files == []:
            fastq_files = scan_workdir_helper(dirname, "fastq.bz")
    return fastq_files

    """
    reads_1 = ""
    reads_2 = ""
    fastq_files = glob.glob(os.path.join(dirname, "*_[12].fastq"))
    if fastq_files == []:
        fastq_files = glob.glob(os.path.join(dirname, "*_[12].fastq.gz"))
    if len(fastq_files) < 2:
        raise Exception("Missing Pair")

    for filename in fastq_files:
        if filename.endswith('_1.fastq') or filename.endswith('_1.fastq.gz'):
            reads_1 = filename
        if filename.endswith('_2.fastq') or filename.endswith('_2.fastq.gz'):
            reads_2 = filename

    return reads_1, reads_2
    """
def decompress(filename, workdir, logger):
    """ Unpack the fastq files """

    if filename.endswith(".tar"):
        print "ending in tar"
        cmd = ['tar','xvf', filename, '-C', workdir]
    elif filename.endswith(".gz"):
        cmd = ['tar', 'xvzf', filename, '-C', workdir]
    elif filename.endswith(".bz"):
        cmd = ['tar', 'xvjf', filename, '-C', workdir]
    else:
        raise Exception('Unknown input file extension for file %s' % filename)
    run_command(cmd, logger)

def run_command(cmd, logger):
    """ Run a subprocess command """

    stdoutdata, stderrdata = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
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

def tophat_paired(tmp_dir, output_dir, transcriptome_index,
                  num_proc, genome_annotation, analysis_id,
                  bowtie2_build_basename, reads_1, reads_2,
                  picard_path, logger):
    """ Perform tophat on paired end data and fix mate information """
    print "Aligning using TopHat"
    cmd = ['time', '/usr/bin/time', 'tophat2', '-p', '%s' %num_proc,
            '--library-type=fr-unstranded',
            '--segment-length', '20',
            '--no-coverage-search',
            '--min-intron-length', '6',
            '-G', '%s' %genome_annotation,
            '--max-multihits','20',
            '--mate-inner-dist', '350',
            '--mate-std-dev', '300',
            '--fusion-search',
            '--fusion-min-dist', '1000000',
            '--tmp-dir', tmp_dir,
            '-o', output_dir,
            '--transcriptome-index', transcriptome_index,
            bowtie2_build_basename,
            reads_1, reads_2
            ]
    log_function_time('TOPHAT', analysis_id, cmd, logger)

    #fix mate information
    cmd = ['time', '/usr/bin/time', 'java', '-jar', picard_path, 'FixMateInformation',
            'INPUT=%s' % (os.path.join(output_dir, 'accepted_hits.bam')),
            'ASSUME_SORTED=false',
            'VALIDATION_STRINGENCY=LENIENT',
            'TMP_DIR=%s' %tmp_dir]
    log_function_time('FIXMATEINFORMATION', analysis_id, cmd, logger)

def downstream_steps(output_dir, analysis_id, read_groups, logger):
    """ merge and sort unmapped reads with mapped reads """

    out_file_basename = os.path.join(output_dir, analysis_id, analysis_id)

    merge_cmd = ['time', '/usr/bin/time', 'samtools', 'merge', '-',]
    for rg_id in read_groups:
        rg_id_dir = os.path.join(output_dir, analysis_id, rg_id)
        mapped_reads = os.path.join(rg_id_dir, 'accepted_hits.bam')
        unmapped_reads = os.path.join(rg_id_dir, 'unmapped.bam')
        if os.path.isfile(mapped_reads):
            merge_cmd.append(mapped_reads)
        if os.path.isfile(unmapped_reads):
            merge_cmd.append(unmapped_reads)

    print merge_cmd
    sort_cmd = ['samtools', 'sort','-', out_file_basename]
    start_time = time.time()
    merge = subprocess.Popen(merge_cmd, stdout=subprocess.PIPE)
    sort = subprocess.check_output(sort_cmd, stdin=merge.stdout)
    end_time = time.time()
    logger.info("SAMTOOLS_TIME:%s\t%s" %(analysis_id, (end_time-start_time)/60.0))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='align_tophat.py', description='RNA-seq alignment using TopHat')
    #parser.add_argument('tarfile', help='path to tarfile')
    parser.add_argument('index', help='path to index directory')
    parser.add_argument('genome_annotation', help='path to genome annotation file')
    parser.add_argument('tmp_dir', help='path to temporary directory',
                        default='/mnt/cinder/SCRATCH/data/top_hat_tmp_dir')
    parser.add_argument('analysis_id', help='analysis id of the sample')
    parser.add_argument('bowtie2_build_basename', help='path to bowtie2_build')
    parser.add_argument('--outdir', help='path to output directory', default=os.getcwd())
    parser.add_argument('--cghub', help='path to cghub key', default="/home/ubuntu/keys/cghub.key")
    parser.add_argument('--p', help='number of threads', default = int(0.8 * multiprocessing.cpu_count()))
    parser.add_argument('--picard', help='path to picard executable',
                        default='/home/ubuntu/tools/picard-tools-1.128/picard.jar')
    args = parser.parse_args()

    log_file = "%s.log" % os.path.join(args.outdir, "%s_1" %args.analysis_id)

    logger = setupLog.setup_logging(logging.INFO, "%s_1" %args.analysis_id, log_file)
    if not os.path.isdir(args.tmp_dir):
        os.mkdir(args.tmp_dir)
    #Unpack the files
    #decompress(args.tarfile, args.outdir, logger)
    #Select the fastq reads
    read_group_pairs = scan_workdir(os.path.join(args.outdir, args.analysis_id))
    read_groups = list()
    print read_group_pairs
    #Perform the paired end alignment
    start_time = time.time()
    for (rg_id, reads_1, reads_2) in read_group_pairs:
        read_groups.append(rg_id)
        """
        print rg_id, reads_1, reads_2
        rg_id_dir = os.path.join(args.outdir, args.analysis_id, rg_id)
        if not os.path.isdir(rg_id_dir):
            os.mkdir(rg_id_dir)
        tophat_paired(args.tmp_dir, rg_id_dir, args.index,
                    args.p, args.genome_annotation, rg_id,
                    args.bowtie2_build_basename, reads_1, reads_2,
                    args.picard, logger)
    end_time = time.time()
    """
    #Merge and sort the resulting BAM
    downstream_steps(args.outdir, args.analysis_id, read_groups, logger)
    """
    #Remove the reads
        bam_file_name = "%s.bam" % os.path.join(args.outdir, args.analysis_id)
        if os.path.isfile(bam_file_name) and os.path.getsize(bam_file_name):
            os.remove(reads_1)
            os.remove(reads_2)
    """
