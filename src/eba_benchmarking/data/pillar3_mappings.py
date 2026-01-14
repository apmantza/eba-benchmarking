"""
Pillar III Item Mappings to EBA Transparency Exercise Items
This file defines the verified mappings between Pillar III disclosure templates
and EBA transparency exercise item_ids.
"""

# Format: (template_code, row_id): (eba_item_id, description)
# eba_item_id = None means this is a NEW metric not in EBA data

PILLAR3_TO_EBA_MAPPINGS = {
    # ==========================
    # KM1 - KEY METRICS TEMPLATE
    # ==========================
    ('KM1', '1'): ('2520102', 'CET1 Capital'),
    ('KM1', '2'): ('2520133', 'Tier 1 Capital'),
    ('KM1', '3'): ('2520101', 'Total Own Funds'),
    ('KM1', '4'): ('2520138', 'Total RWA'),
    ('KM1', '4a'): ('2520154', 'Total RWA - Pre floor'),
    ('KM1', '5'): ('2520146', 'CET1 Ratio (fully loaded)'),
    ('KM1', '5b'): ('2520146', 'CET1 Ratio (fully loaded)'),
    ('KM1', '6'): ('2520147', 'Tier 1 Ratio (fully loaded)'),
    ('KM1', '6b'): ('2520147', 'Tier 1 Ratio (fully loaded)'),
    ('KM1', '7'): ('2520148', 'Total Capital Ratio (fully loaded)'),
    ('KM1', '7b'): ('2520148', 'Total Capital Ratio (fully loaded)'),
    ('KM1', '8'): (None, 'Capital Conservation Buffer (%)'),
    ('KM1', '9'): (None, 'Countercyclical Capital Buffer (%)'),
    ('KM1', 'EU 10a'): (None, 'O-SII Buffer (%)'),
    ('KM1', '11'): (None, 'Combined Buffer Requirement (%)'),
    ('KM1', 'EU 11a'): (None, 'Overall Capital Requirements (%)'),
    ('KM1', '13'): ('2520903', 'Total Leverage Ratio Exposures'),
    ('KM1', '14'): ('2520903', 'Total Leverage Ratio Exposures'),
    ('KM1', '15'): (None, 'LCR - Total HQLA'),
    ('KM1', '16'): (None, 'LCR - Total Net Cash Outflows'),
    ('KM1', '17'): (None, 'LCR Ratio'),
    ('KM1', '18'): (None, 'NSFR - Available Stable Funding'),
    ('KM1', '19'): (None, 'NSFR - Required Stable Funding'),
    ('KM1', '20'): (None, 'NSFR Ratio'),
    
    # ===========================
    # CC1 - CAPITAL COMPOSITION
    # ===========================
    ('CC1', '1'): ('2520103', 'Capital instruments eligible as CET1'),
    ('CC1', '2'): ('2520104', 'Retained earnings'),
    ('CC1', '3'): ('2520105', 'Accumulated other comprehensive income'),
    ('CC1', 'EU-3a'): ('2520107', 'Funds for general banking risk'),
    ('CC1', '5'): ('2520108', 'Minority interest in CET1'),
    ('CC1', '6'): (None, 'CET1 before regulatory adjustments'),
    ('CC1', '7'): ('2520109', 'Prudent valuation adjustments'),
    ('CC1', '8'): ('2520110', '(-) Intangible assets (including Goodwill)'),
    ('CC1', '10'): ('2520111', '(-) DTAs that rely on future profitability'),
    ('CC1', '28'): (None, 'Total regulatory adjustments to CET1'),
    ('CC1', '29'): ('2520102', 'CET1 Capital'),
    ('CC1', '36'): (None, 'AT1 before regulatory adjustments'),
    ('CC1', '43'): (None, 'Total regulatory adjustments to AT1'),
    ('CC1', '44'): ('2520133', 'Tier 1 Capital'),
    ('CC1', '45'): ('2520135', 'Tier 2 Capital instruments'),
    ('CC1', '51'): (None, 'Tier 2 before regulatory adjustments'),
    ('CC1', '57'): (None, 'Total regulatory adjustments to Tier 2'),
    ('CC1', '58'): ('2520101', 'Total Own Funds'),
    ('CC1', '59'): ('2520138', 'Total RWA'),
    ('CC1', '60'): ('2520140', 'CET1 Ratio (transitional)'),
    ('CC1', '61'): ('2520141', 'Tier 1 Ratio (transitional)'),
    ('CC1', '62'): ('2520142', 'Total Capital Ratio (transitional)'),
    
    # ===========================
    # OV1 - RWA OVERVIEW
    # ===========================
    ('OV1', '1'): ('2520201', 'Credit risk (excl CCR and Securitisations)'),
    ('OV1', '2'): ('2520202', 'Credit risk - SA'),
    ('OV1', '3'): ('2520203', 'Credit risk - FIRB'),
    ('OV1', '4'): ('2520204', 'Credit risk - Slotting'),
    ('OV1', '5'): ('2520205', 'Credit risk - Equities IRB'),
    ('OV1', '6'): ('2520206', 'Counterparty credit risk (CCR)'),
    ('OV1', '7'): (None, 'CCR - SA-CCR'),
    ('OV1', '10'): ('2520207', 'Credit Valuation Adjustment (CVA)'),
    ('OV1', '15'): ('2520208', 'Settlement risk'),
    ('OV1', '16'): ('2520209', 'Securitisation exposures in banking book'),
    ('OV1', '18'): (None, 'Securitisation - SEC-ERBA'),
    ('OV1', '19'): (None, 'Securitisation - SEC-SA'),
    ('OV1', '20'): ('2520210', 'Position, FX and commodities risks'),
    ('OV1', '21'): ('2520211', 'Market risk - SA'),
    ('OV1', '22'): ('2520212', 'Market risk - IMA'),
    ('OV1', '23'): ('2520215', 'Operational risk'),
    ('OV1', '24'): ('2520215', 'Operational risk'),
    ('OV1', '25'): ('2520217', 'Operational risk - SA'),
    ('OV1', '26'): (None, 'Output floor amount'),
    ('OV1', '29'): ('2520220', 'Total Risk exposure amount'),
    
    # ===========================
    # LR - LEVERAGE RATIO
    # ===========================
    ('LR1', '1'): (None, 'Total assets per financial statements'),
    ('LR1', '13'): ('2520903', 'Leverage ratio - total exposure measure'),
    ('LR2', '13'): ('2520903', 'Leverage ratio - total exposure measure'),
    ('LR2', 'EU-19a'): ('2520133', 'Tier 1 Capital'),
    ('LR2', '20'): ('2520905', 'Leverage ratio (transitional)'),
    ('LR2', 'EU-21'): ('2520906', 'Leverage ratio (fully phased-in)'),
    ('LR3', '1'): (None, 'Total assets per financial statements'),
    ('LR3', '13'): ('2520903', 'Leverage ratio - total exposure measure'),
    
    # ===========================
    # LIQ1 - LCR
    # ===========================
    ('LIQ1', '1'): (None, 'Total HQLA'),
    ('LIQ1', '2'): (None, 'Retail deposits - total'),
    ('LIQ1', '3'): (None, 'Retail deposits - stable'),
    ('LIQ1', '4'): (None, 'Retail deposits - less stable'),
    ('LIQ1', '5'): (None, 'Unsecured wholesale funding'),
    ('LIQ1', '6'): (None, 'Operational deposits'),
    ('LIQ1', '7'): (None, 'Non-operational deposits'),
    ('LIQ1', '16'): (None, 'Total cash outflows'),
    ('LIQ1', '19'): (None, 'Total cash inflows'),
    ('LIQ1', '20'): (None, 'Total cash inflows capped'),
    ('LIQ1', '21'): (None, 'LCR (%)'),
    ('LIQ1', '22'): (None, 'Total net cash outflows'),
    ('LIQ1', '23'): (None, 'LCR ratio'),
    
    # ===========================
    # LIQ2 - NSFR
    # ===========================
    ('LIQ2', '1'): (None, 'Capital items and instruments'),
    ('LIQ2', '2'): (None, 'Own funds'),
    ('LIQ2', '4'): (None, 'Retail deposits'),
    ('LIQ2', '5'): (None, 'Stable deposits'),
    ('LIQ2', '12'): (None, 'Total ASF'),
    ('LIQ2', '13'): (None, 'Total HQLA for NSFR'),
    ('LIQ2', '26'): (None, 'Total RSF'),
    ('LIQ2', '27'): (None, 'NSFR (%)'),
    
    # ===========================
    # KM2 - MREL KEY METRICS
    # ===========================
    ('KM2', '1'): (None, 'Own funds and eligible liabilities'),
    ('KM2', 'EU-1a'): ('2520101', 'Own Funds'),
    ('KM2', '2'): ('2520138', 'Total RWA'),
    ('KM2', '3'): (None, 'MREL ratio (% of RWA)'),
    ('KM2', '4'): ('2520903', 'Total exposure measure'),
    ('KM2', '5'): (None, 'MREL ratio (% of TEM)'),
}


