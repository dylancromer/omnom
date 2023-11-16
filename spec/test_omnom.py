from __future__ import annotations
import pytest
from omnom import MarkdownParser, MdCode, NomNomlSettings


def describe_MarkdownParser() -> None:
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
            + "  [C] --> [D]\n"
            + "```"
        )

    def it_parses_markdown_and_finds_nomnoml_codefences(example_md: str) -> None:
        parser = MarkdownParser()
        fences = parser.get_code_blocks(example_md)
        assert fences.langs == ["nomnoml"]
        assert fences.code_blocks[0].raw == "[A] -> [B]\n[C] --> [D]\n"


def describe_MdCodeBlocks() -> None:
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
            + "  [C] --> [D]\n"
            + "```\n"
        )

    @pytest.fixture
    def nomnoml_settings() -> str:
        with open("default_settings.noml", "r") as inf:
            settings_data = inf.read()
        return settings_data

    @pytest.fixture
    def what_it_should_be(nomnoml_settings: str) -> MdCode:
        return MdCode(
            lang="nomnoml",
            raw=(nomnoml_settings + "[A] -> [B]\n[C] --> [D]\n"),
        )


    def describe_get_nomnoml():
        def it_returns_MdCode_objects_of_nomnoml_lang_with_the_settings(
            example_md: str,
            nomnoml_settings: str,
            what_it_should_be: MdCode,
        ) -> None:
            parser = MarkdownParser()
            fences = parser.get_code_blocks(example_md)
            nomnoml_with_settings = fences.get_nomnoml(
                settings=NomNomlSettings.new(nomnoml_settings),
            )
            assert nomnoml_with_settings == [what_it_should_be]
