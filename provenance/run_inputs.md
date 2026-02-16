# Runtime inputs (milestone 2026-02-13)

## Config
- access-om3-configs branch/tag: 
- control dir: 

## Clocks
- start: 1993-01-01
- stop: 1994-12-31

## MOM6
- IC: ~/AFIM_input/mom/ic/ocean_temp_salt.res.nc
  copied from `/g/data/vk83/configurations/inputs/access-om3/mom/initial_conditions/global.025deg/2020.10.22/ocean_temp_salt.res.nc`

## CICE6
- IC (zeroed ice): ~/AFIM_input/cice/ic/iced_zero.nc
  `/g/data/vk83/configurations/inputs/access-om3/cice/initial_conditions/global.025deg/2024.04.09/iced.1900-01-01-10800.nc`

### `ice_in` / namelist additions/edits

```fortran

grid_ice          = 'C'
F2_file           = '/g/data/gv90/da1339/coastal_drag/form_factors/ADD_high-res_cstln_v7p9_GI.nc'
F2x_varname       = 'F2x'
F2y_varname       = 'F2y'
F2_map_method     = 'max'
F2_test           = .false.
F2_test_val       = 0.25

kdyn                 = 1
ndte                 = 720
boundary_condition   = 'free_slip'
lateral_drag         = .true.
form_func            = 'static'
Cs                   = 1e-3
Cq                   = 0.0
u_cap                = 0.0
C_L                  = 0.0
u0                   = 5e-5

```
