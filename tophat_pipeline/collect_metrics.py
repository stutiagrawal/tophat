import argparse
import os

def add_to_dict(line, dictionary):
    line = line.split("\t")
    analysis_id = line[1]
    time = line[2]
    if analysis_id not in dictionary:
        dictionary[analysis_id] = 0
    dictionary[analysis_id] += float(time)
    return dictionary

def write_to_file(f_ptr, dictionary):
    for analysis_id in dictionary:
        f_ptr.write("%s\t%s\n" %(analysis_id, dictionary[analysis_id]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='collect_metrics.py', description='Collect Metrics from node')
    required = parser.add_argument_group("Required Input Parameters")
    required.add_argument('--target_dir', default='/home/ubuntu/SCRATCH', help='target directory')
    required.add_argument('--node_name', default=None, help='Name of node')
    args = parser.parse_args()

    target_dir = args.target_dir
    output_dir = "/home/ubuntu/logs"

    t_out = open(os.path.join("%s" %(output_dir), "tophat_%s" %(args.node_name)), "w")
    s_out = open(os.path.join("%s" %(output_dir), "samtools_%s" %(args.node_name)), "w")

    tophat = dict()
    samtools = dict()

    for dirname in os.listdir(target_dir):
        subdir = os.path.join(target_dir, dirname)
        if os.path.isdir(subdir):
            for filename in os.listdir(subdir):
                if filename.endswith(".log"):
                    filename = os.path.join(subdir, filename)
                    #print filename
                    f = open(filename, "r")
                    for line in f:
                        if "TOPHAT_TIME" in line:
                            tophat = add_to_dict(line, tophat)
                        if "SAMTOOLS_TIME" in line:
                            samtools = add_to_dict(line, samtools)
                            #outfile.write(line)
    write_to_file(t_out, tophat)
    write_to_file(s_out, samtools)
    t_out.close()
    s_out.close()
