#!/bin/bash
# Version 1.1  (6/22/95) rm
#
# Usage:
#   depend directory directory ...
#
#   Where each 'directory' contains the .h and .cpp files for
#   one class category.  
#
#   If 'directory' is a file, or does not contain .h files
#   then it is ignored.
#
#   The #include parsing scheme used by this script depends upon
#   #includes being written in the form:
#
#         #include "categoryName/className.h"
#
# This script calculates the following metrics.
#
# Ca is the number of classes outside a category that depend
#    upon classes inside the category.
#
# Ce is the number of classes outside a category that are
#    dependend upon by classes inside the category.
#
# N  is the number of classes in a category
#
# Ac is the number of abstract classes in a category
#
# I  is the Instability of the category [0,100]
#    I=Ce/(Ce+Ca) * 100
#
# A  is the abstractness of the category.  [0,100] 
#    A = 100 * (Ac / N)
#
# D' is the distance of the category from the
#    main sequence.  D' = |A + I - 1|
#
# (See "Designing Object Oriented C++ Applications using
# the Booch Method", by Robert C. Martin, Prentice Hall, 1995)
#
#     Robert Martin, 21 Jun, 1995.
#     
#Robert Martin       | Design Consulting   | Training courses offered:
#Object Mentor Assoc.| rmartin@oma.com     |   OOA/D, C++, Advanced OO
#14619 N. Somerset Cr| Tel: (800) 338-6716 |   Mgt. Overview of OOT
#Green Oaks IL 60048 | Fax: (847) 918-1023 | www.objectmentor.com

#
# symbols 
#
wrk=/tmp/depend.wrk
sum=`pwd`/dependency.report
returnDir=`pwd`

rm -f $sum
touch $sum

#
# Set up work directory
#

if [ -d $wrk ] 
then
    rm -rf $wrk 
fi

mkdir $wrk

#
# first find all the directories in the arguments.
#

categories=""

for i in $*
do
    if [ -d $i ] 
    then
        if test `ls 2>/dev/null $i/*.h | wc -l` -ne 0
        then
            categories="$categories $i"
        fi
    fi
done

#
# Print header for report
#

echo "*****************************************************" >>$sum
echo Dependency report generated on `date` >>$sum
echo "*****************************************************" >>$sum
echo >>$sum
echo Processed Categories are: >>$sum
echo -------------------------- >>$sum
echo >>$sum

for name in $categories
do
    echo `basename $name` -- "($name)" >>$sum
done
echo -------------------------- >>$sum

#
# Now process each category building the dependency data base.
#


for c in $categories
do
    categoryName=`basename $c`
    echo Building dependency database for $categoryName
    cd $returnDir
    cd $c
    wrkc=$wrk/$categoryName
    mkdir $wrkc
    # get #include statements that don't have angle brackets.
    grep "#[ \t]*include" [a-zA-Z]*.h [a-zA-Z]*.cpp [a-zA-Z]*.cc 2>/dev/null | grep -hv "<" >$wrkc/inc

    # now create the dependency database whic is a file that 
    # has the format: 
    #    sourceClassName:TargetCategoryName:TargetClassName
    #
    sed "s/#include//g" <$wrkc/inc | sed "s/\.cpp://g" | \
        sed "s/\.h://g" | sed "s/\"//g" | sed "s/\// /g" | \
        sed "s/\\\\/ /g" | sed "s/\.h.*$//g" | sed "s/ /:/g" | \
        sed "s/::/:/g" | grep ".*:.*:.*" >$wrkc/db

    # Next create a list of classes in this category.  This
    # is Kludged by simply counting the .h files that contain
    # the keyword "class".

    grep -l class *.h >$wrkc/n

    # Next create a list of abstract classes.  These are
    # classes that have pure virtual functions in them.
    # This is Kludged by counting variations of ") = 0"
    # in the .h files.  This is pretty easy to fool.

    #
    grep -l ")[ \t]*=[ \t]*0;" *.h >$wrkc/ac
    grep -l ")[ \t]*const[ \t]*=[ \t]*0;" *.h >>$wrkc/ac
    sort <$wrkc/ac | uniq >$wrkc/acx
    mv $wrkc/acx $wrkc/ac

    # Next create the database of efferent dependencies.
    #  Format is:  Ce TargetCategoryName.  
    #                 where Ce is the number of classes in
    #                 other the target category that this
    #                 category depends upon.
    #
    cd $wrkc
    cut -d: -f2,3 <db | grep -v "^$categoryName:" | sort | uniq | \
        cut -d: -f1 >ce
    uniq -c <ce >ceCount

    #
    # Next create the database of afferent dependencies.
    #   Format is:  Ca TargetCategoryName.
    #                  where Ca is the number of classes in
    #                  this category that depend upon classes
    #                  in the target category
    cut -d: -f2,1 <db | grep -v "^$categoryName:" | sort | uniq | \
        cut -d: -f2 | sort >ca
    uniq -c <ca >caCount

done

#
# now generate the report for each category
#

for c in $categories
do
    categoryName=`basename $c`
    echo Generating $categoryName ...
    cd $wrk/$categoryName
    echo "" >>$sum
    echo ---------- Category: $categoryName ------------- >>$sum
    echo **Efferent Dependencies: >>$sum
    cat <ceCount >>$sum
    Ce=`wc -l <ce`
    echo **Ce = $Ce >>$sum
    #
    # Now calculate afferent dependencies
    #
    echo >>$sum
    echo **Afferent Dependencies: >>$sum
    accumulator=$wrk/$categoryName/ca.acc
    touch $accumulator
    for xc in $categories
    do
        otherCategory=`basename $xc`
        if [ $otherCategory != $categoryName ]
        then
            cd $wrk/$otherCategory
            grep "^$categoryName$" <ca >>$accumulator
            grep "^$categoryName$" <ca >$categoryName.ca
            if [ -s $categoryName.ca ]
            then
                echo "    " `wc -l <$categoryName.ca` $otherCategory >> $sum
            else
                rm -f $categoryName.ca
            fi
            cd $wrk/$categoryName
        fi
    done

    Ca=`wc -l <$accumulator`
    echo **Ca = $Ca >> $sum

    #
    # Now print N and AC
    #

    Ac=`wc -l <ac`
    N=`wc -l <n`
    echo >> $sum
    echo **Class Counts >> $sum
    echo "N (Number of classes)" = $N >> $sum
    echo "AC (Abstract classes)" = $Ac >> $sum
    echo >> $sum

    #
    # now calculate derived metrics
    #

    A=`expr "(" 100 "*" $Ac ")" "/" $N`
    I=`expr "(" 100 "*" $Ce ")" "/" "(" $Ce "+" $Ca ")"`
    D=`expr "(" $A "+" $I ")" "-" 100`
    if test $D -lt 0
    then
        D=`expr 0 "-" $D`
    fi

    echo A = $A >> $sum
    echo I = $I >> $sum
    echo "D'" = $D >> $sum

done

echo ------------------------------- >> $sum

#
# Clean Up
#

#rm -rf $wrk
cd $returnDir
