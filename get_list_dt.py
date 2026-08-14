import datetime
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--start_exp", type=str, default="2025-07-03 10:00:00")
    parser.add_argument("--stop_exp", type=str, default="2025-10-28 10:00:00")
    args = parser.parse_args()

    start_exp = args.start_exp
    stop_exp = args.stop_exp

    start_dt = datetime.datetime.strptime(start_exp, "%Y-%m-%d %H:%M:%S")
    stop_dt = datetime.datetime.strptime(stop_exp, "%Y-%m-%d %H:%M:%S")
    dt_path = "dt_list.txt"

    assert start_dt < stop_dt

    dt_next_first = start_dt
    next_month = dt_next_first.replace(day=28) + datetime.timedelta(days=4)
    dt_next_last = next_month - datetime.timedelta(days=next_month.day)
    dt_next_last = dt_next_last.replace(hour=23, minute=59, second=59)

    ss = dt_next_first.strftime("%Y-%m-%d %H:%M:%S%z")
    fs = dt_next_last.strftime("%Y-%m-%d %H:%M:%S%z")
    #print(f"{ss}, {fs}")

    # write the result
    with open(dt_path, "w") as t:  # here, "w" to erase the existing one
        t.write(f"{ss},{fs}\n")

    while dt_next_last < stop_dt:

        dt_next_first = (
            dt_next_last.replace(day=1) + datetime.timedelta(days=32)
        ).replace(day=1)
        dt_next_first = dt_next_first.replace(hour=00, minute=00, second=00)

        next_month = dt_next_first.replace(day=28) + datetime.timedelta(days=4)
        dt_next_last = next_month - datetime.timedelta(days=next_month.day)
        dt_next_last = dt_next_last.replace(hour=23, minute=59, second=59)

        if dt_next_last > stop_dt:
            dt_next_last = stop_dt

        ss = dt_next_first.strftime("%Y-%m-%d %H:%M:%S%z")
        fs = dt_next_last.strftime("%Y-%m-%d %H:%M:%S%z")

        # write the result
        with open(dt_path, "a") as t:
            t.write(f"{ss},{fs}\n")

# EOF
