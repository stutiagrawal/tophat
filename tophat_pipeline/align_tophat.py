import pipelineUtil
import logging
import argparse
import os
import setupLog
import time
import multiprocessing
import subprocess
import glob
import re
import xml.etree.ElementTree as ET
import qc
import post_alignment_qc

def get_xml(dirname, analysis_id, logger):

    print "Downloading XML"
    print "Analysis ID = %s" % analysis_id
    xml_file = "%s.xml" %os.path.join(dirname, analysis_id)
    cmd = ['cgquery', '-o' , xml_file, 'analysis_id=%s' %analysis_id]
    pipelineUtil.log_function_time('cgquery', analysis_id, cmd, logger)

    return xml_file

def get_value_from_tree(result, field):
    if not (result == None):
        if not (result.find(str(field)) == None):
            field_value = result.find(str(field)).text
            if field_value == None:
                return ""
            else:
                return field_value
    else:
        raise Exception("Empty result from XML")

def extract_metadata(dirname, xml_file, logger):

    #Download the xml file
    #xml_file = get_xml(dirname, analysis_id, logger)

    #Parse XML to get required fields
    tree = ET.parse(xml_file)
    root = tree.getroot()
    metadata = dict()
    for result in root.iter("Result"):
        metadata["participant_id"] = get_value_from_tree(result, "participant_id")
        metadata["sample_id"] = get_value_from_tree(result, "sample_id")
        metadata["disease"] = get_value_from_tree(result, "disease")
        metadata["tss_id"] = get_value_from_tree(result, "tss_id")
        metadata["library_strategy"] = get_value_from_tree(result, "library_strategy")
        metadata["analyte_code"] = get_value_from_tree(result, "analyte_code")
        metadata["sample_type"] = get_value_from_tree(result, "sample_type")
        metadata["platform"] = get_value_from_tree(result, "platform")
        metadata["aliquot_id"] = get_value_from_tree(result, "aliquot_id")

    os.remove(xml_file)
    return metadata

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

def decompress(filename, workdir, analysis_id, logger):
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
    pipelineUtil.log_function_time("tar", analysis_id, cmd, logger)


def tophat_paired(args, rg_id_dir, rg_id, reads_1, reads_2, logger):
    """ Perform tophat on paired end data and fix mate information """

    print "Aligning using TopHat"

    cmd = ['time', '/usr/bin/time', 'tophat2', '-p', '%s' %args.p,
            '--library-type=%s' %args.library_type,
            '--segment-length', '%s' %args.segment_length,
            '--no-coverage-search',
            '--min-intron-length', '%s' %args.min_intron_length,
            '-G', args.genome_annotation,
            '--max-multihits', '%s' %args.max_multihits,
            '--mate-inner-dist', '%s' %args.mate_inner_dist,
            '--mate-std-dev', '%s' %args.mate_std_dev,
            '--fusion-search',
            '--fusion-min-dist', '%s' %args.fusion_min_dist,
            '--tmp-dir', args.tmp_dir,
            '-o', rg_id_dir,
            '--transcriptome-index', args.transcriptome_index,
            '--rg-id', rg_id,
            '--rg-sample', args.sample_id,
            args.bowtie2_build_basename,
            reads_1, reads_2
            ]
    pipelineUtil.log_function_time('TOPHAT', args.id, cmd, logger)

def downstream_steps(output_dir, analysis_id, read_groups, logger):
    """ merge and sort unmapped reads with mapped reads """

    out_file_basename = os.path.join(output_dir, analysis_id)
    merge_cmd = ['time', '/usr/bin/time', 'samtools', 'merge', '-',]
    for rg_id in read_groups:

        rg_id_dir = os.path.join(output_dir, rg_id)
        mapped_reads = os.path.join(rg_id_dir, 'accepted_hits.bam')
        unaligned_reads = os.path.join(rg_id_dir, 'unmapped.bam')
        unmapped_reads = post_alignment_qc.add_or_replace_read_group(args.picard, unaligned_reads,
                                                                    rg_id_dir, rg_id, rg_id, logger=logger)
        if os.path.isfile(mapped_reads):
            merge_cmd.append(mapped_reads)
        if os.path.isfile(unmapped_reads):
            merge_cmd.append(unmapped_reads)

    sort_cmd = ['samtools', 'sort','-', out_file_basename]
    start_time = time.time()
    merge = subprocess.Popen(merge_cmd, stdout=subprocess.PIPE)
    sort = subprocess.check_output(sort_cmd, stdin=merge.stdout)
    end_time = time.time()
    logger.info("SAMTOOLS_TIME:%s\t%s" %(analysis_id, (end_time-start_time)/60.0))
    final_bam = '%s.bam' %out_file_basename
    if not os.path.isfile(final_bam):
        raise Exception("Could not merge/sort or find the BAM files")
    return final_bam

