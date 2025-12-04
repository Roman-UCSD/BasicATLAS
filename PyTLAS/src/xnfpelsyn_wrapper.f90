module xnfpelsyn_wrapper
  use iso_c_binding
  implicit none

  character(kind=c_char), pointer :: f17(:,:) => null()
  integer(c_int) :: f17_nlines = 0
  integer(c_int) :: f17_ncols = 0

  character(kind=c_char), pointer :: f5(:,:) => null()
  integer(c_int) :: f5_nlines = 0
  integer(c_int) :: f5_ncols = 0

  real(c_double), pointer :: f2(:,:) => null()

  real(c_double), pointer :: abun(:) => null()

contains

  subroutine run_xnfpelsyn(teff_logg, frqedg, wledge, cmedge, idmol, momass, &
                         & freqset, structure, continall, contabs, contscat, &
                         & xnfpel, dopple) bind(c)
    use iso_c_binding
    real(c_double), intent(out) :: teff_logg(2)
    real(c_double), intent(out) :: frqedg(344)
    real(c_double), intent(out) :: wledge(344)
    real(c_double), intent(out) :: cmedge(344)
    real(c_double), intent(out) :: idmol(100)
    real(c_double), intent(out) :: momass(100)
    real(c_double), intent(out) :: freqset(1029)
    real(c_double), intent(out) :: structure(16,99)
    real(c_double), intent(out) :: continall(72,1131)
    real(c_double), intent(out) :: contabs(72,1131)
    real(c_double), intent(out) :: contscat(72,1131)
    real(c_double), intent(out) :: xnfpel(72,139,6)
    real(c_double), intent(out) :: dopple(72,139,6)

    call XNFPELSYN(teff_logg,frqedg,wledge,cmedge,idmol,momass,freqset,structure,continall,contabs,contscat,xnfpel,dopple,abun)

  end subroutine run_xnfpelsyn

  subroutine set_abun(ptr) bind(c)
      use iso_c_binding
      type(c_ptr), value :: ptr

      call c_f_pointer(ptr, abun, [100])
  end subroutine set_abun

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

  subroutine set_f17(ptr, n, m) bind(c)
      use iso_c_binding
      type(c_ptr), value :: ptr
      integer(c_int), value :: n, m

      call c_f_pointer(ptr, f17, [n, m])
      f17_nlines = n
      f17_ncols = m
  end subroutine set_f17

  subroutine loadf17(idx, card) bind(c, name="loadf17_")
      use iso_c_binding
      integer(c_int), intent(in) :: idx
      character(kind=c_char) :: card(f17_ncols)

      card(:) = f17(idx,:)
  end subroutine loadf17

end module xnfpelsyn_wrapper
