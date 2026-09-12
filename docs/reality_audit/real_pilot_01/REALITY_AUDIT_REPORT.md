# REALITY_AUDIT_REPORT.md

- Audited at: 2026-09-12T22:01:04.553412+00:00
- Samples: 10 (expressible 10 / non-expressible 0)
- Data nature: **real_pilot_place_claims_verified_online_2026_09_13**.

## real-qt-taikoo-li — expressible: yes
- place: 前滩太古里 (mall)
- source taikoo_official: official_operator_policy (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['qt-indoor-legal', 'qt-indoor-op'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'outdoor_open'} → effect=conditional, compliance=CONSISTENT, applicable=['qt-outdoor-op'], suppressed=[]
- resolver: {'animal': 'cat', 'service_role': 'none', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['qt-indoor-op'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'indoor'} → effect=allowed, compliance=CONSISTENT, applicable=['qt-indoor-legal', 'qt-sd-legal', 'qt-sd-op'], suppressed=[]

## real-dl-disneyland — expressible: yes
- place: 上海迪士尼乐园 (scenic_area)
- source disney_official: official_operator_policy (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_park'} → effect=prohibited, compliance=CONSISTENT, applicable=['dl-legal-dog', 'dl-pet-ban'], suppressed=[]
- resolver: {'animal': 'cat', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_park'} → effect=prohibited, compliance=CONSISTENT, applicable=['dl-pet-ban'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'whole_park'} → effect=conditional, compliance=CONSISTENT, applicable=['dl-legal-dog', 'dl-sd-legal', 'dl-sd-op'], suppressed=[]

## real-gc-huangpu-sect — expressible: yes
- place: 广场公园（黄浦段） (park)
- source hp_gov_notice: government_service (valid=True, freshness=-1d, redistribution=True)
- source pincang_detail: external_web_reference (valid=True, freshness=-1d, redistribution=False)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'h6_pet_area'} → effect=conditional, compliance=CONSISTENT, applicable=['gc-h6-detail-media', 'gc-h6-pilot'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'other_areas'} → effect=prohibited, compliance=CONSISTENT, applicable=['gc-other-keep'], suppressed=[]
- resolver: {'animal': 'cat', 'service_role': 'none', 'action': 'enter', 'zone_key': 'h6_pet_area'} → effect=conditional, compliance=CONSISTENT, applicable=['gc-h6-detail-media', 'gc-h6-pilot'], suppressed=[]

## real-dj-daji-park — expressible: yes
- place: 大吉路公园 (park)
- source hp_gov_notice: government_service (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_park'} → effect=conditional, compliance=CONSISTENT, applicable=['dj-pilot'], suppressed=[]

## real-gh-grand-gateway — expressible: yes
- place: 港汇恒隆广场 (mall)
- source jfdaily_news: external_web_reference (valid=True, freshness=-1d, redistribution=False)
- source xinhua_news: external_web_reference (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['gh-legal-dog', 'gh-indoor-new'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'outdoor'} → effect=conditional, compliance=CONSISTENT, applicable=['gh-outdoor-keep'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['gh-legal-dog', 'gh-sd-legal'], suppressed=[]

## real-lib-sh-library-east — expressible: yes
- place: 上海图书馆东馆 (library)
- source library_notice: official_operator_policy (valid=True, freshness=-1d, redistribution=True)
- source sh_dog_regulation: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_building'} → effect=prohibited, compliance=CONSISTENT, applicable=['lib-legal-dog', 'lib-pets-op'], suppressed=[]
- resolver: {'animal': 'cat', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_building'} → effect=prohibited, compliance=CONSISTENT, applicable=['lib-pets-op'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'whole_building'} → effect=allowed, compliance=CONSISTENT, applicable=['lib-legal-dog', 'lib-sd-legal', 'lib-sd-op'], suppressed=[]

## real-fp-peace-hotel — expressible: yes
- place: 和平饭店（费尔蒙） (hotel)
- source ota_pages: external_web_reference (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_hotel'} → effect=prohibited, compliance=CONSISTENT, applicable=['fp-legal-dog', 'fp-pets-op'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'whole_hotel'} → effect=conditional, compliance=CONSISTENT, applicable=['fp-legal-dog', 'fp-sd-legal', 'fp-sd-op'], suppressed=[]

## real-sb-roastery — expressible: yes
- place: 星巴克臻选上海烘焙工坊 (cafe)
- source sbux_brand: official_operator_policy (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_store'} → effect=prohibited, compliance=CONSISTENT, applicable=['sb-legal-dog'], suppressed=[]
- resolver: {'animal': 'cat', 'service_role': 'none', 'action': 'enter', 'zone_key': 'whole_store'} → effect=unknown, compliance=UNKNOWN, applicable=[], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'whole_store'} → effect=prohibited, compliance=CONSISTENT, applicable=['sb-legal-dog', 'sb-sd-legal'], suppressed=[]

## real-mn-kaidi-hongkou — expressible: yes
- place: Manner咖啡（凯德虹口商业中心店） (cafe)
- source cbndata_news: external_web_reference (valid=True, freshness=-1d, redistribution=False)
- source social_posts: ordinary_user (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation_note: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['mn-legal-dog', 'mn-indoor-media'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'outdoor_seating'} → effect=conditional, compliance=CONSISTENT, applicable=['mn-outdoor-media'], suppressed=[]

## real-xm-west-bund-gate-m — expressible: yes
- place: 星巴克咖啡（徐汇西岸梦中心店） (cafe)
- source media_report: external_web_reference (valid=True, freshness=-1d, redistribution=False)
- source user_posts: ordinary_user (valid=True, freshness=-1d, redistribution=False)
- source sh_dog_regulation_note: statute_or_regulation (valid=True, freshness=-1d, redistribution=True)
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['xm-legal-dog', 'xm-indoor-new'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'none', 'action': 'enter', 'zone_key': 'outdoor_pet_area'} → effect=conditional, compliance=CONSISTENT, applicable=['xm-outdoor-media'], suppressed=[]
- resolver: {'animal': 'dog', 'service_role': 'working', 'action': 'enter', 'zone_key': 'indoor'} → effect=prohibited, compliance=CONSISTENT, applicable=['xm-legal-dog', 'xm-sd-legal'], suppressed=[]