def post_aln_qc(args, bam_file, logger=None):
    """ perform post alignment quality check """

    #validate the post-alignment BAM file
    post_alignment_qc.validate_bam_file(args.picard, bam_file, args.id, args.outdir, logger)

    #collect RNA-seq metrics
    post_alignment_qc.collect_rna_seq_metrics(args.picard, bam_file, args.id,
                                                args.outdir, args.ref_flat, logger)

    #run rna_seq_qc from broad institute
    reordered_bam = post_alignment_qc.reorder_bam(args.picard, bam_file, args.id, args.outdir,
                                                args.ref_genome, logger)
    post_alignment_qc.bam_index(reordered_bam, args.id, logger)
    post_alignment_qc.rna_seq_qc(args.rna_seq_qc_path, reordered_bam, args.id, args.outdir, args.ref_genome,
                args.genome_annotation, logger)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='align_tophat.py', description='RNA-seq alignment using TopHat')
    required = parser.add_argument_group("Required input parameters")
    required.add_argument('--tarfile', default=None, help='Input file containing sequence information',
                          required=True)
    required.add_argument('--index', default='/home/ubuntu/SCRATCH/grch38/with_decoy/transcriptome_index',
                        help='Directory containing the reference genome index', required=True)
    required.add_argument('--genome_annotation', default='/home/ubuntu/SCRATCH/grch38/gencode.v21.annotation.gtf',
                        help='path to genome annotation file', required=True)
    required.add_argument('--bowtie2_build_basename', help='path to bowtie2_build', required=True)
    required.add_argument('--sample_id', help='sample_id of the sample', required=True)
    required.add_argument('--ref_flat', help='Genome annotations in RefFlat format',
                        default='/home/ubuntu/SCRATCH/grch38/gencode.v21.annotation.ref_flat_final',
                        required=True)
    required.add_argument('--ref_genome', help='Reference genome',
                        default='/home/ubuntu/SCRATCH/grch38/with_decoy/bowtie2_2/bowtie2_buildname.fa',
                        required=True)

    optional = parser.add_argument_group('optional input parameters')
    optional.add_argument('--id', help='id of the sample', default="test")
    optional.add_argument('--outdir', help='path to output directory', default=os.getcwd())
    optional.add_argument('--cghub', help='path to cghub key', default="/home/ubuntu/keys/cghub.key")
    optional.add_argument('--picard', help='path to picard executable',
                        default='/home/ubuntu/tools/picard-tools-1.128/picard.jar')
    optional.add_argument('--fastqc_path', help='path to fastqc', default='/home/ubuntu/bin/FastQC/fastqc')
    optional.add_argument('--metadata_xml', help='metadata in XML format as given by cgquery', default=False)
    optional.add_argument('--rna_seq_qc_path', help='path to RNAseq-QC',
                        default='/home/ubuntu/bin/RNA-SeQC_v1.1.8.jar')


    tophat = parser.add_argument_group("TopHat input parameters")
    tophat.add_argument("--p", type=int, help='No. of threads', default=int(0.8 * multiprocessing.cpu_count()))
    tophat.add_argument("--segment_length", type=int, help='Length of segment', default=20)
    tophat.add_argument("--library_type", type=str, help='Type of library', default='fr-unstranded')
    tophat.add_argument("--no_coverage_search", type=str, help='Coverage search', default='')
    tophat.add_argument("--min_intron_length", type=int, help='Minimum intron length', default=6)
    tophat.add_argument("-G", type=str, help='Path to genome annotation file',
                        default='/home/ubuntu/SCRATCH/grch38/gencode.v21.annotation.gtf')
    tophat.add_argument("--max_multihits", type=int, help="Maximum multihits", default=20)
    tophat.add_argument("--mate_inner_dist", type=int, help="Inner mate distance", default=350)
    tophat.add_argument("--mate_std_dev", type=int, help="Mate standard deviation", default=300)
    tophat.add_argument("--fusion_search", type=str, help="Search for fusions", default='')
    tophat.add_argument("--fusion_min_dist", type=str, help="Minimum fusion distance", default=1000000)
    tophat.add_argument("--tmp_dir", type=str, help="Directory for tmp files", default='/home/ubuntu/SCRATCH/tmp')
    tophat.add_argument("--transcriptome_index", type=str, help="Directory for transcriptome index",
                        default='/home/ubuntu/SCRATCH/grch38/with_decoy/transcriptome_index')
    args = parser.parse_args()

    log_file = "%s.log" % os.path.join(args.outdir, "%s_2" %args.id)

    logger = setupLog.setup_logging(logging.INFO, "%s_2" %args.id, log_file)

    if not os.path.isdir(args.tmp_dir):
        os.mkdir(args.tmp_dir)
    #Unpack the files
    decompress(args.tarfile, args.outdir, args.id, logger)
    #Select the fastq reads
    read_group_pairs = scan_workdir(os.path.join(args.outdir))
    read_groups = list()
    if(args.metadata_xml):
        metadata = extract_metadata(args.outdir, args.metadata_xml, logger)
    #Perform the paired end alignment
    for (rg_id, reads_1, reads_2) in read_group_pairs:
        read_groups.append(rg_id)
        print rg_id, reads_1, reads_2
        rg_id_dir = os.path.join(args.outdir, rg_id)
        if not os.path.isdir(rg_id_dir):
            os.mkdir(rg_id_dir)
        qc.fastqc(args.fastqc_path, reads_1, reads_2, rg_id_dir, rg_id, logger)
        #    print "Passed FASTQC"
        tophat_paired(args, rg_id_dir, rg_id, reads_1, reads_2,logger)
        #else:
        #    logger.info("Failed FastQC for %s and %s" %(reads_1, reads_2))
    #Merge and sort the resulting BAM
    bam_file_name = downstream_steps(args.outdir, args.id, read_groups, logger)
    #Perform QC checks
    post_aln_qc(args, bam_file_name, logger)
    #Remove the reads
    bam_file_name = "%s.bam" % os.path.join(args.outdir, args.id)
    if os.path.isfile(bam_file_name) and os.path.getsize(bam_file_name):
        for (rg_id, reads_1, reads_2) in read_group_pairs:
            pass
            #os.remove(reads_1)
            #os.remove(reads_2)
