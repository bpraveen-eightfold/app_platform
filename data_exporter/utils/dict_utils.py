def get_nested_content(dict_in, path, delimiter='.'):
    key_list = path.split(delimiter)

    content = dict_in

    for key in key_list:
        if not content or key not in content:
            return None

        content = content.get(key, {})

    return content