def get_eba_mapping(template_code, row_id):
    """Get EBA item_id for a Pillar III item. Returns (item_id, description) or (None, None)."""
    key = (template_code, row_id)
    if key in PILLAR3_TO_EBA_MAPPINGS:
        return PILLAR3_TO_EBA_MAPPINGS[key]
    return (None, None)


def is_new_metric(template_code, row_id):
    """Check if a Pillar III item is a new metric (not mapped to EBA)."""
    eba_id, _ = get_eba_mapping(template_code, row_id)
    return eba_id is None


if __name__ == '__main__':
    # Print summary
    mapped = sum(1 for v in PILLAR3_TO_EBA_MAPPINGS.values() if v[0] is not None)
    new = sum(1 for v in PILLAR3_TO_EBA_MAPPINGS.values() if v[0] is None)
    
    print(f"Total Pillar III items defined: {len(PILLAR3_TO_EBA_MAPPINGS)}")
    print(f"  Mapped to EBA: {mapped}")
    print(f"  New metrics: {new}")
    
    # List by template
    templates = {}
    for (t, r), (eba, desc) in PILLAR3_TO_EBA_MAPPINGS.items():
        if t not in templates:
            templates[t] = {'mapped': 0, 'new': 0}
        if eba:
            templates[t]['mapped'] += 1
        else:
            templates[t]['new'] += 1
    
    print("\nBy Template:")
    for t, counts in sorted(templates.items()):
        print(f"  {t}: {counts['mapped']} mapped, {counts['new']} new")
