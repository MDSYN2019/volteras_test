with source as (
    select * from {{ source('application', 'vehicle_data') }}
)

select
    id as vehicle_data_id,
    vehicle_id,
    timestamp as observed_at,
    speed,
    odometer,
    soc as state_of_charge_pct,
    elevation,
    upper(nullif(trim(shift_state), '')) as shift_state
from source

