import argparse
from datetime import datetime
import json
import os
import pandas as pd
import subprocess
from pathlib import Path
import pytz
import re
import copy

G5K_INFO_FILE = "cluster_info.json"


def mkdir(dir):
    Path(dir).mkdir(parents=True, exist_ok=True)
    return


def create_json_oarstat(start_date, stop_date, out_dir="outputs/"):

    # Folder where to record json files for the OAR log
    dir_oar = os.path.join(out_dir, "oar/")
    mkdir(dir_oar)

    # Path to file json where to record the data
    path_oar = os.path.join(dir_oar, f"jobs_{start_date}_{stop_date}.json")
    path_tmp = os.path.join(
        dir_oar, f'tmp_{start_date.replace(" ","_")}_{stop_date.replace(" ","_")}.json'
    )

    # Record all oarstat (jobs, resources, ...) happend between start_time and end_time
    if not os.path.exists(path_oar):
        command = f'oarstat -g "{start_date},{stop_date}" -J > {path_tmp}'
        subprocess.run(command, shell=True)
        
        # Read the oarstat file and extract only the jobs dictionnary (reduce memory size)
        with open(path_tmp, "r") as f:
            data = json.load(f)
            jobs = data["jobs"]

        with open(path_oar, "w") as f:
            json.dump(jobs, f)

        command = f"rm {path_tmp}"
        subprocess.run(command, shell=True)

    return path_oar


def get_info_json_jobid(job_id, dir_jobs):

    # Load Grid5k info (useful for nb_gpu)
    with open(G5K_INFO_FILE, "r") as fp:
        CLUSTERS_INFO_GPU = json.load(fp)["CLUSTERS_INFO_GPU"]

    # Define the path of the json file for this job ID
    path_job_json = os.path.join(dir_jobs, f"{job_id}.json")

    # If the file doesn't exist, create it
    if not os.path.exists(path_job_json):
        command = f"oarstat -fj {job_id} -J > {path_job_json}"
        subprocess.run(command, shell=True)

    # Define the path of the json file for this job ID
    path_job_json = os.path.join(dir_jobs, f"{job_id}.json")

    # read the information of the job
    with open(path_job_json) as j:
        job_json = json.load(j)

        # Extract relevant fields
        node = job_json[job_id]["assigned_network_address"][0].split(".")[0]
        cluster = node.split("-")[0]
        request = job_json[job_id]["initial_request"]
        directory = job_json[job_id]["launching_directory"]
        user = job_json[job_id]["owner"]

        wanted_resources = job_json[job_id]["wanted_resources"]
        match_gpu = re.match(r".*gpu=(\d+).*", wanted_resources)
        if cluster in CLUSTERS_INFO_GPU.keys():
            if match_gpu:
                nb_gpu = int(match_gpu.group(1))
            else:
                nb_gpu = CLUSTERS_INFO_GPU[cluster]["nb_gpu"]
        else:
            nb_gpu = 0

        # Dates (and converted)
        start_timestamp = job_json[job_id]["start_time"]
        start_readable = datetime.fromtimestamp(start_timestamp).strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        )
        stop_timestamp = job_json[job_id]["stop_time"]
        stop_readable = datetime.fromtimestamp(stop_timestamp).strftime(
            "%Y-%m-%dT%H:%M:%S%z"
        )

    return (
        node,
        cluster,
        request,
        directory,
        user,
        nb_gpu,
        start_timestamp,
        stop_timestamp,
        start_readable,
        stop_readable,
    )


def create_load_bmc_file(
    node, job_id, start_date_job, stop_date_job, dir_bmc="outputs/bmc/"
):

    path_bmc = os.path.join(dir_bmc, f"{job_id}.csv")

    if not os.path.exists(path_bmc):
        url = f"https://api.grid5000.fr/stable/sites/nancy/metrics?nodes={node}&metrics=bmc_node_power_watt&start_time={start_date_job}&end_time={stop_date_job}"
        header = "timestamp,device_id,metric_id,value,labels"
        command = f"{{ echo {header}; curl \"{url}\"| jq -r '.[] | [.timestamp, .device_id, .metric_id, .value, .labels|tostring] | @csv'; }} > {path_bmc}"
        subprocess.run(command, shell=True)

    df_bmc = pd.read_csv(path_bmc)

    return df_bmc


