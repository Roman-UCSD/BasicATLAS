module synthe_wrapper
  use iso_c_binding
  implicit none

  type, bind(c) :: f12_record
    integer(c_int) :: skip0
    integer(c_int) :: NBUFF
    real(c_float)  :: CONGF
    integer(c_int) :: NELION
    real(c_float)  :: ELO
    real(c_float)  :: GAMRF
    real(c_float)  :: GAMSF
    real(c_float)  :: GAMWF
    real(c_float)  :: alpha
    integer(c_int) :: skip9
  end type f12_record
  type(f12_record), pointer :: f12(:) => null()

  type, bind(c) :: f19_record
    integer(c_int) :: skip0
    integer(c_int) :: WL_low
    integer(c_int) :: WL_high    
    real(c_float)  :: ELO
    real(c_float)  :: GF
    integer(c_int) :: NBLO
    integer(c_int) :: NBUP
    integer(c_int) :: NELION
    integer(c_int) :: TYPE
    integer(c_int) :: NCON
    integer(c_int) :: NELIONX
    real(c_float)  :: GAMMAR
    real(c_float)  :: GAMMAS
    real(c_float)  :: GAMMAW
    real(c_float)  :: alpha
    integer(c_int) :: NBUFF
    integer(c_int) :: skip8
    integer(c_int) :: skip9
  end type f19_record
  type(f19_record), pointer :: f19(:) => null()

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

  real(c_float), pointer :: asynth(:,:) => null()

  real(c_float), pointer :: f18(:,:) => null()

