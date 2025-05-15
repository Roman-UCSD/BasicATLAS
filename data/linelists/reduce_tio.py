import os

script_dir = os.path.dirname(os.path.realpath(__file__))

print('Remove weak lines from the TiO Toto molecular line list')
min_gf = float(input('Minimum log(gf) to keep: '))
print('Working on it...')

total = 0
kept = 0

output = script_dir + '/../synthe_files/tiototo.asc'
if not os.path.isfile(original := (script_dir + '/../synthe_files/tiototo.original.asc')):
    os.rename(output, original)
g = open(output, 'w')
f = open(original, 'r')
for line in f:
    total += 1
    gf = float(line[10:17].strip())
    if gf > min_gf:
        g.write(line)
        kept += 1
f.close()
g.close()

print('Kept {} lines out of {}'.format(kept, total))
print('Saved reduced list in {}'.format(os.path.realpath(output)))
print('Original file available in {}'.format(os.path.realpath(original)))
