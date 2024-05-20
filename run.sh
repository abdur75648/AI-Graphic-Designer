#!/bin/bash

start_time=$(date +%s)

python generate_prompt.py
python automate_midjourney.py
node index.js

end_time=$(date +%s)
execution_time=$((end_time - start_time))
minutes=$((execution_time / 60))
seconds=$((execution_time % 60))
echo "Total execution time: $minutes minutes $seconds seconds"