import pytest
from omnom import Om


def describe_Om() -> None:
    @pytest.fixture
    def example_md() -> str:
        return (
            "#A lovely title\n"
            + "\n"
            + "Some lovely text\n"
            + "\n"
            + "## A lovely subtitle\n"
            + "\n"
            + "```nomnoml\n"
            + "  [A] -> [B]\n"
        )

    def it_parses_markdown_and_finds_nomnoml_codefences() -> None:
        om = Om()
        fence = om.nom(example_md)
        assert fence.lang == "nomnoml"
        assert fence.raw == "[A] -> [B]\n"
