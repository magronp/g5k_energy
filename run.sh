source .venv/bin/activate

# Collect input arguments (start/stop_exp, and user_list)
for ARGUMENT in "$@"
do
   KEY=$(echo $ARGUMENT | cut -f1 -d=)

   KEY_LENGTH=${#KEY}
   VALUE="${ARGUMENT:$KEY_LENGTH+1}"

   export "$KEY"="$VALUE"
done

# Compute the list of month-level start/stop dates
python get_list_dt.py --start_exp "${start_exp}" --stop_exp "${stop_exp}"

# Read the list of month dates, and process each chunk
while IFS=, read -r start_month stop_month; do
  python collect_exp.py --start_exp "${start_month}" --stop_exp "${stop_month}" --user_list "${user_list}"
done < "dt_list.txt"

# Remove the list of month-level start/stop dates
rm -f dt_list.txt

# Run the concatenation of files
python concat.py --user_list "${user_list}"
