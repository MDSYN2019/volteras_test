select
    vehicle_id,
    date_trunc('hour', observed_at) as observed_hour,
    count(*) as observation_count,
    avg(speed) as average_speed,
    min(state_of_charge_pct) as minimum_state_of_charge_pct,
    max(state_of_charge_pct) as maximum_state_of_charge_pct,
    max(odometer) - min(odometer) as distance_travelled
from {{ ref('stg_vehicle_data') }}
group by 1, 2

