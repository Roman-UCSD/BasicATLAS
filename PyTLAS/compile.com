mkdir -p bin

# Apply patches to the original Kurucz codes: ATLAS7V, XNFPELSYN, SYNTHE and SPECTRV
for diff_file in src/*.diff; do
    base=$(basename "$diff_file" .diff)
    orig="../src/${base}.for"
    out="src/${base}.for"

    if patch --dry-run "$orig" "$diff_file" > /dev/null 2>&1; then
        tmp=$(mktemp)
        cp "$orig" "$tmp"
        patch "$tmp" "$diff_file" > /dev/null
        mv "$tmp" "$out"
    else
        echo "ERROR: Patch $diff_file failed to apply to $orig"
        exit 1
    fi
done

# Compile the patched Kurucz codes
gfortran -fPIC -fno-automatic -w -O3 -c src/xnfpelsyn.for -std=legacy
gfortran -fPIC -fno-automatic -w -O3 -c src/atlas7v.for -std=legacy
gfortran -fPIC -fno-automatic -w -O3 -c src/synthe.for -std=legacy
gfortran -fPIC -fno-automatic -w -O3 -c src/spectrv.for -std=legacy

# Compile the wrappers for those codes
gfortran -fPIC -fno-automatic -w -O3 -c src/xnfpelsyn_wrapper.f90 -std=legacy
gfortran -fPIC -fno-automatic -w -O3 -c src/synthe_wrapper.f90 -std=legacy
gfortran -fPIC -fno-automatic -w -O3 -c src/spectrv_wrapper.f90 -std=legacy

# Generate SO interfaces
gfortran -shared -fPIC -o bin/xnfpelsyn.so xnfpelsyn.o atlas7v.o xnfpelsyn_wrapper.o -std=legacy
gfortran -shared -fPIC -o bin/synthe.so synthe.o synthe_wrapper.o -std=legacy
gfortran -shared -fPIC -o bin/spectrv.so spectrv.o atlas7v.o spectrv_wrapper.o -std=legacy

# Cleanup
rm *.o *.mod
