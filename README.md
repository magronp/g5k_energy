# Collecting Energy from Grid5000 Jobs

This repository allows users of the [Grid5000 platform](https://www.grid5000.fr/w/Grid5000) to collect the list of jobs and estimate energy for any user/project, using the [Kwollect API](https://www.grid5000.fr/w/Monitoring_Using_Kwollect). This code supports [our paper](https://arxiv.org/abs/2610.01619), which considers specifically audio projects from the [Multispeech](https://team.inria.fr/multispeech/home/) research team of [LORIA](https://www.loria.fr/en/loria/), France.


## Setup
Start by cloning this repository, creating/activating a virtual environment, and installing the required package (pandas and numpy):

```
git clone git@github.com:magronp/g5k_energy.git
cd g5k_energy/
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

##  Collecting jobs (and BMC)

Note: the following will work only if you're connected to the Grid5000 frontend.

### Basic usage

If you want to collect jobs (and the corresponding BMC) on a short period of time (about 1 month), you can directly run:
```
python collect_exp.py --start_exp "2023-04-03 00:00:00" --stop_exp "2023-04-28 23:59:59" --user_list <user1>,<user2>,...,<userN>
```
(note that the list of users must be separated with commas, no space)

This will create one folder per user `outputs/csv/<user>/` containing both the list of jobs and the BMC on ths period, for this user. Note that the BMC is tracked by default, but you can disable it with a flag: `--bmc False`.

If you do this multiple times on different time periods and then want to concatenate all job information into a single file, run:
```
python concat.py --user_list <user1>,<user2>,...,<userN>
```
It will create a file `outputs/jobs_<user>.csv` for each user.


### Collecting jobs on a long period of time

If the time period is longer than about a month, you might need to slice it into smaller chunks, otherwise the process will likely be killed. Then you need to concatenate the results as above.

We automate that with the `run.sh` shell script, that you can simply run as follows:

```
./run.sh start_exp="2023-03-13 00:00:00" stop_exp="2026-10-15 23:59:59" user_list=<user1>,<user2>,...,<userN> timestep=10
```

where the `timestep` parameter controls the chunk duration, in days. Note that a more efficient way of collecting jobs could be implemented using the potgresSQL client, as indicated [here](https://www.grid5000.fr/w/Advanced_OAR#OAR_database_logs). We leave it to future work.


### Collecting team-level data

The above scripts work also is using a *team* instead of a *user*. For instance, to track the job/BMC for the Multispeech team, as in [our paper](https://arxiv.org/abs/2610.01619), you can run:

```
./run.sh start_exp="2023-09-01 00:00:00" stop_exp="2024-12-31 23:59:59" user_list=multispeech timestep=10
```


## Estimating energy

Once the list of job is obtained over a period of time for a list of users, you should have a file `outputs/jobs_<user>.csv` for each user, as per above. At this point, you might want to do a bit of filtering, e.g., to only keep jobs for a given user corresponding to a certain *project* (for instance, based on the launching `directory`, whose name might be indicative of a project). Likewise, you might also want to allocate jobs a certain *weight*: for instance, if a job is useful to many projects (e.g., some heavy dataset pre-processing, or training a model that's used in multiple projects), you might want to divide its energy toll across corresponding projects.

Then, to get all energy estimates using our methodology, run the following script:
```
python compute_nrj.py --user_list <user1>,<user2>,...,<userN>
```
This will create a file `outputs/jobs_<user>_energy.csv` for each user. It will also display the total energy (in terms of MLC02, green algorithm, and BMC).


## Visualization

Running the `visualization.ipynb` notebook will display the BMC energy over days for a given user (i.e., Figure 2 in our paper).


## Reference

If you use this code, please consider citing ou paper.

```latex
@misc{Douwes2026,  
  author={Constance Douwes and Paul Magron and Romain Serizel},  
  title={Exposing the Cost of Deep Learning Audio Development},
  url = {https://arxiv.org/abs/2610.01619},
  year = {2026}
}
```