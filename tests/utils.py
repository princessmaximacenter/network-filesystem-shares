import os


def fabricate_a_source(root_dir, relative_paths) -> list:
    items = []
    for rel_path in relative_paths:
        abs_path = os.path.join(root_dir, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w') as f:
            f.write(str(abs_path))
        items.append(abs_path)
    return items
