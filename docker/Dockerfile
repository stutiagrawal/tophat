FROM ubuntu:14.04
MAINTAINER Stuti Agrawal <stutia@uchicago.edu>
USER root
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --force-yes \
    curl \
    g++ \
    make \
    python \
    libboost-dev \
    libboost-thread-dev \
    libboost-system-dev \
    zlib1g-dev \
    ncurses-dev \
    unzip \
    gzip \
    bzip2 \
    libxml2-dev \
    libxslt-dev \
    python-pip \
    python-dev \
    git \
    s3cmd \
    time \
    wget \
    python-virtualenv

RUN adduser --disabled-password --gecos '' ubuntu && adduser ubuntu sudo && echo "ubuntu    ALL=(ALL)   NOPASSWD:ALL" >> /etc/sudoers.d/ubuntu
ENV HOME /home/ubuntu
USER ubuntu
RUN mkdir ${HOME}/bin
WORKDIR ${HOME}/bin

#install TopHat 2.0.13
RUN wget http://ccb.jhu.edu/software/tophat/downloads/tophat-2.0.13.Linux_x86_64.tar.gz && tar xzvf tophat-2.0.13.Linux_x86_64.tar.gz \

#install Bowtie2-2.2.2
&& wget http://sourceforge.net/projects/bowtie-bio/files/bowtie2/2.2.2/bowtie2-2.2.2-linux-x86_64.zip && unzip bowtie2-2.2.2-linux-x86_64.zip \

#install FastQC 0.11.2
&& wget http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.11.2.zip && unzip fastqc_v0.11.2.zip && chmod +x FastQC/fastqc \

#download genetorrent
&& wget https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/genetorrent-common_3.8.7-ubuntu2.207-14.04_amd64.deb \
&& wget https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/genetorrent-download_3.8.7-ubuntu2.207-14.04_amd64.deb \

#remove the compressed files
&& rm *.gz *.zip

USER root
RUN dpkg -i --force-depends ${HOME}/bin/genetorrent-*.deb \
    && apt-get update \
    && apt-get -f install -y

RUN pip install s3cmd --user
ENV rna_seq 0.02
RUN git clone https://github.com/stutiagrawal/tophat.git
ENTRYPOINT ["/bin/bash", "-c"]
