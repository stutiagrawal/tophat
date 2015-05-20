import os
import argparse
import pipelineUtil

def retrieve_data(analysis_id, cghub_key, output_dir):
    if not os.path.isdir(os.path.join(output_dir, analysis_id)):
        os.system("gtdownload -v -c %s -p %s %s" %(cghub_key, output_dir, analysis_id))

def download_from_cleversafe(bucket, name, outdir):
    filename_on_cleversafe = os.path.join(bucket, name)
    analysis_dir = os.path.join(outdir, name)
    if not os.path.isdir(analysis_dir):
        os.system("s3cmd sync %s %s" %(filename_on_cleversafe, outdir))

def get_reference_build(bucket, refdir):
    ref_build_dir = os.path.join(refdir, "grch38")
    if not os.path.isdir(ref_build_dir):
        download_from_cleversafe(bucket, "grch38", refdir)
    if os.path.isdir(ref_build_dir):
        gtf = os.path.join(ref_build_dir, "gencode.v21.annotation.gtf")
        bowtie = os.path.join(ref_build_dir, "with_decoy", "bowtie2_2")
        transcriptome = os.path.join(ref_build_dir, "with_decoy", "transcriptome_index")
        print gtf
        print bowtie
        print transcriptome
        if not os.path.isfile(gtf) or not os.path.isdir(bowtie) or not  os.path.isdir(transcriptome):
            print "Cannot get reference genome"

def upload_fastqc(bucket, entity_path, read_group, analysis_id, filename):

    mate_1_in = os.path.join(entity_path, "fastqc_results", "%s_1_fastqc" %(read_group),"%s.txt" %filename)
    mate_1_out = os.path.join(bucket, "fastqc_%s"%filename, analysis_id, "%s_1" %read_group)
    mate_2_in = os.path.join(entity_path, "fastqc_results", "%s_2_fastqc" %(read_group), "%s.txt" %filename)
    mate_2_out = os.path.join(bucket, "fastqc_%s" %filename, analysis_id, "%s_2" %read_group)
    if (os.path.isfile(mate_1_in) and os.path.isfile(mate_2_in)):
        pipelineUtil.upload_to_cleversafe(None, mate_1_out, mate_1_in)
        pipelineUtil.upload_to_cleversafe(None, mate_2_out, mate_2_in)

def upload_important_files(bucket, dirname, args):
    for entity in os.listdir(dirname):
        entity_path = os.path.join(dirname, entity)
        if entity.endswith(".log"):
            log_in_path = entity_path
            log_out_path = os.path.join(bucket, 'rna_seq_logs', entity)
            pipelineUtil.upload_to_cleversafe(None, log_out_path, log_in_path)
        if entity.endswith(".bam"):
            bam_in_path = entity_path
            bam_out_path = os.path.join(bucket, args.analysis_id, entity)
            pipelineUtil.upload_to_cleversafe(None, bam_out_path, bam_in_path)
        if os.path.isdir(entity_path):
            read_group = entity
            upload_fastqc(bucket, entity_path, read_group, args.analysis_id, "summary")
            upload_fastqc(bucket, entity_path, read_group, args.analysis_id, "fastqc_data")

            alignment_summary = os.path.join(entity_path, "align_summary.txt")
            alignment_summary_out = os.path.join(bucket, "tophat_summary", "%s_%s.txt" %(args.analysis_id, read_group))
            pipelineUtil.upload_to_cleversafe(None, alignment_summary_out, alignment_summary)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='tophat_elastic_cluster.py')
    parser.add_argument('analysis_id', help='uuid of the analysis')

    args = parser.parse_args()

    index = '/home/ubuntu/SCRATCH/grch38/with_decoy/transcriptome_index'
    genome_annotation = '/home/ubuntu/SCRATCH/grch38/gencode.v21.annotation.gtf'
    bowtie2_build_basename = '/home/ubuntu/SCRATCH/grch38/with_decoy/bowtie2_2/bowtie2_buildname'
    output_dir = '/home/ubuntu/SCRATCH/'
    cghub_key = '/home/ubuntu/keys/cghub.key'
    bucket = 's3://bioinformatics_scratch'
    refdir = '/home/ubuntu/SCRATCH/'
    analysis_id = args.analysis_id

    #download the reference build for tophat
    get_reference_build(bucket, refdir)
        #retrieve_data(analysis_id, cghub_key, output_dir)
    download_from_cleversafe(bucket, analysis_id, output_dir)

    outdir = os.path.join(output_dir, analysis_id)
    tmp_dir = os.path.join(outdir, "tophat_tmp")
    tarfile = ""
    for filename in os.listdir(outdir):
        if filename.endswith(".tar") or filename.endswith(".tar.gz") or filename.endswith(".tar.bz"):
            tarfile = os.path.join(outdir, filename)
    if tarfile != "":
        print tarfile
        #os.system('python /home/ubuntu/tophat/tophat_pipeline/align_tophat.py --tarfile %s --index %s --genome_annotation %s --tmp_dir %s --analysis_id %s --bowtie2_build_basename %s --outdir %s'
         #       %(tarfile, index, genome_annotation, tmp_dir, analysis_id, bowtie2_build_basename,
         #       outdir))
        upload_important_files(bucket, outdir, args)
        pipelineUtil.remove_dir(outdir)
