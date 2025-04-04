import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_and_sort_folders(base_path):
    """List and sort directories by their names, which represent datetimes."""
    try:
        folders = [os.path.join(base_path, d) for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        # Sort folders based on the folder names, which are in a datetime format
        folders.sort(key=lambda x: os.path.basename(x))
        logging.info("Folders sorted by name:")
        for folder in folders:
            logging.info(f"{folder}")
        return folders
    except Exception as e:
        logging.error(f"Error listing and sorting folders: {e}")
        return []

def pair_folders_and_export(src_base_path, dest_base_path):
    """Pair folders and copy their contents to new directories maintaining the original folder names."""
    folders = list_and_sort_folders(src_base_path)
    pair_count = 1  

    # Ensure the destination base path exists
    if not os.path.exists(dest_base_path):
        os.makedirs(dest_base_path, exist_ok=True)

    # Process folders in pairs
    for i in range(0, len(folders), 2):
        if i + 1 < len(folders):  # Ensure there is a pair
            folder1, folder2 = folders[i], folders[i + 1]
            new_pair_folder = os.path.join(dest_base_path, f'pair_{pair_count}')
            os.makedirs(new_pair_folder, exist_ok=True)

            try:
                # Copying process for each folder
                dest_folder1 = os.path.join(new_pair_folder, os.path.basename(folder1))
                dest_folder2 = os.path.join(new_pair_folder, os.path.basename(folder2))
                os.makedirs(dest_folder1, exist_ok=True)
                os.makedirs(dest_folder2, exist_ok=True)

                for file in os.listdir(folder1):
                    shutil.copy(os.path.join(folder1, file), dest_folder1)
                for file in os.listdir(folder2):
                    shutil.copy(os.path.join(folder2, file), dest_folder2)

                logging.info(f"Paired {os.path.basename(folder1)} and {os.path.basename(folder2)} into {new_pair_folder}")
                pair_count += 1
            except Exception as e:
                logging.error(f"Failed to copy files from {folder1} and {folder2}: {e}")

if __name__ == "__main__":
    src_base_path = './metric_exports'
    dest_base_path = './paired_metric_exports'
    pair_folders_and_export(src_base_path, dest_base_path)
