ATOMIC LINES

BasicATLAS provides multiple alternative atomic line lists

1. gfall08oct17.dat

    This is the standard line list for SYNTHE compiled by Robert Kurucz. It is downloaded from http://kurucz.harvard.edu/linelists/gfnew/gfall08oct17.dat

2. vald3.dat

    Line list retrieved from the VALD3 (https://vald.astro.uu.se/) database between 200 nm and 1200 nm. Outside this wavelength range, the line list is
    completed with Kurucz data. Hydrogen lines in VALD3 have also been replaced with Kurucz counterparts, since the damping prescription used by VALD3 for
    those lines differs to the one used by SYNTHE

3. kirby_escala.dat

    Line list compiled by Evan Kirby (2011PASP..123..531K) and Ivanna Escala (2019ApJ...878...42E) between 410 nm and 910 nm. Outside this wavelength range,
    the line list is completed with Kurucz data. This line list was converted from the MOOG format. The damping constants were extracted directly from MOOG
    by importing the original line list into moog17scat (https://github.com/alexji/moog17scat). MOOG's trudamp was applied to the Ca II triplet. For
    Fe I 4427 line, the radiative damping constant was taken from VALD3. Isotope mass fractions were adopted from the periodictable Python module

4. merged.dat

    Line list compiled by combining the lines from gfall08oct17.dat, vald3.dat and kirby_escala.dat to attain the best correspondence between synthetic
    spectra and the observed spectrum of Arcturus from 2000vnia.book.....H. Note that while this line list is somewhat over-fitting the spectrum of Arcturus,
    it appears to be a marginally better match to the spectrum of the Sun as well, compared to the three original line lists

5. BasicATLAS.dat >> RECOMMENDED

    A version of merged.dat with the oscillator strengths and damping constants of selected lines adjusted to better match the observed spectrum of Arcturus
    in the optical (2000vnia.book.....H) and infrared (1995PASP..107.1042H). A few strong Kurucz Fe I lines that do not appear in the spectrum of Arcturus
    have been removed

NOTES: The angular momentum numbers in the line lists are sometimes replaced with 1.0 as placeholders, since SYNTHE uses the provided log(gf) values and does not
generally require them.

MOLECULAR LINES

Molecular lines in BasicATLAS are imported according to Fiorella Castelli's tutorial (https://wwwuser.oats.inaf.it/fiorella.castelli/sources/synthe/examples/synthep.html)
with three exceptions:

1. chmasseron.asc
    The CH line list distributed by Robert Kurucz (http://kurucz.harvard.edu/molecules/ch/chmasseron.asc) appears to be faulty as it contains numerous strong
    lines that do not appear in observed spectra. Instead, chmasseron_corrected.asc is shipped with BasicATLAS. It was built from the VizieR table (J/A+A/571/A47)
    of Masseron+2014

2. mgh.asc
    The MgH line list distributed by Robert Kurucz (http://kurucz.harvard.edu/linelists/linesmol/mgh.asc) is replaced in BasicATLAS with the ExoMol line list
    mgh_exomol.asc, built from Owens+2022 (https://www.exomol.com/data/molecules/MgH/24Mg-1H/XAB/ and equivalents for isotopes)

3. tiototo.asc
    The TiO line list compiled by Schwenke+1998 and distributed by Robert Kurucz (http://kurucz.harvard.edu/molecules/tio/tioschwenke.bin) is outdated with multiple
    more recent alternatives available. In BasicATLAS, this list is replaced with the ExoMol/Toto database (McKemmish+2019), which was also downloaded from the Kurucz
    website (http://kurucz.harvard.edu/molecules/tio/tiototo.asc). Even though the Kurucz version of the Toto list is much shorter than the original (the weakest lines
    have been excluded), it is still much larger than the Schwenke list and incurs a large computational penalty. In low- and medium-resolution spectroscopy, the list
    can be reduced even further to ragain some of the original performance. We provide a helper script, reduce_tio.py, which may be used to remove the weakest lines
    from the TiO list up to a given oscillator strength (log(gf)). We found that removing all lines with log(gf)<-3 is typically acceptable. Note that once the list has
    been shortened, it will be considered corrupted by test.py

NOTES: The replaced molecular line lists are imported with RMOLECASC, which provides default damping constants depending on whether the transition is roto-vibrational or
electronic. The nature of each transition is inferred from the energy level labels in the line list. Some of the replaced line lists do not have level labels, and all
transitions are interpreted as electronic. This omission however appears to have a negligibly small effect on the synthesized spectrum.
