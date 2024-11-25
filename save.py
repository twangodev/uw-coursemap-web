import json
import os
from datetime import datetime, timezone
from logging import Logger

from json_serializable import JsonSerializable


def recursive_sort_data(data):
    """
    Recursively sorts dictionaries and lists.
    - For dictionaries, it sorts by keys.
    - For lists, it sorts the elements (and sorts nested structures recursively).
    """
    if isinstance(data, dict):
        return {key: recursive_sort_data(data[key]) for key in sorted(data.keys())}
    elif isinstance(data, (list, set, tuple)):
        return [recursive_sort_data(item) if isinstance(item, (dict, list, set, tuple, JsonSerializable)) else item for item in data]
    elif isinstance(data, JsonSerializable):
        return recursive_sort_data(json.loads(data.to_json()))
    else:
        return data


def format_file_size(size_in_bytes):
    """
    Formats the file size in human-readable units (Bytes, KB, MB, etc.).
    """
    units = ["Bytes", "KB", "MB", "GB", "TB"]
    index = 0
    size = size_in_bytes
    while size >= 1024 and index < len(units) - 1:
        size /= 1024
        index += 1
    return f"{size:.2f} {units[index]}"


def write_file(data_dir, directory_tuple: tuple[str, ...], filename: str, data, logger: Logger):
    """
    Writes a sorted dictionary or list to a JSON file.
    - directory_tuple: Tuple representing the directory path.
    - filename: Name of the JSON file (without the .json extension).
    - data: Dictionary or list to be written to the file.
    - logger: Logger instance for logging messages.
    """
    if not isinstance(data, (dict, list, set, tuple, JsonSerializable)):
        raise TypeError("Data must be a dictionary, list, set, tuple, or JsonSerializable object")

    # Convert data to a list if it is a set or tuple
    if isinstance(data, (set, tuple)):
        data = list(data)
    elif isinstance(data, JsonSerializable):
        data = json.loads(data.to_json())

    # Sort the data
    sorted_data = recursive_sort_data(data)

    # Create the full directory path
    directory_path = os.path.join(data_dir, *directory_tuple)

    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)

    # Sanitize the filename to remove problematic characters
    sanitized_filename = filename.replace("/", "_").replace(" ", "_")

    # Full path to the JSON file
    file_path = os.path.join(directory_path, f"{sanitized_filename}.json")

    # Write the sorted data to the file in JSON format
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(sorted_data, json_file, indent=4)

    # Calculate file size and format it
    file_size = os.path.getsize(file_path)
    readable_size = format_file_size(file_size)

    logger.info(f"Data written to {file_path} ({readable_size})")

def wipe_data(data_dir, logger):
    """
    Wipe all data in the data directory.
    """
    logger.info("Wiping data directory...")

    # Remove all files and directories in the data directory
    for root, dirs, files in os.walk(data_dir, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for directory in dirs:
            os.rmdir(os.path.join(root, directory))

    logger.info("Data directory wiped.")

def write_data(data_dir, subject_to_full_subject, subject_to_courses, identifier_to_course, global_graph, subject_to_graph, global_style, subject_to_style, logger):
    wipe_data(data_dir, logger)

    write_file(data_dir, tuple(), "subjects", subject_to_full_subject, logger)

    for subject, courses in subject_to_courses.items():
        write_file(data_dir, ("courses",), subject, courses, logger)

    for identifier, course in identifier_to_course.items():
        write_file(data_dir, ("course",), identifier, course, logger)

    write_file(data_dir, tuple(), "global_graph", global_graph, logger)
    for subject, graph in subject_to_graph.items():
        write_file(data_dir, ("graphs",), subject, graph, logger)

    write_file(data_dir, tuple(), "global_style", global_style, logger)
    for subject, style in subject_to_style.items():
        write_file(data_dir, ("styles",), subject, style, logger)

    updated_on = datetime.now(timezone.utc).isoformat()
    updated_json = {"updated_on": updated_on}

    write_file(data_dir, tuple(), "update", updated_json, logger)
