from __future__ import annotations
from dataclasses import dataclass
from typing import Self
import marko
from marko.block import (
    Document as MarkoDocument,
    FencedCode as MarkoFencedCode,
    BlockElement as MarkoBlockElement,
    BlankLine as MarkoBlankLine,
    Heading as MarkoHeading,
    Paragraph as MarkoParagraph,
)
from marko.inline import RawText
from marko.element import Element as MarkoElement


@dataclass(frozen=True)
class NomNomlSettings:
    raw: str

    @classmethod
    def new(cls, settings_string: str) -> Self:
        return cls(raw=settings_string)


@dataclass(frozen=True)
class MdCode:
    lang: str
    raw: str


@dataclass(frozen=True)
class MdCodeBlocks:
    code_blocks: list[MdCode]
    langs: list[str]

    @classmethod
    def _get_fences(cls, markdown: MarkoDocument) -> list[MarkoFencedCode]:
        return [child for child in markdown.children if isinstance(child, MarkoFencedCode)]

    @classmethod
    def _marko_to_mdcode(cls, marko_cf: MarkoFencedCode) -> MdCode:
        assert len(marko_cf.children) == 1

        raw_text_obj = marko_cf.children[0]
        assert isinstance(raw_text_obj, RawText)
        raw_text_ = raw_text_obj.children
        raw_text_lines = raw_text_.split("\n")
        raw_text = "\n".join(line.strip() for line in raw_text_lines)
        return MdCode(
            lang=marko_cf.lang,
            raw=raw_text,
        )

    @classmethod
    def from_marko(cls, marko_markdown: MarkoDocument) -> Self:
        marko_codefences = cls._get_fences(marko_markdown)
        code_blocks = [cls._marko_to_mdcode(marko_cf) for marko_cf in marko_codefences]
        return cls(
            code_blocks=code_blocks,
            langs=[mdcode.lang for mdcode in code_blocks],
        )

    def _add_settings_to_nomnoml(
        self,
        nomnoml_block: MdCode,
        settings: NomNomlSettings,
    ) -> MdCode:
        return MdCode(
            lang=nomnoml_block.lang,
            raw=settings.raw + nomnoml_block.raw,
        )

    def _is_nomnoml(self, mdcode: MdCode) -> bool:
        return mdcode.lang == "nomnoml"

    def get_nomnoml(self, settings: NomNomlSettings) -> list[MdCode]:
        return [
            self._add_settings_to_nomnoml(
                nomnoml_block=mdcode,
                settings=settings,
            )
            for mdcode in self.code_blocks
            if self._is_nomnoml(mdcode)
        ]


class _CodeFenceMarker:
    pass


class MarkdownParser:
    @classmethod
    def _make_markdown(cls, markdown_string: str) -> MarkoDocument:
        return marko.parse(markdown_string)

    @classmethod
    def get_code_blocks(cls, markdown_str: str) -> MdCodeBlocks:
        markdown = cls._make_markdown(markdown_str)
        return MdCodeBlocks.from_marko(markdown)

    @classmethod
    def _is_nomnoml(cls, element: MarkoElement) -> bool:
        return isinstance(element, MarkoFencedCode) and element.lang == "nomnoml"

    @classmethod
    def _get_nomnoml_block_positions(
        cls,
        markdown: MarkoDocument,
    ) -> list[int]:
        markdown_elements = markdown.children
        return [
            idx for idx, element in enumerate(markdown_elements)
            if cls._is_nomnoml(element)
        ]

    @classmethod
    def _raw_string_from_element(cls, element: MarkoBlockElement) -> str:
        assert len(element.children) == 1, element
        raw_text_obj = element.children[0]
        assert isinstance(raw_text_obj, RawText)
        assert isinstance(raw_text_obj.children, str)
        return raw_text_obj.children

    @classmethod
    def _element_to_string(cls, element: MarkoElement) -> str | _CodeFenceMarker:
        if isinstance(element, MarkoBlankLine):
            return "\n"

        assert isinstance(element, MarkoBlockElement)
        raw_text = cls._raw_string_from_element(element)

        if isinstance(element, MarkoFencedCode):
            return f"```{element.lang}\n" + raw_text + "```\n"
        elif isinstance(element, MarkoHeading):
            return f"{element.level*"#"} {raw_text}\n"
        else:
            assert isinstance(element, MarkoParagraph)
            return raw_text + "\n"

    @classmethod
    def _cast_to_string(cls, ele_str: str | _CodeFenceMarker) -> str:
        assert isinstance(ele_str, str)
        return ele_str

    @classmethod
    def _cast_to_list_of_strings(cls, element_strings: list[str | _CodeFenceMarker]) -> list[str]:
        return [cls._cast_to_string(ele_str) for ele_str in element_strings]

    @classmethod
    def replace_code_blocks(
        cls,
        lang: str,
        replacements: list[str],
        source: str,
    ) -> str:
        markdown = cls._make_markdown(source)
        nomnoml_block_indices = cls._get_nomnoml_block_positions(markdown)
        markdown_element_strings = [
            cls._element_to_string(element) for element in markdown.children
        ]

        assert len(replacements) == len(nomnoml_block_indices)

        for idx, replacement in zip(nomnoml_block_indices, replacements):
            markdown_element_strings[idx] = replacement
        markdown_element_strings = cls._cast_to_list_of_strings(markdown_element_strings)
        return "".join(markdown_element_strings)
