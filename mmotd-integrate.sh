#!/usr/bin/env bash
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=zsh

# for future reference when trying to figure out the printf commands below
#local RED=31
#local GREEN=32
#local ORANGE=33
#local BLUE=34
#local PURPLE=35
#local CYAN=36
#local GREY=37
#local DARK_GREY=90
#local LIGHT_RED=91
#local LIGHT_GREEN=92
#local YELLOW=93
#local LIGHT_BLUE=94
#local LIGHT_PURPLE=95
#local TURQUOISE=96

get_date_format() {
    echo '+%Y-%b-%e %I:%M:%S%P %Z'
}

print_info() {
    local date_fmt="$(get_date_format)"
    printf "\e[93m[%s]  \e[32mINFO\e[37;1m: %s\e[0m\n" "$(date "$date_fmt")" "$1" 1>&2
}

print_error() {
    local date_fmt="$(get_date_format)"
    printf "\e[93m[%s]  \e[31mERROR\e[37;1m: %s\e[0m\n" "$(date "$date_fmt")" "$1" 1>&2
}

error_exit()
{
    print_error "$1"
    exit 1
}

exists() {
    command -v "$1" >/dev/null 2>&1
}

integrate_cmake_init_variation() {
    CC=$1 CXX=$2 cmake -S .. -B . -DCMAKE_BUILD_TYPE="$3" -DCMAKE_VERBOSE_MAKEFILE=ON -GNinja || error_exit "configuring mmotd using $2 in $3 mode"
}

integrate_cmake_build_variation() {
    cmake --build . --target all || error_exit "building mmotd using $1 in $2 mode"
}

integrate_run_test_binary() {
    local quoted_command_line=$(build_command_line $1)
}

integrate_run_test_binaries() {
    [ $# -gt 0 ] && local build_dir=$1 || local build_dir="$HOME/dev/mmotd/build"
    [ $# -gt 1 ] && local cxx_compiler=$2 || local cxx_compiler="clang++ (guessing)"
    [ $# -gt 2 ] && local build_type=$3 || local build_type="Debug (guessing)"
    ctest || error_exit "running 'ctest' using $cxx_compiler in $build_type mode"
    $build_dir/apps/mmotd_raw/mmotd_raw || error_exit "running 'mmotd_raw' using $cxx_compiler in $build_type mode"
    $build_dir/apps/mmotd/mmotd -t $build_dir/../config/mmotd_1_column_template.json || error_exit "running 'mmotd -t ../config/mmotd_1_column_template.json' using $cxx_compiler in $build_type mode"
    $build_dir/apps/mmotd/mmotd -t $build_dir/../config/mmotd_2_column_template.json || error_exit "running 'mmotd -t ../config/mmotd_2_column_template.json' using $cxx_compiler in $build_type mode"
}

integrate_variation() {
    integrate_cmake_init_variation "$1" "$2" "$3"
    integrate_cmake_build_variation "$2" "$3"
}

clean_build_dir() {
    local build_dir_=$1
    if [[ "`realpath -LPe $PWD`" = "$build_dir_" ]]; then
        cd ..
    fi
    if [[ -d "$build_dir_" ]]; then
        /bin/rm -rf "$build_dir_" || error_exit "removing $build_dir_"
    fi
    mkdir "$build_dir_" || error_exit "creating/recreating build directory, $build_dir_"
    cd "$build_dir_" || error_exit "navigating back into $build_dir_"
}

# usage: integrate </dir-to-project/build>
mmotd-integrate() {
    build_dir_=$1
    echo "Integrating $build_dir_"
    if [ "$(uname)" == "Darwin" ]; then
        local -a c_compiler_names=("/usr/local/opt/llvm/bin/clang-13" "/usr/bin/clang" "/usr/local/opt/gcc/bin/gcc-11")
        local -a cxx_compiler_names=("/usr/local/opt/llvm/bin/clang-13" "/usr/bin/clang++" "/usr/local/opt/gcc/bin/g++-11")
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        if exists "g++-11"; then
            local -a c_compiler_names=("/usr/bin/gcc-11")
            local -a cxx_compiler_names=("/usr/bin/g++-11")
        fi
        if exists "clang-13"; then
            local -a c_compiler_names=("clang-13")
            local -a cxx_compiler_names=("clang++-13")
        fi
    else
        local -a c_compiler_names=()
        local -a cxx_compiler_names=()
    fi
    local -a build_types=("Debug" "Release")
    for ((i = 0; i < ${#c_compiler_names[@]}; ++i)) do
        echo "${c_compiler_names[$i]}"
        local c_compiler="${c_compiler_names[$i]}"
        local cxx_compiler="${cxx_compiler_names[$i]}"
        for build_type in "${build_types[@]}"; do
            print_info "compilers, CC: '${c_compiler}', CXX: '${cxx_compiler}'"
            print_info "build type: ${build_type}"
            clean_build_dir "${build_dir_}"
            integrate_variation "${c_compiler}" "${cxx_compiler}" "${build_type}"
            integrate_run_test_binaries "${build_dir_}" "${cxx_compiler}" "${build_type}"
        done
    done
}

main() {
    mmotd-integrate "`pwd`/build"
}

main
