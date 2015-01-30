import os
import argparse

def retrieve_data(analysis_id, cghub_key, output_dir):
    if not os.path.isdir(os.path.join(output_dir, analysis_id)):
        os.system("gtdownload -v -c %s -p %s %s" %(cghub_key, output_dir, analysis_id))

def download_from_cleversafe(bucket, analysis_id, outdir):
    filename_on_cleversafe = os.path.join(bucket, analysis_id)
    analysis_dir = os.path.join(outdir, analysis_id)
    if not os.path.isdir(analysis_dir):
        os.mkdir(analysis_dir)
    os.system("s3cmd sync %s %s" %(filename_on_cleversafe, analysis_dir))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='test_tophat_pipeline.py')
    parser.add_argument('list_of_analysis_id', help='path to file containing analysis ids')

    args = parser.parse_args()

    index = '/home/ubuntu/SCRATCH/grch38/with_decoy/transcriptome_index'
    genome_annotation = '/home/ubuntu/SCRATCH/grch38/gencode.v21.annotation.gtf'
    bowtie2_build_basename = '/home/ubuntu/SCRATCH/grch38/with_decoy/bowtie2_2/bowtie_2_build'
    output_dir = '/home/ubuntu/SCRATCH/'
    cghub_key = '/home/ubuntu/keys/cghub.key'

    analysis_handle = open(args.list_of_analysis_id, "r")
    for analysis_id in analysis_handle:
        analysis_id = analysis_id.rstrip()
        #retrieve_data(analysis_id, cghub_key, output_dir)

        outdir = os.path.join(output_dir, analysis_id)
        tmp_dir = os.path.join(outdir, "tophat_tmp")
        tarfile = ""
        for filename in os.listdir(outdir):
            if filename.endswith(".tar") or filename.endswith(".gz") or filename.endswith(".bz"):
                tarfile = os.path.join(outdir, filename)
        if tarfile != "":
            os.system('python align_tophat.py %s %s %s %s %s %s --outdir %s' %(tarfile, index, genome_annotation,
                                                                tmp_dir, analysis_id, bowtie2_build_basename,
                                                                outdir))
