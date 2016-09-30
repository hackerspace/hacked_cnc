#!/usr/bin/python
import re
import os

dwell_secs = 10
milldrill_depth = -0.4

fnames = ['front.ngc', 'back.ngc', 'outline.ngc', 'drill.ngc']

def replace_val(token, nval, line):
    return re.sub(r'({})(-?[0-9.]+)'.format(token), r'{}{}'.format(token, nval), line)

for file in fnames:
    if not os.path.isfile(file):
        continue

    is_drill = file.startswith('drill')
    out = open('{}_post.ngc'.format(file.rsplit('.', 1)[0]), 'w')
    if is_drill:
        mdout = open('milldrill_post.ngc', 'w')

    with open(file) as f:
        for line in f:
            newline = line
            # prefix lines starting with 'X' with 'G01 '
            if line[0] == 'X':
                if is_drill:
                    newline = 'G81 ' + line
                else:
                    newline = 'G01 ' + line
            if line.startswith('M3'):
                m3 = True
                if is_drill:
                    newline += 'G04 P{}\n'.format(dwell_secs)

            if line.startswith('G04') and m3:
                newline = 'G04 P{}\n'.format(dwell_secs)
                m3 = False

            out.write(newline)

            if is_drill:
                if line.startswith('G81'):
                    newline = replace_val('Z', milldrill_depth, line)

                # replace each 'G81 X' line with 'G81 Z{milldrill_depth} X' so we can level
                # the milldrill file
                if newline.startswith('G81 X'):
                    newline = newline.replace('G81 X', 'G81 Z{} X'.format(milldrill_depth))

                mdout.write(newline)
