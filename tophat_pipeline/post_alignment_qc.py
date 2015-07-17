import pipelineUtil
import os

def validate_bam_file(picard_path, bam_file, uuid, outdir, logger=None):
   """ Validate resulting post-alignment BAM file """

   if os.path.isfile(picard_path) and os.path.isfile(bam_file):
       cmd = ['java', '-jar', picard_path, "ValidateSamFile", "I=%s" %bam_file, "O=%s" %os.path.join(outdir, "picard_out.txt"), "VALIDATION_STRINGENCY=LENIENT"]
       pipelineUtil.log_function_time("ValidateSAM", uuid, cmd, logger)
   else:
       raise Exception("Invalid path to picard or BAM")

def collect_rna_seq_metrics(picard_path, bam_file, uuid, outdir, logger=None):
    """ Collect RNA-seq metrics using Picard """
    if os.path.isfile(picard_path) and os.path.isfile(bam_file):
        cmd = ['java', '-jar', picard_path, "CollectRnaSeqMetrics", "I=%s" %bam_file, "O=%s" %os.path.join(outdir, "rna_seq_metrics.txt")]
        pipelineUtil.log_function_time("RNAseq_metrics", uuid, cmd, logger)
    else:
        raise Exception("Invalid path to picard or bam")

def bam_index(bam_file, uuid, outdir, logger=None):
    """ Index the resultant post alignment BAM file """

    if os.path.isfile(bam_file, outdir, uuid, logger=None):
        cmd = ['samtools', 'index', '-b', bam_file, '%s.bam.bai' %(os.path.join(outdir, uuid))]
        pipelineUtil.log_function_time("BamIndex", uuid, cmd, logger)
    else:
        raise Exception("invalid bam file")

picard_path="/home/ubuntu/picard-tools-1.136/picard.jar"
bam_file="/home/ubuntu/SCRATCH/4bcf3463-ea9c-414e-a1f5-948f72477602/HCC1143.NORMAL.30x.compare.bam"
outdir="/home/ubuntu/SCRATCH/4bcf3463-ea9c-414e-a1f5-948f72477602"
validate_bam_file(picard_path, bam_file, "4bcf3463-ea9c-414e-a1f5-948f72477602", outdir)
