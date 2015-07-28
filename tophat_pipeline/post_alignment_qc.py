import pipelineUtil
import os

def validate_bam_file(picard_path, bam_file, uuid, outdir, logger=None):
   """ Validate resulting post-alignment BAM file """

   if os.path.isfile(picard_path) and os.path.isfile(bam_file):
        tmp_dir = os.path.join(outdir, 'tmp')
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        cmd = ['java', '-jar', picard_path, "ValidateSamFile", "I=%s" %bam_file,
               "O=%s" %os.path.join(outdir, "%s.validate" %uuid), "VALIDATION_STRINGENCY=LENIENT",
               "TMP_DIR=%s" %tmp_dir]
        pipelineUtil.log_function_time("ValidateSAM", uuid, cmd, logger)
   else:
       raise Exception("Invalid path to picard or BAM")

def collect_rna_seq_metrics(picard_path, bam_file, uuid, outdir, ref_flat, logger=None):
    """ Collect RNA-seq metrics using Picard """

    if os.path.isfile(picard_path) and os.path.isfile(bam_file):
        tmp_dir = os.path.join(outdir, 'tmp')
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        cmd = ['java', '-jar', picard_path, "CollectRnaSeqMetrics", "METRIC_ACCUMULATION_LEVEL=READ_GROUP",
                "I=%s" %bam_file, "O=%s" %os.path.join(outdir, "%s.rna_seq_metrics.txt" %uuid), "STRAND=NONE",
                "REF_FLAT=%s" %ref_flat, "VALIDATION_STRINGENCY=LENIENT", "TMP_DIR=%s" %tmp_dir]
        pipelineUtil.log_function_time("RNAseq_metrics", uuid, cmd, logger)
    else:
        raise Exception("Invalid path to picard or bam")

def bam_index(bam_file, uuid, logger=None):
    """ Index the resultant post alignment BAM file """

    if os.path.isfile(bam_file):
        cmd = ['samtools', 'index', '-b', bam_file]
        pipelineUtil.log_function_time("BamIndex", uuid, cmd, logger)
    else:
        raise Exception("invalid bam file")
    assert(os.path.isfile('%s.bai' %bam_file))

def reorder_bam(picard_path, bam_file, uuid, outdir, ref_genome, logger=None):
    """ Reorder the BAM file according to the reference genome """

    if os.path.isfile(bam_file) and os.path.isfile(picard_path) and os.path.isfile(ref_genome):
        outbam = os.path.join(outdir, '%s.reorder.bam' %uuid)
        tmp_dir = os.path.join(outdir, 'tmp')
        if not os.path.isdir(tmp_dir):
            os.mkdir(tmp_dir)
        cmd = ['java', '-jar', picard_path, 'ReorderSam', 'I=%s' %bam_file, 'O=%s' %outbam, 'R=%s' %ref_genome,
                'VALIDATION_STRINGENCY=LENIENT', 'TMP_DIR=%s' %tmp_dir]
        pipelineUtil.log_function_time("picard_reorder_sam", uuid, cmd, logger)
    else:
        raise Exception("invalid bam, picard path or reference genome")
    return outbam

def rna_seq_qc(rna_seq_qc_path, bam_file, uuid, outdir, ref_genome, gtf, logger=None):
    """ Perform RNA-seqQC on post alignment BAM file """

    if os.path.isfile(bam_file) and os.path.isfile(rna_seq_qc_path) and os.path.isfile(gtf):
        cmd = ['java', '-jar', rna_seq_qc_path, '-o', outdir, '-r', ref_genome, '-s',
                '%s|%s|%s' %(uuid, bam_file, uuid), '-t', gtf]
        pipelineUtil.log_function_time('RNAseq_qc', uuid, cmd, logger)
    else:
        raise Exception("Invalid path to rnaseq-qc or bam")
"""
picard_path="/home/ubuntu/tools/picard-tools-1.136/picard.jar"
bam_file="/home/ubuntu/SCRATCH/test_1/trial.reorder.bam"
outdir="/home/ubuntu/SCRATCH/test_1"
ref_flat="/home/ubuntu/gencode.v21.annotation.ref_flat_final"
uuid = "4bcf3463-ea9c-414e-a1f5-948f72477602"
ref_genome = "/home/ubuntu/SCRATCH/grch38/with_decoy/bowtie2_2/bowtie2_buildname.fa"
gtf = "/home/ubuntu/SCRATCH/grch38/gencode.v21.annotation.gtf"
rna_seq_qc_path = "/home/ubuntu/tools/RNA-SeQC_v1.1.8.jar"
#validate_bam_file(picard_path, bam_file, "4bcf3463-ea9c-414e-a1f5-948f72477602", outdir)
#collect_rna_seq_metrics(picard_path, bam_file, uuid, outdir, ref_flat)
reordered_bam = reorder_bam(picard_path, bam_file, outdir, ref_genome)
bam_index(reordered_bam, uuid)
rna_seq_qc(rna_seq_qc_path, reordered_bam, uuid, outdir, ref_genome, gtf)
"""
