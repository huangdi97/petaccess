# REALITY_AUDIT_REPORT.md

- Audited at: 2026-09-12T19:36:51.248386+00:00
- Samples: 6 (expressible 5 / non-expressible 1)
- Data nature: **synthetic adversarial fixtures only** — no real-merchant rule is claimed or fabricated (REALITY_AUDIT_PLAN 第一阶段).

## syn-cafe-001 — expressible: yes
- place: 样板·云边咖啡馆（虚构） (cafe)
- source sign1: onsite_signage (valid=True, freshness=23d, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['c-in'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'outdoor'} → effect=conditional, compliance=CONSISTENT, applicable=['c-out'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'indoor'} → effect=allowed, compliance=CONSISTENT, applicable=['c-sd'], suppressed=[]
- boundary: ordinary_pet_indoor_dining [avoid] → MATCH
- boundary: animal_on_customer_seat [avoid] → MATCH

## syn-mall-002 — expressible: NO
- place: 样板·星荟广场（虚构） (mall)
- unsupported conditions: m-l3:use_pet_elevator
- source op1: official_operator_policy (valid=True, freshness=11d, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'public'} → effect=conditional, compliance=CONSISTENT, applicable=['m-pub'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'fnb'} → effect=prohibited, compliance=CONSISTENT, applicable=['m-fnb'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'l3'} → effect=allowed, compliance=CONSISTENT, applicable=['m-l3'], suppressed=[]
- boundary: dedicated_pet_zone_available [prefer] → UNKNOWN

## syn-park-003 — expressible: yes
- place: 样板·澜山公园（虚构） (park)
- source gov1: government_service (valid=True, freshness=59d, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'off_leash', 'zone_key': 'lawn'} → effect=prohibited, compliance=CONSISTENT, applicable=['p-law'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'lawn'} → effect=conditional, compliance=CONSISTENT, applicable=['p-wk'], suppressed=[]

## syn-hotel-004 — expressible: yes
- place: 样板·栖云酒店（虚构） (hotel)
- source ph1: official_operator_policy (valid=True, freshness=stale, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'stay_overnight', 'zone_key': None} → effect=conditional, compliance=CONSISTENT, applicable=['h-w'], suppressed=[]

## syn-market-005 — expressible: yes
- place: 样板·惠选超市（虚构） (supermarket)
- source weird: social_media_scrape (valid=False, freshness=2d, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': '1f'} → effect=prohibited, compliance=CONSISTENT, applicable=['s-1f'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': '3f'} → effect=allowed, compliance=CONSISTENT, applicable=['s-3f'], suppressed=[]
- boundary: pet_swimming_pool [prefer] → UNKNOWN

## syn-event-006 — expressible: yes
- place: 样板·河湾市集（虚构） (market)
- source ev1: official_operator_policy (valid=True, freshness=1d, redistribution=False)
- source law1: statute_or_regulation (valid=True, freshness=103d, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'plaza'} → effect=prohibited, compliance=POTENTIAL_CONFLICT, applicable=['e-law'], suppressed=['e-ev']

