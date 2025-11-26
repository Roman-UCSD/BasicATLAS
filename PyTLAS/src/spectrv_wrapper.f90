module spectrv_wrapper
  use iso_c_binding
  implicit none

  character(kind=c_char), pointer :: f5(:,:) => null()
  integer(c_int) :: f5_nlines = 0
  integer(c_int) :: f5_ncols = 0

  real(c_double), pointer :: f2(:,:) => null()

  real(c_double), pointer :: teff_logg(:) => null()
  real(c_double), pointer :: frqedg(:) => null()
  real(c_double), pointer :: wledge(:) => null()
  real(c_double), pointer :: cmedge(:) => null()
  real(c_double), pointer :: idmol(:) => null()
  real(c_double), pointer :: momass(:) => null()
  real(c_double), pointer :: freqset(:) => null()
  real(c_double), pointer :: structure(:,:) => null()
  real(c_double), pointer :: continall(:,:) => null()
  real(c_double), pointer :: contabs(:,:) => null()
  real(c_double), pointer :: contscat(:,:) => null()
  real(c_double), pointer :: xnfpel(:,:,:) => null()
  real(c_double), pointer :: dopple(:,:,:) => null()

  integer(c_int) :: n_lines = 0
  integer(c_int) :: n_wl = 0
  integer(c_int) :: ifvac = 0
  integer(c_int) :: n_lines_f19 = 0
  real(c_double) :: wl_start = 0.0
  real(c_double) :: wl_end = 0.0
  real(c_double) :: res = 0.0
  real(c_double) :: ratio = 0.0
  real(c_double) :: ratiolg = 0.0
  real(c_float) :: cutoff = 0.0
  real(c_float) :: vturb = 0.0

  real(c_float), pointer :: asynth(:,:) => null()
  real(c_double), pointer :: spectrum(:,:) => null()

  real(c_double), bind(c, name='wbegin') :: wbegin = 0.0
  real(c_double), bind(c, name='deltaw') :: deltaw = 0.0
  integer(c_int), bind(c, name='numnu') :: numnu = 0

