from app.ai.image_design_provider import ImageDesignProvider
from app.services.design_manufacturing_service import DesignManufacturingService


def test_image_provider_disabled_without_key(monkeypatch):
    monkeypatch.setattr("app.ai.image_design_provider.Settings.OPENAI_API_KEY", "")
    assert ImageDesignProvider().is_enabled() is False


def test_design_prompt_requires_real_product_render():
    service = object.__new__(DesignManufacturingService)
    prompt = service._design_prompt(
        project_name="Premium Magnetic Baseball Lineup Board",
        concept_name="Concept A — Field Command",
        rationale="Coach-first magnetic lineup system",
        materials="birch plywood, acrylic, magnets",
        dimensions="18 x 24 in",
        target="baseball coaches",
        visual_direction="rugged premium dugout equipment",
    )
    assert "genuinely differentiated" in prompt
    assert "not a decorated rectangle" in prompt
    assert "Do not create a generic dry-erase board" in prompt
    assert "Avoid generated words and numbers entirely" in prompt
    assert "one premium industrial-design hero render" in prompt
    assert "powder-coated aluminum frame" in prompt


def test_ai_image_validation_and_decoding():
    value = "data:image/png;base64,dGVzdC1pbWFnZQ=="
    assert DesignManufacturingService.is_ai_image(value) is True
    assert DesignManufacturingService.image_bytes(value) == b"test-image"
    assert DesignManufacturingService.is_ai_image("data:image/png;base64,not-valid!!") is False
