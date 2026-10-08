import os
import pandas as pd
import re
import json
import argparse

# Load Grid5k info
G5K_INFO_FILE = "cluster_info.json"
with open(G5K_INFO_FILE, "r") as fp:
    CLUSTERS_INFO_GPU = json.load(fp)["CLUSTERS_INFO_GPU"]


def energy_green_algorithm(cluster, duration, occupation):
    mem_factor = 0.3725
    cluster_info = CLUSTERS_INFO_GPU[cluster]
    tdp_gpu = cluster_info["tdp_gpu"]
    tdp_cpu = cluster_info["tdp_cpu"]
    nb_gpu = cluster_info["nb_gpu"]
    cores_per_cpu = cluster_info["cores_per_cpu"]
    tdp_core = tdp_cpu / cores_per_cpu
    nb_cores = cluster_info["nb_cpu"] * cores_per_cpu
    memory = cluster_info["mem_gb"]

    duration_h = duration / 3600
    power_gpu = tdp_gpu * nb_gpu * occupation
    power_cpu = tdp_core * nb_cores * occupation
    power_mem = memory * mem_factor

    nrj_ga = (power_gpu + power_cpu + power_mem) * duration_h / 1000

    return nrj_ga


def energy_mlco2(cluster, duration, occupation):
    cluster_info = CLUSTERS_INFO_GPU[cluster]
    tdp_gpu = cluster_info["tdp_gpu"]
    nb_gpu = cluster_info["nb_gpu"]

    duration_h = duration / 3600
    power_gpu = tdp_gpu * nb_gpu * occupation
    energy_mlco2 = power_gpu * duration_h / 1000

    return energy_mlco2


def add_energy_csv(df, out_dir="outputs/"):

    # Convert to timedeta
    df["time"] = pd.to_timedelta(df["time"])
    df["nb_gpu"] = 0
    df["energy_GA"] = 0.0
    df["energy_MLCO2"] = 0.0
    for i in df.index:
        job = df["job_id"][i]
        node = df["node"][i]
        cluster = node.split("-")[0]
        duration = df["time"][i].total_seconds()
        target_gpu = re.search(r"gpu=(\d+)", df["request"][i])
        if target_gpu:
            nb_gpu = int(target_gpu.group(1))  # Use the requested GPU count
        else:
            nb_gpu = CLUSTERS_INFO_GPU[cluster]["nb_gpu"]
        df.loc[i, "nb_gpu"] = nb_gpu
        occupation = nb_gpu / CLUSTERS_INFO_GPU[cluster]["nb_gpu"]
        df.loc[i, "energy_GA"] = round(
            energy_green_algorithm(cluster, duration, occupation), 3
        )
        df.loc[i, "energy_MLCO2"] = round(
            energy_mlco2(cluster, duration, occupation), 3
        )

        # Add BMC if available
        path_bmc = os.path.join(out_dir, "bmc", f"{job}.csv")
        path_bmc_gated = os.path.join(out_dir, "bmc", f"{job}_gated.csv")
        if os.path.exists(path_bmc):
            if os.path.exists(path_bmc_gated):
                job_bmc = pd.read_csv(path_bmc_gated)
            else:
                job_bmc = pd.read_csv(path_bmc)
            if len(job_bmc) != 0:
                df.loc[i, "energy_BMC"] = (
                    ((job_bmc["value"] * 5 / 3600) / 1000).sum().astype(float).round(3)
                )

        else:
            df.loc[i, "warning"] = "Waiting for kwollect to repaired"


def compute_nrj(user, out_dir):

    # Read job list
    df = pd.read_csv(os.path.join(out_dir, f"jobs_{user}.csv"), index_col="Unnamed: 0")

    # Compute energy
    df = df[
        ["job_id", "node", "directory", "time", "start_date", "stop_date", "request"]
    ]
    add_energy_csv(df, out_dir=out_dir)
    df.reset_index(inplace=True, drop=True)

    # Record the data
    df.to_csv(os.path.join(out_dir, f"jobs_{user}_energy.csv"))

    # Display a summary
    for metric in ["MLCO2", "GA", "BMC"]:
        print(f"Total {metric} energy = {df["energy_" + metric].sum().item()} kWh")

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_list", type=str, default="pmagron")
    parser.add_argument("--out_dir", type=str, default="outputs/")
    args = parser.parse_args()

    user_list = args.user_list.split(",")
    out_dir = args.out_dir

    for user in user_list:
        print(f"------ Compute energy for all jobs for user {user}")
        compute_nrj(user, out_dir=out_dir)

# EOF
