#!/usr/bin/env python3
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=python
import sys
import traceback
from pathlib import Path


def create_sysctl(file_name):
    filepath = Path(file_name)
    if not filepath.is_file():
        print(f'ERROR: input file {file_name} does not exist')
        return False

    count = 0
    sysctl_data = {}
    code_types = set()
    for line in filepath.read_text().splitlines():
        count += 1
        line = line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split()]
        if not (3 <= len(parts) <= 4):
            print(f'ERROR: line did not have 3 or 4 parts, {line}')
            continue
        key = parts[0]
        reg_type_value = parts[2] if len(parts) == 4 else parts[1]
        if reg_type_value.upper() == 'INT':
            reg_type_value = 'int32_t'
        type_value = reg_type_value.upper()
        if key in sysctl_data:
            if sysctl_data[key] == type_value:
                # must have added duplicates the input file
                print(f'INFO: added duplicate on line: '
                      f'{count} with {key} and {type_value}')
            else:
                print(f'INFO: found duplicate on line: '
                      f'{count} with {key} and different data: {type_value}')
            continue
        if type_value not in code_types:
            code_types.add(reg_type_value)
        sysctl_data[key] = type_value

    output_data = []
    sorted_code_types = sorted(list(code_types))
    for code_type in sorted_code_types:
        enum_type = code_type.replace('[]', '_array')
        output_data.append(
            f'SYSCTL_TYPE({code_type.upper()}, type_{enum_type})')

    if len(output_data) > 0:
        output_data[-1] = output_data[-1].replace('SYSCTL_TYPE',
                                                  'SYSCTL_TYPE_END')

    sorted_keys = sorted(sysctl_data.keys())
    for name in sorted_keys:
        type_value = sysctl_data[name]
        output_data.append(f'SYSCTL({name}, {type_value})')

    if len(output_data) > 0:
        output_data[-1] = output_data[-1].replace('SYSCTL', 'SYSCTL_END')

    output_data.append('#undef SYSCTL_TYPE')
    output_data.append('#undef SYSCTL_TYPE_END')
    output_data.append('#undef SYSCTL')
    output_data.append('#undef SYSCTL_END')

    output_path = filepath.with_suffix('.h')
    with output_path.open(mode='w') as f:
        f.write('\n'.join(output_data))


# input file generated from copying tables within `man 3 sysctl`


def main():
    try:
        create_sysctl(sys.argv[1])
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type,
                                  exc_value,
                                  exc_traceback,
                                  file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
