import argparse
import os
from pathlib import Path
import shutil  # Added module for moving files

#rename "PIDS_FILENAME.txt" to match your filename

from dora import IslandoraSession, load_pids

def download_rels_ext_datastream_for_pids(session, pids, output_folder, encoding="utf8"):
    # Create the main output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    for pid in pids:
        # Construct the output file path based on the main folder and PID
        output_file = os.path.join(output_folder, f"rels-ext-{pid}.xml")

        # Download the RELS-EXT datastream and save it to the output file
        session.download_rels_ext_datastream(pid, output_file=output_file, encoding=encoding)

if __name__ == "__main__":
    # Create an Islandora Session
    s = IslandoraSession()
    s.login("USERNAME", "PASSWORD")

    # Load PIDs from a text file
    pid_file_path = "PIDS_FILENAME.txt"
    pids = load_pids(pid_file_path)

    # Derive the main folder name from the PID file name by removing "pids_" and the file extension
    main_output_folder = os.path.splitext(pid_file_path.split("pids_")[1])[0]

    # Download RELS-EXT datastreams for each PID and save them directly in the derived folder
    download_rels_ext_datastream_for_pids(s, pids, main_output_folder)