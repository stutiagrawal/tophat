import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='build_index.py', description='Build the index for TopHat')
    parser.add_argument('ref', help='path to genome reference')
    parser.add_argument('gtf', help='path to annotation file')
    parser.add_argument('bowtie_buildname', help='path to bowtie built indices')
    parser.add_argument('transcriptome', help='path to transcriptome index')

    args = parser.parse_args()

    print 'Starting TopHat build'

    #os.system('bowtie2-build --offrate 3 %s %s' %(args.ref, args.bowtie_buildname))
    if not os.path.isdir(args.transcriptome):
        os.mkdir(args.transcriptome)
    os.system('tophat2 -G %s --transcriptome-index %s %s' %(args.gtf, args.transcriptome, args.bowtie_buildname))

    print 'TopHat build complete.'
