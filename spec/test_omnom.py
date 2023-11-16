from __future__ import annotations
import pytest
from omnom import MarkdownParser, MdCode, NomNomlSettings, NomNomMapper
from marko.block import BlockElement, Paragraph
from marko.parser import Parser
from marko.inline import Image, RawText


def describe_MarkdownParser() -> None:
    @pytest.fixture
    def example_md() -> str:
        return (
            "# A lovely title\n"
            + "\n"
            + "Some lovely text\n"
            + "\n"
            + "## A lovely subtitle\n"
            + "\n"
            + "![some_image](some_image_uri)\n"
            + "\n"
            + "[some_link](some_link_uri)\n"
            + "\n"
            + "```nomnoml\n"
            + "  [A] -> [B]\n"
            + "  [C] --> [D]\n"
            + "```\n"
            + "\n"
            + "testing 123\n"
            + "```python\n"
            + "    def the_world_is_my_oyster():\n"
            + "        pass\n"
            + "```\n"
            + "\n"
            + "blah blah\n"
        )

    def describe_get_code_blocks() -> None:
        def it_parses_markdown_and_finds_nomnoml_codefences(example_md: str) -> None:
            parser = MarkdownParser()
            fences = parser.get_code_blocks(example_md)
            assert fences.langs == ["nomnoml", "python"]
            assert fences.code_blocks[0].raw == "[A] -> [B]\n[C] --> [D]\n"

    def describe_replace_code_blocks() -> None:
        @pytest.fixture
        def what_replacement_should_be() -> str:
            return (
                "# A lovely title\n"
                + "\n"
                + "Some lovely text\n"
                + "\n"
                + "## A lovely subtitle\n"
                + "\n"
                + "![some_image](some_image_uri)\n"
                + "\n"
                + "[some_link](some_link_uri)\n"
                + "\n"
                + "XXX\n"
                + "\n"
                + "testing 123\n"
                + "```python\n"
                + "    def the_world_is_my_oyster():\n"
                + "        pass\n"
                + "```\n"
                + "\n"
                + "blah blah\n"
            )

        @pytest.fixture
        def replacement_block() -> BlockElement:
            source_text = "XXX\n"
            parser = Parser()
            doc = parser.parse(source_text)
            assert isinstance(doc.children[0], BlockElement)
            return doc.children[0]


        def it_replaces_the_code_blocks_in_the_markdown(
            example_md: str,
            what_replacement_should_be: str,
            replacement_block: BlockElement,
        ) -> None:
            parser = MarkdownParser()
            replaced_md = parser.replace_code_blocks(
                lang="nomnoml",
                replacements=[replacement_block],
                source=example_md,
            )
            assert replaced_md == what_replacement_should_be


def describe_MdCodeBlocks() -> None:
    @pytest.fixture
    def example_md() -> str:
        return (
            "# A lovely title\n"
            + "\n"
            + "Some lovely text\n"
            + "\n"
            + "## A lovely subtitle\n"
            + "\n"
            + "![some_image](some_image_uri)\n"
            + "\n"
            + "[some_link](some_link_uri)\n"
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


def describe_NomNomMapper() -> None:
    def describe_nomnoml_to_md_image() -> None:
        @pytest.fixture
        def nomnoml_mdcode() -> MdCode:
            nomnoml_raw = "#name: a_b_diagram\n[A] -> [B]"
            return MdCode(
                lang="nomnoml",
                raw=nomnoml_raw,
            )

        def it_maps_a_nomnoml_block_to_a_markdown_image(
            nomnoml_mdcode: MdCode,
        ) -> None:
            mapper = NomNomMapper()

            nomnoml_image_paragraph = mapper.nomnoml_to_md_image(nomnoml_mdcode)
            assert isinstance(nomnoml_image_paragraph, Paragraph)
            assert len(nomnoml_image_paragraph.children) == 1

            nomnoml_image = nomnoml_image_paragraph.children[0]
            assert isinstance(nomnoml_image, Image)
            assert len(nomnoml_image.children) == 1
            assert nomnoml_image.dest == "a_b_diagram_nomnoml.svg"

            nomnoml_image_text = nomnoml_image.children[0]
            assert isinstance(nomnoml_image_text, RawText)
            assert nomnoml_image_text.children == "a_b_diagram"
