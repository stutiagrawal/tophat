import os
import argparse
import multiprocessing
#test downloads and upload from cleversafe
def retrieve_fastq_files(analysis_id, cghub_key, output_dir):
    if not os.path.isdir(os.path.join(output_dir, analysis_id)):
        os.system("gtdownload -v -c %s -p %s %s" %(cghub_key, output_dir, analysis_id))

def upload_to_cleversafe(filename, bucket):
    filepath = filename.split("/")
    if(len(filepath) > 2):
        analysis_id = filepath[len(filepath)-2]
        tarball = filepath[len(filepath)-1]
        upload_name = os.path.join(bucket, analysis_id, tarball)
        print "Uploading %s..." %(upload_name)
        os.system("s3cmd put %s %s" %(filename, upload_name))
        print "Upload complete"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='cleversafe.py', description='RNA-seq alignment using TopHat')
    parser.add_argument('--outdir', help='path to output directory', default=os.getcwd())
    parser.add_argument('--cghub', help='path to cghub key', default="/home/ubuntu/keys/cghub.key")
    parser.add_argument('--p', help='number of threads', default = int(0.8 * multiprocessing.cpu_count()))
    parser.add_argument('--analysis_id_file', help='path to analysis id file')
    parser.add_argument('--bucket', help='Name of the S3 bucket')
    args = parser.parse_args()

    fp = open(args.analysis_id_file, "r")
    for analysis_id in fp:
        analysis_id = analysis_id.rstrip()
        retrieve_fastq_files(analysis_id, args.cghub, args.outdir)
        for filename in os.listdir(os.path.join(args.outdir, analysis_id)):
            if (filename.endswith(".tar") or filename.endswith(".tar.gz") or filename.endswith(".tar.bz")):
                upload_to_cleversafe(os.path.join(args.outdir, analysis_id, filename), args.bucket)

