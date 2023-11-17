from __future__ import annotations
from dataclasses import dataclass
from typing import Self, ClassVar, Sequence
import re
from marko import Markdown
from marko.block import (
    Document,
    FencedCode,
    BlockElement,
    Paragraph,
)
from marko.inline import RawText
from marko.element import Element
from marko.md_renderer import MarkdownRenderer
from marko.parser import Parser


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

    def get_lines(self) -> Sequence[str]:
        return self.raw.split("\n")


@dataclass(frozen=True)
class NomNomlCode(MdCode):
    lang: str
    raw: str
    name: str
    MATCH_PATTERN: ClassVar[str] = r"\#name: \w+"
    REPLACEMENT_STRING: ClassVar[str] = "#name: "

    @classmethod
    def _handle_matches_error(cls, matches_len: int) -> None:
        assert matches_len >= 0
        assert matches_len != 1
        if matches_len == 0:
            msg = "Your NomNoml codefences need to specify a #name directive"
            raise NoNomNomlNameDirective(msg)
        else:
            msg = "One or more NomNoml codefences has too many #name directives"
            raise TooManyNomNomlNameDirectives(msg)

    @classmethod
    def _find_name_line(cls, nomnoml_lines: Sequence[str]) -> str:
        _matches = [re.fullmatch(cls.MATCH_PATTERN, line) for line in nomnoml_lines]
        matches = [_match.string for _match in _matches if _match is not None]
        if not len(matches) == 1:
            cls._handle_matches_error(len(matches))
        return matches[0]

    @classmethod
    def _extract_name(cls, nomnoml: MdCode) -> str:
        nomnoml_lines = nomnoml.get_lines()
        name_line = cls._find_name_line(nomnoml_lines)
        return name_line.replace(cls.REPLACEMENT_STRING, "").strip()

    @classmethod
    def new(cls, nomnoml_mdcode: MdCode) -> Self:
        return cls(
            lang=nomnoml_mdcode.lang,
            raw=nomnoml_mdcode.raw,
            name=cls._extract_name(nomnoml_mdcode),
        )


@dataclass(frozen=True)
class MdCodeBlocks:
    code_blocks: Sequence[MdCode]
    langs: Sequence[str]

    @classmethod
    def _get_fences(cls, document: Document) -> Sequence[FencedCode]:
        return [child for child in document.children if isinstance(child, FencedCode)]

    @classmethod
    def _fenced_code_to_mdcode(cls, fenced_code: FencedCode) -> MdCode:
        assert len(fenced_code.children) == 1

        raw_text_obj = fenced_code.children[0]
        assert isinstance(raw_text_obj, RawText)
        raw_text_ = raw_text_obj.children
        raw_text_lines = raw_text_.split("\n")
        raw_text = "\n".join(line.strip() for line in raw_text_lines)
        return MdCode(
            lang=fenced_code.lang,
            raw=raw_text,
        )

    @classmethod
    def from_document(cls, document: Document) -> Self:
        codefences = cls._get_fences(document)
        code_blocks = [cls._fenced_code_to_mdcode(cf) for cf in codefences]
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

    def get_nomnoml(self) -> Sequence[NomNomlCode]:
        return [
            NomNomlCode.new(mdcode) for mdcode in self.code_blocks
            if self._is_nomnoml(mdcode)
        ]

    def get_nomnoml_and_apply_settings(
        self,
        settings: NomNomlSettings,
    ) -> Sequence[NomNomlCode]:
        return [
            NomNomlCode.new(
                self._add_settings_to_nomnoml(
                    nomnoml_block=mdcode,
                    settings=settings,
                )
            )
            for mdcode in self.code_blocks
            if self._is_nomnoml(mdcode)
        ]


@dataclass
class MarkdownParser:
    _markdown_handler: Markdown = Markdown(
        parser=Parser,
        renderer=MarkdownRenderer,
    )

    def _make_document(self, markdown_string: str) -> Document:
        return self._markdown_handler.parse(markdown_string)

    def get_code_blocks(self, markdown_str: str) -> MdCodeBlocks:
        document = self._make_document(markdown_str)
        return MdCodeBlocks.from_document(document)

    def _is_lang(self, element: Element, lang: str) -> bool:
        return isinstance(element, FencedCode) and element.lang == lang

    def _get_code_block_positions(
        self,
        document: Document,
        lang: str,
    ) -> Sequence[int]:
        document_elements = document.children
        return [
            idx for idx, element in enumerate(document_elements)
            if self._is_lang(element=element, lang=lang)
        ]

    def replace_code_blocks(
        self,
        lang: str,
        replacements: Sequence[BlockElement],
        source: str,
    ) -> str:
        document = self._make_document(source)

        code_block_indices = self._get_code_block_positions(
            document=document,
            lang=lang,
        )
        assert len(replacements) == len(code_block_indices)

        new_document_children = list(document.children)
        for idx, replacement in zip(code_block_indices, replacements):
            new_document_children[idx] = replacement

        document.children = new_document_children
        return self._markdown_handler.render(document)


class NoNomNomlNameDirective(ValueError):
    pass


class TooManyNomNomlNameDirectives(ValueError):
    pass


@dataclass
class NomNomMapper:
    _parser: Parser = Parser()
    IMAGE_SUFFIX: ClassVar[str] = "_nomnoml.svg"

    def _generate_image_string(self, name: str) -> str:
        return f"![{name}]({name + self.IMAGE_SUFFIX})"

    def nomnoml_to_md_image(self, nomnoml: NomNomlCode) -> Paragraph:
        nomnoml_name = nomnoml.name
        image_string = self._generate_image_string(nomnoml_name)
        parsed_md_doc = self._parser.parse(image_string)
        assert len(parsed_md_doc.children) == 1
        paragraph = parsed_md_doc.children[0]
        assert isinstance(paragraph, Paragraph)
        return paragraph
