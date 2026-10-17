source .venv/bin/activate

# Collect input arguments (start/stop_exp, and user_list)
for ARGUMENT in "$@"
do
   KEY=$(echo $ARGUMENT | cut -f1 -d=)

   KEY_LENGTH=${#KEY}
   VALUE="${ARGUMENT:$KEY_LENGTH+1}"

   export "$KEY"="$VALUE"
done

# Remove the list of chunk-level start/stop dates (in case it's still there)
rm -f dt_list.txt

# Compute the list of chunk-level start/stop dates
python get_list_dt.py --start_exp "${start_exp}" --stop_exp "${stop_exp}" --timestep "${timestep}"

# Read the list of chunk dates, and process each chunk
while IFS=, read -r start_chunk stop_chunk; do
  python collect_exp.py --start_exp "${start_chunk}" --stop_exp "${stop_chunk}" --user_list "${user_list}"
done < "dt_list.txt"

# Remove the list of chunk-level start/stop dates
rm -f dt_list.txt

# Concatenate all files
python concat.py --user_list "${user_list}"
