#!/usr/bin/env -S gawk -F= -f ${_} --
# vim: awa:sts=4:ts=4:sw=4:et:cin:fdm=manual:tw=120:ft=awk

# this is typically called with the following command line
# isoinfo -d -i /dev/cdrom | sed -n -e 's/Logical block size is: /bs=/g p' -e 's/Volume size is: /count=/g p' | \
#  gawk -F'=' -f ~/scripts/prepare_cd_copy.awk | \
#  xargs -l bash -c 'pv -tprebs $0 /dev/cdrom | dd of=test.iso bs=$1 count=$2' | xargs

BEGIN {
    values["total"]=1
}

#awk -F'=' 'BEGIN {total=1} {print $0; total=total*int($2)} END {printf "total=%d\n", total}'

{
    if (index($0, "bs=") != 0) {
        values["block"] = int($2);
        values["total"] = int(values["total"]) * int(values["block"]);
    } else if (index($0, "count=") != 0) {
        values["volume"] = int($2);
        values["total"] = int(values["total"]) * int(values["volume"]);
    } else {
        printf("Encountered unknown value: %s\n", $0);
    }
}

END {
    printf("%d %d %d\n", values["total"], values["block"], values["volume"]);
}
