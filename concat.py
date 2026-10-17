import os
import pandas as pd
import json
import argparse

# Load Grid5k info
G5K_INFO_FILE = "cluster_info.json"
with open(G5K_INFO_FILE, "r") as fp:
    CLUSTERS_INFO_GPU = json.load(fp)["CLUSTERS_INFO_GPU"]


def concat_all_job_files_usr(user, out_dir):

    df_all = pd.DataFrame()
    dir_user = os.path.join(out_dir, "per_user", user)

    for _, _, files in os.walk(dir_user, topdown=False):
        for name in files:
            if "jobs_" in name:  # ignore bmc files here

                # Load the data
                df = pd.read_csv(os.path.join(dir_user, name), index_col="Unnamed: 0")

                if not (df.empty):
                    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
                    df["stop_date"] = pd.to_datetime(df["stop_date"], errors="coerce")

                    # Compute time difference and add as a column
                    df["time"] = df["stop_date"] - df["start_date"]

                    # Extract cluster from node
                    df["cluster"] = df["node"].str.rsplit("-", n=1).str[0]
                    df["cluster"] = df["node"].str.rsplit("-", n=1).str[0]

                    # Add to overall list
                    df_all = pd.concat([df_all, df], ignore_index=True)

    df_all.sort_values(by=["job_id"], inplace=True)

    # Remove duplicates (jobs that run on multiple exp. time window)
    df_all.drop_duplicates(subset=["job_id"], inplace=True)
    df_all.reset_index(inplace=True, drop=True)
    print(df_all.cluster.value_counts())

    # Only keep jobs on actual known nodes
    df_all = df_all[df_all["cluster"].isin(CLUSTERS_INFO_GPU.keys())]

    # Record
    df_all.to_csv(os.path.join(out_dir, f"jobs_{user}.csv"))

    print(f"Total number of jobs for user {user} = {len(df_all)}")

    return


def concat_bmc_usr(user, out_dir):

    year_consumption = pd.DataFrame()
    dir_user = os.path.join(out_dir, "per_user", user)

    for _, _, files in os.walk(dir_user, topdown=False):
        for name in files:
            if "bmc_" in name:  # ignore jobs files here

                # Load the data
                df_month = pd.read_csv(os.path.join(dir_user, name))

                if not (df_month.empty):

                    # Ensure the 'timestamp' column is treated as the index with DatetimeIndex
                    df_month["timestamp"] = pd.to_datetime(
                        df_month["timestamp"], utc=True
                    )
                    df_month.set_index("timestamp", inplace=True)  # Set as index
                    time_interval_s = 60
                    energy_kwh = (
                        df_month["value"] * time_interval_s / 3600
                    ) / 1000  # Convert Wh to kWh

                    # Resample to daily frequency and sum the energy values for each day
                    daily_consumption = energy_kwh.resample("D").sum()

                    # Add daily consumption data to year_consumption DataFrame
                    daily_consumption = daily_consumption.to_frame(
                        name="daily_kwh"
                    )  # Make sure it's a DataFrame

                    daily_consumption["timestamp"] = daily_consumption.index
                    year_consumption = pd.concat(
                        [year_consumption, daily_consumption], ignore_index=True
                    )

    # Set the index of the year_consumption to timestamp and plot yearly data
    year_consumption.sort_values(by="timestamp", inplace=True)
    year_consumption.set_index("timestamp", inplace=True)
    year_consumption.to_csv(os.path.join(out_dir, f"bmc_{user}.csv"))

    yearly_totals = year_consumption["daily_kwh"].sum()
    yearly_daily_mean = year_consumption["daily_kwh"].mean()

    print(f"Total consumption = {yearly_totals} kW")
    print(f"Average daily consumption = {yearly_daily_mean} kW")

    return


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_list", type=str, default="pmagron")
    parser.add_argument("--out_dir", type=str, default="outputs/")
    args = parser.parse_args()

    user_list = args.user_list.split(",")
    out_dir = args.out_dir

    for user in user_list:
        print(f"------ Concatenate all jobs for user {user}")
        concat_all_job_files_usr(user, out_dir=out_dir)

        print(f"------ Concatenate BMC for user {user}")
        concat_bmc_usr(user, out_dir=out_dir)

# EOF