contains

  subroutine run_spectrv() bind(c)

    call SPECTRV

  end subroutine run_spectrv

  subroutine set_spectrum(ptr_spectrum, n_wl) bind(c)
    use iso_c_binding
    type(c_ptr),   value :: ptr_spectrum
    integer(c_int), value :: n_wl

    call c_f_pointer(ptr_spectrum, spectrum, [n_wl,2])

  end subroutine set_spectrum

  subroutine update_spectrum(idx, S_Q) bind(c, name="update_spectrum_")
    use iso_c_binding
    integer(c_int), intent(in)  :: idx
    real(c_double), intent(in)  :: S_Q(41)

    spectrum(idx,:) = S_Q(:2)
  end subroutine update_spectrum

  subroutine update_meta(S_WBEGIN, S_DELTAW, S_NUMNU) bind(c, name="update_meta_")
    use iso_c_binding
    integer(c_int), intent(in)  :: S_NUMNU
    real(c_double), intent(in)  :: S_WBEGIN, S_DELTAW

    wbegin = S_WBEGIN
    deltaw = S_DELTAW
    numnu = S_NUMNU
  end subroutine update_meta

  subroutine set_asynth(ptr_asynth, n_wl) bind(c)
    use iso_c_binding
    type(c_ptr),   value :: ptr_asynth
    integer(c_int), value :: n_wl

    call c_f_pointer(ptr_asynth, asynth, [n_wl,72])

  end subroutine set_asynth

  subroutine load_asynth(idx, S_ASYNTH) bind(c, name="load_asynth_")
    use iso_c_binding
    integer(c_int), intent(in)  :: idx
    real(c_float), intent(out)  :: S_ASYNTH(99)

    S_ASYNTH(:72) = asynth(idx,:)
  end subroutine load_asynth

  subroutine set_f93(in_n_lines, in_n_wl, in_ifvac, in_n_lines_f19, in_wl_start, in_wl_end, in_res, in_ratio, &
                    & in_ratiolg, in_cutoff, in_vturb) bind(c)
    use iso_c_binding
    integer(c_int), value :: in_n_lines
    integer(c_int), value :: in_n_wl
    integer(c_int), value :: in_ifvac
    integer(c_int), value :: in_n_lines_f19
    real(c_double), value :: in_wl_start
    real(c_double), value :: in_wl_end
    real(c_double), value :: in_res
    real(c_double), value :: in_ratio
    real(c_double), value :: in_ratiolg
    real(c_float), value :: in_cutoff
    real(c_float), value :: in_vturb

    n_lines = in_n_lines
    n_wl = in_n_wl
    ifvac = in_ifvac
    n_lines_f19 = in_n_lines_f19
    wl_start = in_wl_start
    wl_end = in_wl_end
    res = in_res
    ratio = in_ratio
    ratiolg = in_ratiolg
    cutoff = in_cutoff
    vturb = in_vturb

  end subroutine set_f93

  subroutine loadf93(S_WLBEG,S_RESOLU,S_WLEND,S_LENGTH,S_N,S_LINOUT,S_TURBV,S_IFVAC) bind(c, name="loadf93_")
    use iso_c_binding
    integer(c_int), intent(out) :: S_LENGTH, S_IFVAC, S_LINOUT, S_N
    real(c_double), intent(out) :: S_WLBEG, S_WLEND, S_RESOLU
    real(c_float), intent(out)  :: S_TURBV

    S_N = 72
    S_LENGTH = n_wl
    S_IFVAC = ifvac
    S_TURBV = vturb
    S_WLBEG = wl_start
    S_WLEND = wl_end
    S_RESOLU = res
    S_LINOUT = -1
  end subroutine loadf93

  subroutine set_f10(ptr_teff_logg, ptr_frqedg, ptr_wledge, ptr_cmedge, ptr_idmol, ptr_momass, ptr_freqset, ptr_structure, &
                    & ptr_continall, ptr_contabs, ptr_contscat, ptr_xnfpel, ptr_dopple) bind(c)
    use iso_c_binding
    type(c_ptr),   value :: ptr_teff_logg
    type(c_ptr),   value :: ptr_frqedg
    type(c_ptr),   value :: ptr_wledge
    type(c_ptr),   value :: ptr_cmedge
    type(c_ptr),   value :: ptr_idmol
    type(c_ptr),   value :: ptr_momass
    type(c_ptr),   value :: ptr_freqset
    type(c_ptr),   value :: ptr_structure
    type(c_ptr),   value :: ptr_continall
    type(c_ptr),   value :: ptr_contabs
    type(c_ptr),   value :: ptr_contscat
    type(c_ptr),   value :: ptr_xnfpel
    type(c_ptr),   value :: ptr_dopple

    call c_f_pointer(ptr_teff_logg, teff_logg, [2])
    call c_f_pointer(ptr_frqedg, frqedg, [344])
    call c_f_pointer(ptr_wledge, wledge, [344])
    call c_f_pointer(ptr_cmedge, cmedge, [344])
    call c_f_pointer(ptr_idmol, idmol, [100])
    call c_f_pointer(ptr_momass, momass, [100])
    call c_f_pointer(ptr_freqset, freqset, [1029])
    call c_f_pointer(ptr_structure, structure, [16,99])
    call c_f_pointer(ptr_continall, continall, [72,1131])
    call c_f_pointer(ptr_contabs, contabs, [72,1131])
    call c_f_pointer(ptr_contscat, contscat, [72,1131])
    call c_f_pointer(ptr_xnfpel, xnfpel, [72,139,6])
    call c_f_pointer(ptr_dopple, dopple, [72,139,6])

  end subroutine set_f10

  subroutine loadf10_1(S_NEDGE, S_FRQEDG, S_WLEDGE, S_CMEDGE, S_NCON, S_CONFRQ) bind(c, name="loadf10_1_")
    use iso_c_binding
    integer(c_int), intent(out) :: S_NEDGE, S_NCON
    real(c_double), intent(out) :: S_FRQEDG(377),S_WLEDGE(377),S_CMEDGE(377),S_CONFRQ(1131)

    S_NEDGE = 344
    S_FRQEDG(:S_NEDGE) = frqedg(:S_NEDGE)
    S_WLEDGE(:S_NEDGE) = wledge(:S_NEDGE)
    S_CMEDGE(:S_NEDGE) = cmedge(:S_NEDGE)
    S_NCON = 1029
    S_CONFRQ(:S_NCON) = freqset(:S_NCON)

  end subroutine loadf10_1

  subroutine loadf10_2(S_J, S_QCONTABS, S_QCONTSCAT) bind(c, name="loadf10_2_")
    use iso_c_binding
    integer(c_int), intent(in) :: S_J
    real(c_double), intent(out) :: S_QCONTABS(1131), S_QCONTSCAT(1131)

    S_QCONTABS = contabs(S_J,:)
    S_QCONTSCAT = contscat(S_J,:)

  end subroutine loadf10_2

  subroutine set_f2(ptr, n, m) bind(c)
      use iso_c_binding
      type(c_ptr), value :: ptr
      integer(c_int), value :: n, m

      call c_f_pointer(ptr, f2, [n, m])
  end subroutine set_f2

  subroutine loadf2(idx, C,E1,E2,E3,E4,E5,E6,E7) bind(c, name="loadf2_")
      use iso_c_binding
      integer(c_int), intent(in) :: idx
      real(c_double) :: C,E1,E2,E3,E4,E5,E6,E7

      C = f2(idx,1)
      E1 = f2(idx,2)
      E2 = f2(idx,3)
      E3 = f2(idx,4)
      E4 = f2(idx,5)
      E5 = f2(idx,6)
      E6 = f2(idx,7)
      E7 = f2(idx,8)
  end subroutine loadf2

  subroutine set_f5(ptr, n, m) bind(c)
      use iso_c_binding
      type(c_ptr), value :: ptr
      integer(c_int), value :: n, m

      call c_f_pointer(ptr, f5, [n, m])
      f5_nlines = n
      f5_ncols = m
  end subroutine set_f5

  subroutine loadf5(idx, card) bind(c, name="loadf5_")
      use iso_c_binding
      integer(c_int), intent(in) :: idx
      character(kind=c_char) :: card(f5_ncols)

      card(:) = f5(idx,:)
  end subroutine loadf5

end module spectrv_wrapper
