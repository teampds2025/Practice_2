cd /home/ubuntu/jn
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python src/data_receiver/daily_data_collection.py
deactivate