def update_bmc(df_bmc, job_id, nb_gpu, jobs_same_node, dir_jobs="outputs/jobs/"):

    # Create a copy of df_bmc
    df_gate = copy.deepcopy(df_bmc)

    # Initialize a 'gate' column in the copy, default is nb_gpu (meaning no overlap)
    df_gate["gate"] = nb_gpu

    # Iterate over jobs on the same node
    for other_job_id, other_job_info in jobs_same_node.items():
        if other_job_id != job_id:  # Only process other jobs, not the current one

            _, _, _, _, _, nb_other_gpu, _, _, start_readable, stop_readable = (
                get_info_json_jobid(other_job_id, dir_jobs)
            )

            df_gate.loc[
                (df_gate["timestamp"] >= start_readable)
                & (df_gate["timestamp"] <= stop_readable),
                "gate",
            ] += nb_other_gpu

    # Apply the gate to the BMC power values (multiply power values with the gate)
    df_bmc["value"] = df_bmc["value"] * nb_gpu / df_gate["gate"]

    return df_bmc


def create_df_jobinfo(list_job, out_dir="outputs/"):

    # Folder where to store json files for each job ID
    dir_jobs = os.path.join(out_dir, "jobs/")
    mkdir(dir_jobs)

    # Initialize an empty list to store rows of data
    rows = []

    # Iterate through the job IDs in the list
    for job_id in list_job:

        # Get job info
        node, _, request, directory, _, _, _, _, start_readable, stop_readable = (
            get_info_json_jobid(job_id, dir_jobs)
        )

        # Append the data as a row
        rows.append(
            {
                "job_id": job_id,
                "node": node,
                "directory": directory,
                "start_date": start_readable,
                "stop_date": stop_readable,
                "request": request,
            }
        )

    # Create a DataFrame from the collected rows
    dataframe = pd.DataFrame(rows)

    return dataframe


def record_joblist(user, jobs_all, out_dir="outputs/"):

    # Folder where to store user-specific csv data
    dir_user = os.path.join(out_dir, "csv", user)
    mkdir(dir_user)

    # Collect job data for these specific jobs IDs
    jobs_ids = [i for i, j_inf in jobs_all.items() if j_inf["owner"] == user]

    # Store this data
    user_df = create_df_jobinfo(jobs_ids, out_dir)
    user_df.to_csv(os.path.join(dir_user, f"jobs_{start_exp}_{stop_exp}.csv"))

    return jobs_ids


