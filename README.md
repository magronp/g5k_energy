# Collecting jobs from Grid5000 API using Kwollect

## Setup
Start by cloning this repository, creating/activating a virtual environment, and installing the required package (pandas and numpy):

```
git clone git@github.com:magronp/g5k-energy.git
cd g5k-energy/
pip install -r requirements.txt
```

##  How to use

### Basic usage

If you want to collect jobs on a short period of time (less than 1 month), you can directly run:
```
python collect_exp.py --start_exp "2023-04-03 00:00:00" --stop_exp "2023-04-28 23:59:59" --user_list <user1>,<user2>,...,<userN>
```
(note that the list of users must be separated with commas, no space)

This will create one folder per user `outputs/csv/<user>/` containing both the list of jobs and the BMC on ths period, for this user.

If you do this multiple times on different time periods and then want to concatenate all job information into a single file, run:
```
python concat.py --user_list <user1>,<user2>,...,<userN>
```
It will create a file `outputs/<user>.csv`.


### Collecting jobs on a long period of time

Otherwise, need to slice the time period into chunks of 1 month, and run the command multiple times. This is assembled in the shell script:

```
./run.sh start_exp="2023-03-13 00:00:00" stop_exp="2026-07-31 23:59:59" user_list=<user1>,<user2>,...,<userN>
```
