from app.db.read_repository import public_properties


def test_public_properties_use_category_allowlist() -> None:
    result = public_properties(
        "parking",
        {
            "car_spaces": 30,
            "fee_description": "每小時 30 元",
            "source_row_number": 12,
            "coordinate_error": None,
            "internal_note": "不可公開",
        },
    )
    assert result == {"car_spaces": 30, "fee_description": "每小時 30 元"}


def test_unknown_category_exposes_no_properties() -> None:
    assert public_properties("future_private_category", {"secret": "value"}) == {}