def get_bmc_powerprofile(
    user,
    jobs_ids,
    jobs_all,
    start_exp,
    stop_exp,
    out_dir="outputs/",
    tight_bmc_bound=False,
):

    # Ensure start_date_exp and stop_date_exp are timezone-aware with the correct timezone
    # (UTC+02:00 corresponds to 'Europe/Paris' during summer)
    timezone = pytz.timezone("Europe/Paris")
    start_exp_tz = pd.to_datetime(start_exp).tz_localize("UTC").tz_convert(timezone)
    stop_exp_tz = pd.to_datetime(stop_exp).tz_localize("UTC").tz_convert(timezone)

    # Folder where to store files for each job ID and BMC files
    dir_jobs = os.path.join(out_dir, "jobs/")
    mkdir(dir_jobs)
    dir_bmc = os.path.join(out_dir, "bmc/")
    mkdir(dir_bmc)

    # Folder where to store user-specific csv data
    dir_user = os.path.join(out_dir, "csv", user)
    mkdir(dir_user)

    df_user = []
    for job_id in jobs_ids:

        # Get job info
        (
            node,
            _,
            _,
            _,
            _,
            nb_gpu,
            start_timestamp,
            stop_timestamp,
            start_readable,
            stop_readable,
        ) = get_info_json_jobid(job_id, dir_jobs)

        # Get the BMC data from the job ID information (node, dates, etc.)
        df_bmc = create_load_bmc_file(
            node, job_id, start_readable, stop_readable, dir_bmc
        )

        df_bmc["timestamp"] = pd.to_datetime(
            df_bmc["timestamp"], format="ISO8601", utc=True
        )

        # Check if there were some other jobs on the same node
        jobs_same_node = {
            other_job_id: job_info
            for other_job_id, job_info in jobs_all.items()
            if (job_info["network_address"][0].split(".")[0] == node)
            and (
                # Case 1: The other job starts during this job
                (start_timestamp <= job_info["start_time"] < stop_timestamp)
                or
                # Case 2: The other job ends during this job
                (start_timestamp < job_info["stop_time"] <= stop_timestamp)
                or
                # Case 3: This job is completely contained within the other job
                (
                    job_info["start_time"] <= start_timestamp
                    and job_info["stop_time"] >= stop_timestamp
                )
            )
        }

        # if the job is not alone on the node
        if len(jobs_same_node) > 1:
            df_bmc = update_bmc(df_bmc, job_id, nb_gpu, jobs_same_node, dir_jobs)
            path_bmc_gated = os.path.join(dir_bmc, f"{job_id}_gated.csv")
            df_bmc.to_csv(path_bmc_gated)
            print(f"GATED {job_id}")

        df_bmc_resampled = (
            df_bmc.set_index("timestamp").resample("1min")["value"].mean().reset_index()
        )

        df_user.append(df_bmc_resampled)
        #df_user = pd.concat([df_user, df_bmc_resampled], ignore_index=False)

    if not all([df.empty for df in df_user]):
        df_user = pd.concat([df for df in df_user if not df.empty])

        # After processing all jobs, combine all the updated BMC values
        df_user = df_user.groupby("timestamp")["value"].sum().reset_index()
        df_user.set_index("timestamp", inplace=True)

        # Filter jobs that started / stopped outside experiment date
        if tight_bmc_bound:
            df_user = df_user[
                (df_user.index >= start_exp_tz) & (df_user.index <= stop_exp_tz)
            ]

        # Record
        df_user.to_csv(os.path.join(dir_user, f"bmc_{start_exp_tz}_{stop_exp_tz}.csv"))

    return


def collect_exp(
    user_list,
    start_exp,
    stop_exp,
    out_dir="outputs/",
    compute_bmc=True,
    tight_bmc_bound=False,
):

    # Create json file for the whole period
    print(f"----- Collecting jobs from the {start_exp} to the {stop_exp}")
    path_oar = create_json_oarstat(start_exp, stop_exp, out_dir)
    print("done")

    # Load the lsit of all jobs
    print(f"----- Load list of jobs")
    with open(path_oar, "r") as f:
        jobs_all = json.load(f)
    print(f"Number of jobs in total = {len(jobs_all)}")

    for user in user_list:
        print(f"----- Process data for user {user}")
        # Record job list for each user
        jobs_ids = record_joblist(user, jobs_all, out_dir)
        print(f"Number of jobs for user {user} = {len(jobs_ids)}")

        # Get the BMC power profile
        if compute_bmc:
            print(f"Compute BMC / create power profile")
            get_bmc_powerprofile(
                user,
                jobs_ids,
                jobs_all,
                start_exp,
                stop_exp,
                out_dir=out_dir,
                tight_bmc_bound=tight_bmc_bound,
            )

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_list", type=str, default="pmagron")
    parser.add_argument("--start_exp", type=str, default="2026-07-21 00:00:00")
    parser.add_argument("--stop_exp", type=str, default="2026-08-13 07:59:59")
    parser.add_argument("--out_dir", type=str, default="outputs/")
    args = parser.parse_args()

    user_list = args.user_list.split(',')
    start_exp = args.start_exp
    stop_exp = args.stop_exp
    out_dir = args.out_dir

    # Process job data from the start to stop of the exp
    collect_exp(user_list, start_exp, stop_exp, out_dir=out_dir, tight_bmc_bound=False)

# EOF
