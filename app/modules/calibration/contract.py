from app.errors import InspectionError
from app.modules.trace.units import scaled

FIELDS = ('length_m', 'zero_a_m', 'zero_b_m', 'pair_tol_m', 'design_tol_m', 'reference_limit_db')


def setup(metadata):
    if not isinstance(metadata, dict) or set(metadata) != set(FIELDS):
        raise InspectionError('SETTING_FIELDS')
    numbers = []
    try:
        for key in FIELDS:
            number = metadata[key]
            if not isinstance(number, str) and type(number) is not int:
                raise ValueError
            maximum = 10_000 if key == 'reference_limit_db' else 500_000_000
            numbers.append(scaled(str(number), 1000, 0, maximum))
    except ValueError:
        raise InspectionError('BAD_SETTING') from None
    length, za, zb, tolerance, design_tolerance, reference = numbers
    if length == 0 or max(tolerance, design_tolerance) > length:
        raise InspectionError('BAD_LINK_RANGE')
    return {'length_mm': length, 'zero_a_mm': za, 'zero_b_mm': zb, 'pair_tol_mm': tolerance,
            'design_tol_mm': design_tolerance, 'reference_limit_mdb': reference}