contains

  subroutine run_synthe() bind(c)

    call SYNTHE

  end subroutine run_synthe

  subroutine set_f18(ptr, n, m) bind(c)
      use iso_c_binding
      type(c_ptr), value :: ptr
      integer(c_int), value :: n, m

      call c_f_pointer(ptr, f18, [n, m])
  end subroutine set_f18

  subroutine loadf18(idx, mode, S_FNE, S_DWL, S_PHI, S_PHI4026, S_PHI4387, S_NE, S_IL) bind(c, name="loadf18_")
      use iso_c_binding
      integer(c_int), intent(in) :: idx, mode, S_NE, S_IL
      real(c_float), intent(out) :: S_FNE, S_DWL, S_PHI(8), S_PHI4026(4,8,196), S_PHI4387(4,8,204)

      S_FNE = f18(idx,1)
      S_DWL = f18(idx,2)
      if (mode .eq. 1) then
        S_PHI(:) = f18(idx,3:10)
      endif
      if (mode .eq. 2) then
        S_PHI4026(:,S_NE,S_IL) = f18(idx,3:6)
      endif
      if (mode .eq. 3) then
        S_PHI4387(:,S_NE,S_IL) = f18(idx,3:6)
      endif
  end subroutine loadf18

  subroutine set_asynth(ptr_asynth, n_wl) bind(c)
    use iso_c_binding
    type(c_ptr),   value :: ptr_asynth
    integer(c_int), value :: n_wl

    call c_f_pointer(ptr_asynth, asynth, [n_wl,72])

  end subroutine set_asynth

  subroutine update_asynth(idx, S_ASYNTH) bind(c, name="update_asynth_")
    use iso_c_binding
    integer(c_int), intent(in)  :: idx
    real(c_float), intent(in)  :: S_ASYNTH(99)

    asynth(idx,:) = S_ASYNTH(:72)
  end subroutine update_asynth

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

  subroutine loadf10_1(S_NRHOX, S_TEFF, S_GLOG, S_NEDGE, S_FRQEDG, S_WLEDGE, S_CMEDGE, S_IDMOL, S_MOMASS, S_NCON, S_CONFRQ, &
                      & S_QT, S_QTKEV, S_QTK, S_QHKT, S_QTLOG, S_QHCKT, S_QP, S_QXNE, S_QXNATOM, S_QRHO, S_QRHOX, S_QVTURB, &
                      & S_QXNFH, S_QXNFHE, S_QXNFH2) bind(c, name="loadf10_1_")
    use iso_c_binding
    integer(c_int), intent(out) :: S_NRHOX, S_NEDGE, S_NCON
    real(c_double), intent(out) :: S_TEFF,S_GLOG,S_FRQEDG(377),S_WLEDGE(377),S_CMEDGE(377),S_IDMOL(100),S_MOMASS(100),S_CONFRQ(1131)
    real(c_double), intent(out) :: S_QT(99), S_QTKEV(99), S_QTK(99), S_QHKT(99), S_QTLOG(99), S_QHCKT(99), S_QP(99), S_QXNE(99)
    real(c_double), intent(out) :: S_QRHO(99), S_QRHOX(99), S_QVTURB(99), S_QXNFH(99), S_QXNFHE(99,2), S_QXNFH2(99), S_QXNATOM(99)

    S_NRHOX = 72
    S_TEFF = teff_logg(1)
    S_GLOG = teff_logg(2)
    S_NEDGE = 344
    S_FRQEDG(:S_NEDGE) = frqedg(:S_NEDGE)
    S_WLEDGE(:S_NEDGE) = wledge(:S_NEDGE)
    S_CMEDGE(:S_NEDGE) = cmedge(:S_NEDGE)
    S_IDMOL = idmol
    S_MOMASS = momass
    S_NCON = 1029
    S_CONFRQ(:S_NCON) = freqset(:S_NCON)
    S_QT(:S_NRHOX) = structure(1,:S_NRHOX)
    S_QTKEV(:S_NRHOX) = structure(2,:S_NRHOX)
    S_QTK(:S_NRHOX) = structure(3,:S_NRHOX)
    S_QHKT(:S_NRHOX) = structure(4,:S_NRHOX)
    S_QTLOG(:S_NRHOX) = structure(5,:S_NRHOX)
    S_QHCKT(:S_NRHOX) = structure(6,:S_NRHOX)
    S_QP(:S_NRHOX) = structure(7,:S_NRHOX)
    S_QXNE(:S_NRHOX) = structure(8,:S_NRHOX)
    S_QXNATOM(:S_NRHOX) = structure(9,:S_NRHOX)
    S_QRHO(:S_NRHOX) = structure(10,:S_NRHOX)
    S_QRHOX(:S_NRHOX) = structure(11,:S_NRHOX)
    S_QVTURB(:S_NRHOX) = structure(12,:S_NRHOX)
    S_QXNFH(:S_NRHOX) = structure(13,:S_NRHOX)
    S_QXNFHE(:S_NRHOX,1) = structure(14,:S_NRHOX)
    S_QXNFHE(:S_NRHOX,2) = structure(15,:S_NRHOX)
    S_QXNFH2(:S_NRHOX) = structure(16,:S_NRHOX)

  end subroutine loadf10_1

  subroutine loadf10_2(S_J, S_QABLOG, S_QXNFPEL, S_QDOPPLE) bind(c, name="loadf10_2_")
    use iso_c_binding
    integer(c_int), intent(in) :: S_J
    real(c_double), intent(out) :: S_QABLOG(1131), S_QXNFPEL(834), S_QDOPPLE(834)

    S_QABLOG = continall(S_J,:)
    S_QXNFPEL = reshape(transpose(xnfpel(S_J,:,:)), [834])
    S_QDOPPLE = reshape(transpose(dopple(S_J,:,:)), [834])

  end subroutine loadf10_2

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

  subroutine loadf93(S_NLINES,S_LENGTH,S_IFVAC,S_IFNLTE,S_N19,S_TURBV,S_DECKJ,S_IFPRED,S_WLBEG,S_WLEND,S_RESOLU,S_RATIO, &
                    & S_RATIOLG,S_CUTOFF,S_LINOUT) bind(c, name="loadf93_")
    use iso_c_binding
    integer(c_int), intent(out) :: S_NLINES, S_LENGTH, S_IFVAC, S_IFNLTE, S_N19, S_IFPRED, S_LINOUT
    real(c_double), intent(out) :: S_WLBEG, S_WLEND, S_RESOLU, S_RATIO, S_RATIOLG
    real(c_float), intent(out)  :: S_TURBV, S_CUTOFF
    real(c_float), intent(out)  :: S_DECKJ(7,99)

    S_NLINES = n_lines
    S_LENGTH = n_wl
    S_IFVAC = ifvac
    S_IFNLTE = 0
    S_N19 = n_lines_f19
    S_TURBV = vturb
    S_DECKJ = 0.0
    S_IFPRED = 1
    S_WLBEG = wl_start
    S_WLEND = wl_end
    S_RESOLU = res
    S_RATIO = ratio
    S_RATIOLG = ratiolg
    S_CUTOFF = cutoff
    S_LINOUT = -1
  end subroutine loadf93

  subroutine set_f12(ptr_base, n_lines) bind(c)
    use iso_c_binding
    type(c_ptr),   value :: ptr_base
    integer(c_int), value :: n_lines

    call c_f_pointer(ptr_base, f12, [n_lines])

  end subroutine set_f12

  subroutine loadf12(idx, NBUFF,CONGF,NELION,ELO,GAMRF,GAMSF,GAMWF,alpha) bind(c, name="loadf12_")
    use iso_c_binding
    integer(c_int), intent(in)  :: idx
    integer(c_int), intent(out) :: NBUFF, NELION
    real(c_float), intent(out)  :: CONGF, ELO, GAMRF, GAMSF, GAMWF, alpha

    NBUFF  = f12(idx)%NBUFF
    CONGF  = f12(idx)%CONGF
    NELION = f12(idx)%NELION
    ELO    = f12(idx)%ELO
    GAMRF  = f12(idx)%GAMRF
    GAMSF  = f12(idx)%GAMSF
    GAMWF  = f12(idx)%GAMWF
    alpha  = f12(idx)%alpha
  end subroutine loadf12

  subroutine set_f19(ptr_base, n_lines) bind(c)
    use iso_c_binding
    type(c_ptr),   value :: ptr_base
    integer(c_int), value :: n_lines

    call c_f_pointer(ptr_base, f19, [n_lines])

  end subroutine set_f19

  subroutine loadf19(idx, WL,ELO,GF,NBLO,NBUP,NELION,TYPE,NCON,NELIONX,GAMMAR,GAMMAS,GAMMAW,alpha,NBUFF) bind(c, name="loadf19_")
    use iso_c_binding
    integer(c_int), intent(in)  :: idx
    integer(c_int), intent(out) :: NBLO, NBUP, NELION, TYPE, NCON, NELIONX, NBUFF
    real(c_float), intent(out)  :: ELO, GF, GAMMAR, GAMMAS, GAMMAW, alpha
    real(c_double), intent(out)  :: WL

    WL = transfer([f19(idx)%WL_low,f19(idx)%WL_high], WL)
    ELO  = f19(idx)%ELO
    GF  = f19(idx)%GF
    NBLO  = f19(idx)%NBLO
    NBUP  = f19(idx)%NBUP
    NELION  = f19(idx)%NELION
    TYPE  = f19(idx)%TYPE
    NCON  = f19(idx)%NCON
    NELIONX  = f19(idx)%NELIONX
    GAMMAR  = f19(idx)%GAMMAR
    GAMMAS  = f19(idx)%GAMMAS
    GAMMAW  = f19(idx)%GAMMAW
    alpha  = f19(idx)%alpha
    NBUFF  = f19(idx)%NBUFF
  end subroutine loadf19

end module synthe_wrapper
