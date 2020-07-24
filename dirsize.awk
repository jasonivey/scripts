#!/usr/bin/env -S awk -F: -f ${_} --
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=awk

# This is normally invoked by the 'dirsize' alias which turns around and calls the dir-size function.
#  The dir-size function will grab the arg and if doesn't exist then uses the current-working-directory
#  to call the following command:
#   du -hcs "$dir_" | sed -n '1p;$p' | awk -f dirsize.awk
#
# This boils down to 'du --human-readable --total --summarize'.  It was necessary to go with the short form
#  since macOS (non-Brew version) still doesn't support the long options.
#
# The command will could the disk usage in a particular directory and output only two lines, the summary
#  and the total.  This makes the sed command a little redundant, but who's counting.  As mentioned,
#  the sed line pulls from the input stream the first and last lines:
#   sample:
#    15M    .
#    15M    total
#
# This awk script starts by taking the first line (--summary) and parsing it for the input directory.
#  It then uses the last line (i.e. --total) to grab the (--human-readable) total size.  Together the
#  script outputs those two values.
#   sample:
#    /home/jasoni/.oh-my-zsh: 15M

BEGIN {
    dir = ""
}

{
    if (NR == 1) {
        cmd = sprintf("realpath -LPe %s", $2)
        cmd |  getline dir_
        close(cmd)
    } else {
        printf("%s: %s\n", dir_, $1)
    }
}
