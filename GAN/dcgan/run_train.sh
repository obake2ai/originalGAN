#!/bin/sh
#PBS -q h-regular
#PBS -l select=1:mpiprocs=4:ompthreads=4
#PBS -W group_list=gj16
#PBS -l walltime=40:00:00 
cd $PBS_O_WORKDIR
. /etc/profile.d/modules.sh
module load keras
python dcgan.py
