from datetime import datetime, timedelta
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--start_exp", type=str, default="2025-08-01 00:00:00")
    parser.add_argument("--stop_exp", type=str, default="2026-10-15 23:59:59")
    parser.add_argument("--timestep", type=int, default=10)
    args = parser.parse_args()

    # Start and end of the time period
    timestep = args.timestep
    start_exp = args.start_exp
    stop_exp = args.stop_exp

    start_dt = datetime.strptime(start_exp, "%Y-%m-%d %H:%M:%S")
    stop_dt = datetime.strptime(stop_exp, "%Y-%m-%d %H:%M:%S")
    assert start_dt < stop_dt

    # File where to record the list of time chunks
    dt_path = "dt_list.txt"

    # Add an interval
    curr_st = start_dt
    curr_end = start_dt

    while curr_st < stop_dt:
        curr_end = curr_st + timedelta(days=timestep) - timedelta(seconds=1)

        if curr_end > stop_dt:
            curr_end = stop_dt

        ss = curr_st.strftime("%Y-%m-%d %H:%M:%S%z")
        fs = curr_end.strftime("%Y-%m-%d %H:%M:%S%z")

        # write the result
        with open(dt_path, "a") as t:
            t.write(f"{ss},{fs}\n")
            
        curr_st = curr_end + timedelta(seconds=1)
        
# EOF
