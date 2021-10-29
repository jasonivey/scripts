#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=zsh

get_date_format() {
    echo '+%Y-%b-%e %I:%M:%S%P %Z'
}

print_debug() {
    #local date_fmt="$(get_date_format)"
    #printf "\e[93m[%s]  \e[33mDEBUG\e[37;1m: %s\e[0m\n" "$(date "$date_fmt")" "$1" 1>&2
    echo > /dev/null
}

print_info() {
    local date_fmt="$(get_date_format)"
    printf "\e[93m[%s]  \e[32mINFO\e[37;1m: %s\e[0m\n" "$(date "$date_fmt")" "$1" 1>&2
}

print_error() {
    local date_fmt="$(get_date_format)"
    printf "\e[93m[%s]  \e[31mERROR\e[37;1m: %s\e[0m\n" "$(date "$date_fmt")" "$1" 1>&2
}

error_exit() {
    print_error "$1"
    exit 1
}

get_virtual_machine_directory() {
    local os_name="unknown"
    case "$OSTYPE" in
        solaris*) os_name="SOLARIS" ;;
        darwin*)  os_name="OSX" ;;
        linux*)   os_name="LINUX" ;;
        bsd*)     os_name="BSD" ;;
        msys*)    os_name="WIN32" ;;
        cygwin*)  os_name="WIN32" ;;
        *)        os_name="unknown: $OSTYPE" ;;
    esac
    if [[ "$os_name" =~ "OSX" ]]; then
        print_debug "platform is macOS";
        ret_val="`realpath -LPe \"$HOME/Virtual Machines.localized/\"`";
    elif [[ "$os_name" == "LINUX" ]]; then
        ret_val="`realpath -LPe $HOME/vms`";
    elif [[ "$os_name" == "WIN32" ]]; then
        ret_val="`realpath -LPe $HOME/vms`";
    fi
}

start_virtual_machine() {
    local vmx_file="$1"
    local vmx_file_basename="${vmx_file##*/}"
    local vmx_file_str="${vmx_file_basename%.vmx}"
    print_info "starting virtual machine: $vmx_file_str"
    vmrun -T fusion start "$vmx_file" nogui || error_exit "failed to start virtual machine: $vmx_file"
    print_info "waiting for virtual machine to startup: $vmx_file_str"
    read ip_addr_str < <(vmrun -T fusion getGuestIPAddress "$vmx_file" -wait)
    print_info "started: $vmx_file_str, ip address: $ip_addr_str"
}

find_virtual_machine_vmx() {
    local vm_dir="$1"
    local vmx_path=$(/bin/ls "$vm_dir" | egrep -i '\.vmx\b')
    if [[ $? -ne 0 ]]; then
        error_exit "unable to find a .vmx file within: $vm_dir"
    fi
    vmx_path="`realpath -LPe "$vm_dir"/"$vmx_path"`"
    print_debug "vmx file found: $vmx_path"
    ret_val="$vmx_path"
}

find_virtual_machine_vmwarevm() {
    local vm_name="$1"
    get_virtual_machine_directory
    local vm_root_dir="$ret_val"
    print_debug "virtual machine directory: $vm_root_dir"
    local vm_dir="$vm_root_dir/$vm_name"
    print_debug "full virtual machine directory: $vm_dir"
    if [[ ! -d "$vm_dir" ]]; then
        error_exit "unable to find vm directory: $vm_dir"
    fi
    ret_val="$vm_dir"
}

find_virtual_machine_path() {
    vm_name="$1"
    print_debug "vm_name: $vm_name"

    local ends_with_vmx=0
    if [[ "${vm_name/*.vmx/1}" == '1' ]]; then
        print_debug "path ends with .vmx extension";
        ends_with_vmx=1
    fi

    if [[ -e "$vm_name" && ((ends_with_vmx == 1)) ]]; then
        print_debug "file exists: $vm_name";
        ret_val="$vm_name";
    elif [[ -e "${vm_name}.vmx" ]]; then
        print_debug "file exists (after adding .vmx): $vm_name";
        ret_val="${vm_name}.vmx";
    elif [[ -d "$vm_name" ]]; then
        print_debug "directory exists: $vm_name";
        find_virtual_machine_vmx "$vm_name";
    elif [[ -d "${vm_name}.vmwarevm" ]]; then
        print_debug "directory exists (after adding .vmwarevm): $vm_name";
        find_virtual_machine_vmx "${vm_name}.vmwarevm";
    else
        if [[ "${vm_name/*.vmwarevm/1}" == '1' ]]; then
            find_virtual_machine_vmwarevm "$vm_name";
            vm_dir="$ret_val"
        else
            find_virtual_machine_vmwarevm "${vm_name}.vmwarevm";
            vm_dir="$ret_val"
        fi
        find_virtual_machine_vmx "$vm_dir"
    fi
}

main() {
    local ret_val=""
    find_virtual_machine_path "$1"
    local vmx_path="$ret_val"
    print_info "virtual machine path: $vmx_path"
    start_virtual_machine "$vmx_path"
}

print_info "input name: $1"
main "$1"
